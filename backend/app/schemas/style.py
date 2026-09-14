"""Style schemas.

Defines the canonical structured fashion representation (``StyleDNA``) and the
analyze endpoint response. ``StyleDNA`` is also intended to validate AI analyzer
output later, so it is strict about shape but flexible about which style tags
appear (the lists are open-ended).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import NonBlankStr, NonNegativeInt, Score


class StyleScore(BaseModel):
    """A single style/aesthetic weighting, e.g. {"streetwear": 45}."""

    name: NonBlankStr
    score: Score  # 0-100


class StyleDNA(BaseModel):
    """Canonical structured fashion profile derived from inspiration.

    All dimension lists default to empty so partial analyzer output is still
    valid. New dimensions can be added over time without breaking existing data.
    """

    styles: list[StyleScore] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    garments: list[str] = Field(default_factory=list)
    fits: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    """Response for ``POST /style/analyze``."""

    profile_id: int
    style_dna: StyleDNA
    sources_processed: NonNegativeInt
    sources_failed: NonNegativeInt
