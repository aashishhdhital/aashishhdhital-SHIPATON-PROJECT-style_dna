"""Feedback schemas.

Shapes for ``POST /outfits/{outfit_id}/feedback``. ``reaction`` uses a Literal
so invalid values are rejected at the schema boundary.

Integrity rule (enforced later in the service, NOT here): ``result_id`` must
belong to the recommendation session identified by the path ``{outfit_id}``.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import PositiveInt, Reaction


class FeedbackRequest(BaseModel):
    """Request body for submitting feedback on a shown result."""

    result_id: PositiveInt
    reaction: Reaction


class FeedbackResponse(BaseModel):
    """Response after recording feedback."""

    status: str
    result_id: int
    reaction: Reaction
