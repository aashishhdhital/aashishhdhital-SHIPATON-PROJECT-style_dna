"""Recommendation generation logic (for POST /outfits/generate).

Stays HTTP-agnostic and raises plain domain exceptions for the router to map.

Flow:
    1. confirm the user exists
    2. load the user's latest StyleProfile (validated as StyleDNA)
    3. build a deterministic Pinterest search intent from Style DNA + occasion
    4. ask the Pinterest provider (MOCK) for candidate pins
    5. rank candidates against BOTH Style DNA overlap AND feedback-derived
       preference_weights (deterministic)
    6. persist a RecommendationSession + RecommendationResult rows (incl. tags)
    7. return a GenerateResponse
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.recommendation_result import RecommendationResult
from app.models.recommendation_session import RecommendationSession
from app.models.style_profile import StyleProfile
from app.models.user import User
from app.providers import pinterest_provider
from app.providers.pinterest_provider import PinCandidate, PinterestProviderError
from app.schemas.recommendation import GenerateResponse, RecommendationItem
from app.schemas.style import StyleDNA

# How many ranked results to persist/return per generation.
_MAX_RESULTS = 5

# Ranking tunables. The preference adjustment is deliberately small and capped
# so learned feedback nudges ranking WITHOUT overpowering the Style DNA base.
_PREF_POINTS_PER_UNIT = 2.0  # points added per unit of accumulated weight
_PREF_MAX_ADJUST = 15  # max absolute preference adjustment (points)


class UserNotFoundError(Exception):
    """Raised when the supplied user_id has no matching User row."""


class ProfileNotFoundError(Exception):
    """Raised when the user exists but has no StyleProfile to base results on."""


def _load_latest_profile(db: Session, user_id: int) -> StyleProfile:
    """Return the user's latest StyleProfile row (or raise ProfileNotFoundError)."""
    profile = db.execute(
        select(StyleProfile)
        .where(StyleProfile.user_id == user_id)
        .order_by(StyleProfile.created_at.desc(), StyleProfile.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if profile is None:
        raise ProfileNotFoundError(f"No style profile found for user {user_id}")
    return profile


def _style_terms(dna: StyleDNA) -> set[str]:
    """Flatten a Style DNA into a lowercased set of characteristic terms."""
    terms: set[str] = set()
    terms.update(s.name.lower() for s in dna.styles)
    for bucket in (dna.colors, dna.garments, dna.fits, dna.patterns, dna.materials, dna.traits):
        terms.update(item.lower() for item in bucket)
    return terms


def build_search_intent(dna: StyleDNA, occasion: str, context: dict[str, Any] | None) -> str:
    """Deterministically build a Pinterest search query from DNA + occasion.

    Uses the top styles (by score) plus leading colors/garments and the occasion.
    This is a simple string assembly today; an AI-assisted intent generator can
    replace it later without changing the flow.
    """
    top_styles = [s.name for s in sorted(dna.styles, key=lambda s: s.score, reverse=True)[:2]]
    top_colors = dna.colors[:1]
    top_garments = dna.garments[:1]

    parts = [*top_styles, *top_colors, *top_garments, occasion.strip(), "outfit"]

    # Fold in a couple of simple context hints if present (kept minimal on purpose).
    if context:
        for key in ("dress_code", "weather", "season"):
            value = context.get(key)
            if isinstance(value, str) and value.strip():
                parts.insert(-1, value.strip())

    # De-duplicate while preserving order, drop blanks.
    seen: set[str] = set()
    ordered = []
    for part in parts:
        p = part.strip().lower()
        if p and p not in seen:
            seen.add(p)
            ordered.append(p)
    return " ".join(ordered)


def _preference_adjustment(candidate: PinCandidate, weights: dict[str, float]) -> float:
    """Sum feedback weights for a candidate's tags, scaled and capped.

    Positive if the user has liked these traits, negative if disliked. The
    result is clamped to +/- _PREF_MAX_ADJUST so it can only nudge the ranking.
    """
    raw = sum(float(weights.get(t.lower(), 0.0)) for t in candidate.tags)
    scaled = raw * _PREF_POINTS_PER_UNIT
    return max(-_PREF_MAX_ADJUST, min(_PREF_MAX_ADJUST, scaled))


def _score_candidate(
    candidate: PinCandidate, terms: set[str], weights: dict[str, float]
) -> tuple[int, list[str]]:
    """Return a deterministic (match_score, matched_terms) for a candidate.

    Final score combines two signals:
        base  = 50 + 10 * (number of Style DNA terms the pin's tags match)
        pref  = clamp(sum(preference_weights[tag]) * 2.0, -15, +15)
        score = clamp(round(base + pref), 0, 100)

    Style DNA is the primary signal (base 50-100, +10 per matched term); the
    feedback preference term is a small, capped nudge so learned weights never
    overpower the inspiration-derived identity.
    """
    matched = sorted(t for t in candidate.tags if t.lower() in terms)
    base = 50 + 10 * len(matched)
    pref = _preference_adjustment(candidate, weights)
    score = round(base + pref)
    score = max(0, min(100, score))
    return score, matched


def _match_reason(matched: list[str], occasion: str) -> str:
    if matched:
        return f"Matches your {', '.join(matched)} preferences for {occasion}."
    return f"A general option for {occasion}."


def generate(
    db: Session,
    user_id: int,
    occasion: str,
    context: dict[str, Any] | None = None,
) -> GenerateResponse:
    """Generate and persist recommendations for a user + occasion."""
    # 1. Confirm the user exists.
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} does not exist")

    # 2. Load the latest profile: its Style DNA (identity) and preference_weights
    # (feedback-derived). style_data is never mutated here.
    profile = _load_latest_profile(db, user_id)
    dna = StyleDNA.model_validate(profile.style_data)
    weights: dict[str, float] = dict(profile.preference_weights or {})

    # 3. Build the search intent.
    search_intent = build_search_intent(dna, occasion, context)

    # 4. Ask the provider for candidates. The mock never fails, but we structure
    # failure handling now: a provider error yields an empty, "failed" session
    # rather than crashing (real degraded/failed behavior comes with the real
    # integration).
    provider_status = "ok"
    try:
        candidates = pinterest_provider.search(search_intent, limit=_MAX_RESULTS)
    except PinterestProviderError:
        candidates = []
        provider_status = "failed"

    # 5. Rank candidates using Style DNA overlap + feedback preference weights.
    terms = _style_terms(dna)
    scored = [(*_score_candidate(c, terms, weights), c) for c in candidates]
    # Sort by score desc, then external_id for a stable deterministic order.
    scored.sort(key=lambda t: (-t[0], t[2].external_id))

    # 6. Persist the session and its results.
    session = RecommendationSession(
        user_id=user_id,
        occasion=occasion,
        context=context,
        search_intent=search_intent,
        provider_status=provider_status,
    )
    db.add(session)
    db.flush()  # assign session.id

    results: list[RecommendationResult] = []
    for position, (score, matched, candidate) in enumerate(scored):
        result = RecommendationResult(
            session_id=session.id,
            title=candidate.title,
            image_url=candidate.image_url,
            pinterest_url=candidate.pinterest_url,
            description=candidate.description,
            match_score=score,
            match_reason=_match_reason(matched, occasion),
            external_id=candidate.external_id,
            position=position,
            # Persist normalized tags so feedback can derive preference keys.
            tags=list(candidate.tags),
        )
        results.append(result)
    db.add_all(results)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    # 7. Build the response from the persisted rows.
    return GenerateResponse(
        id=session.id,
        occasion=session.occasion,
        search_intent=session.search_intent,
        provider_status=session.provider_status,
        recommendations=[RecommendationItem.model_validate(r) for r in results],
    )
