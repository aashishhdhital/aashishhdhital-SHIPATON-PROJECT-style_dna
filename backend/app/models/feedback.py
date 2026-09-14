"""Feedback model.

A user's reaction (like / maybe / dislike) to a specific shown Pinterest result.
``session_id`` is denormalized alongside ``result_id`` for easy per-session
rollups. Weighting/ranking logic is NOT implemented yet.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.recommendation_result import RecommendationResult
    from app.models.recommendation_session import RecommendationSession

REACTIONS = ("like", "maybe", "dislike")


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint(
            "reaction IN ('like', 'maybe', 'dislike')",
            name="ck_feedback_reaction",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    result_id: Mapped[int] = mapped_column(
        ForeignKey("recommendation_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("recommendation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reaction: Mapped[str] = mapped_column(String(20), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    result: Mapped["RecommendationResult"] = relationship(back_populates="feedback")
    session: Mapped["RecommendationSession"] = relationship(back_populates="feedback")
