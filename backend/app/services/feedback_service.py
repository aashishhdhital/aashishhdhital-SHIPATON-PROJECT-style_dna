"""Feedback persistence logic (for POST /outfits/{outfit_id}/feedback).

Stays HTTP-agnostic and raises plain domain exceptions for the router to map.

Flow:
    1. confirm the RecommendationSession (outfit_id) exists
    2. confirm the RecommendationResult exists
    3. confirm the result belongs to that session (integrity rule)
    4. persist a Feedback row (append-only; see policy note below)
    5. commit
    6. return FeedbackResponse data

DUPLICATE-FEEDBACK POLICY: append-only (Option A). Every submission inserts a
new Feedback row, forming an event history, and EACH event also adjusts the
user's preference_weights. We do NOT update or de-duplicate existing rows.

PREFERENCE LEARNING: on each feedback event we adjust the latest StyleProfile's
``preference_weights`` (feedback-derived) -- never ``style_data`` (inspiration
identity). Keys come from the result's persisted ``tags``. The feedback insert
and the weight update commit together (atomic).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.models.recommendation_result import RecommendationResult
from app.models.recommendation_session import RecommendationSession
from app.models.style_profile import StyleProfile
from app.schemas.common import Reaction
from app.schemas.feedback import FeedbackResponse

# Deterministic MVP reaction deltas applied to each matched preference key.
_REACTION_DELTAS: dict[str, float] = {
    "like": 1.0,
    "maybe": 0.25,
    "dislike": -1.0,
}


class SessionNotFoundError(Exception):
    """Raised when the outfit_id has no matching RecommendationSession."""


class ResultNotFoundError(Exception):
    """Raised when the result does not exist, or does not belong to the session."""


def _apply_preference_update(
    db: Session, user_id: int, tags: list[str], delta: float
) -> None:
    """Adjust the user's latest StyleProfile.preference_weights by ``delta``.

    KNOWN LIMITATION (flagged): RecommendationSession stores user_id but not
    profile_id, so we update the user's *latest* profile. If the user generated
    a NEWER StyleProfile (e.g. re-ran /style/analyze) after this session was
    created, feedback from the older session will adjust the newer profile.
    Acceptable for the MVP; revisit by storing profile_id on the session if this
    ever causes incorrect attribution.

    style_data is never touched here. If the user has no profile, we skip
    silently (feedback itself is still recorded).
    """
    if not tags:
        return
    profile = (
        db.query(StyleProfile)
        .filter(StyleProfile.user_id == user_id)
        .order_by(StyleProfile.created_at.desc(), StyleProfile.id.desc())
        .first()
    )
    if profile is None:
        return

    # Reassign a NEW dict so SQLAlchemy detects the change (in-place JSONB
    # mutation is not tracked by default).
    weights: dict[str, float] = dict(profile.preference_weights or {})
    for tag in tags:
        key = tag.lower()
        weights[key] = round(weights.get(key, 0.0) + delta, 4)
    profile.preference_weights = weights


def submit_feedback(
    db: Session,
    outfit_id: int,
    result_id: int,
    reaction: Reaction,
) -> FeedbackResponse:
    """Record a reaction to a shown result within a session.

    ``outfit_id`` is a ``RecommendationSession.id``. The ``result_id`` must
    belong to that session or a ``ResultNotFoundError`` is raised (we never
    trust the client's pairing).
    """
    # 1. Session must exist.
    session = db.get(RecommendationSession, outfit_id)
    if session is None:
        raise SessionNotFoundError(f"Recommendation session {outfit_id} does not exist")

    # 2. Result must exist.
    result = db.get(RecommendationResult, result_id)
    # 3. And it must belong to THIS session. Checking session_id here means a
    # result from another session is treated as "not found within this session".
    if result is None or result.session_id != outfit_id:
        raise ResultNotFoundError(
            f"Result {result_id} not found in session {outfit_id}"
        )

    # 4. Append a new Feedback event.
    feedback = Feedback(
        result_id=result_id,
        session_id=outfit_id,
        reaction=reaction,
    )
    db.add(feedback)

    # 5. Adjust the user's preference_weights from this result's tags. The
    # feedback insert + weight update commit together (atomic).
    delta = _REACTION_DELTAS[reaction]
    _apply_preference_update(db, session.user_id, list(result.tags or []), delta)

    # 6. Commit both changes.
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    # 7. Return the response payload.
    return FeedbackResponse(status="saved", result_id=result_id, reaction=reaction)
