"""Pydantic schemas package (API request/response shapes).

Kept entirely separate from the SQLAlchemy models in ``app.models``.
"""

from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.schemas.inspiration import InspirationSourceOut, PinterestLinkInput
from app.schemas.profile import ProfileResponse
from app.schemas.recommendation import (
    GenerateRequest,
    GenerateResponse,
    RecommendationItem,
)
from app.schemas.style import AnalyzeResponse, StyleDNA, StyleScore

__all__ = [
    # style
    "StyleScore",
    "StyleDNA",
    "AnalyzeResponse",
    # inspiration
    "PinterestLinkInput",
    "InspirationSourceOut",
    # profile
    "ProfileResponse",
    # recommendation
    "GenerateRequest",
    "RecommendationItem",
    "GenerateResponse",
    # feedback
    "FeedbackRequest",
    "FeedbackResponse",
]
