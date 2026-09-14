"""Recommendation schemas.

Shapes for generating recommendations and returning REAL Pinterest results.
No price / retailer / inventory / commerce fields -- Pinterest is a visual
inspiration source here, not a product catalog.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import (
    NonBlankStr,
    NonNegativeInt,
    PositiveInt,
    ProviderStatus,
    Score,
)


class GenerateRequest(BaseModel):
    """Request for ``POST /outfits/generate``."""

    user_id: PositiveInt
    occasion: NonBlankStr
    # Left intentionally loose (weather, dress code, etc. are not finalized).
    context: dict[str, Any] | None = None


class RecommendationItem(BaseModel):
    """A single real Pinterest result shown to the user.

    ``image_url`` / ``pinterest_url`` carry real provider-returned values once
    the Pinterest integration exists; they are never fabricated.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    image_url: str
    pinterest_url: str
    description: str | None = None
    match_score: Score  # 0-100
    match_reason: str
    position: NonNegativeInt


class GenerateResponse(BaseModel):
    """Response for ``POST /outfits/generate``."""

    id: int
    occasion: str
    search_intent: str
    provider_status: ProviderStatus
    recommendations: list[RecommendationItem] = Field(default_factory=list)
