"""Profile schemas.

Public shape for ``GET /profile/{user_id}``. Returns the user's current/latest
Style DNA only. ``preference_weights`` (feedback-derived) is intentionally NOT
exposed in this public response.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.style import StyleDNA


class ProfileResponse(BaseModel):
    """Response for ``GET /profile/{user_id}``."""

    id: int
    name: str
    style_dna: StyleDNA
