"""Profile read-path business logic (for GET /profile/{user_id}).

Stays HTTP-agnostic: it raises plain domain exceptions that the router maps to
HTTP responses. Responsibilities: query the user, find the latest StyleProfile,
validate the stored ``style_data`` through the ``StyleDNA`` schema, and return
the data needed for a ``ProfileResponse``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.style_profile import StyleProfile
from app.models.user import User
from app.schemas.profile import ProfileResponse
from app.schemas.style import StyleDNA


class UserNotFoundError(Exception):
    """Raised when the supplied user_id has no matching User row."""


class ProfileNotFoundError(Exception):
    """Raised when the user exists but has no StyleProfile."""


def get_profile(db: Session, user_id: int) -> ProfileResponse:
    """Return the user's current (latest) profile as a ``ProfileResponse``.

    Raises ``UserNotFoundError`` / ``ProfileNotFoundError`` for the router to
    translate into 404 responses.
    """
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} does not exist")

    # Latest profile wins. Order by created_at DESC, with id DESC as a
    # deterministic tie-breaker for rows sharing a timestamp.
    profile = db.execute(
        select(StyleProfile)
        .where(StyleProfile.user_id == user_id)
        .order_by(StyleProfile.created_at.desc(), StyleProfile.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    if profile is None:
        raise ProfileNotFoundError(f"No style profile found for user {user_id}")

    # Validate the persisted JSONB against the canonical schema before returning.
    # This also strips anything not part of StyleDNA, so only the seven
    # dimensions are exposed (never preference_weights or DB internals).
    style_dna = StyleDNA.model_validate(profile.style_data)

    return ProfileResponse(id=user.id, name=user.name, style_dna=style_dna)
