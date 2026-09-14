"""RecommendationResult model.

A single REAL Pinterest result shown to the user within a session. ``image_url``
and ``pinterest_url`` are persisted exactly as returned by the Pinterest provider
(never fabricated). ``match_score`` is constrained to 0-100.

Persisting exactly what was shown is what lets feedback reference a concrete Pin.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.recommendation_session import RecommendationSession


class RecommendationResult(Base):
    __tablename__ = "recommendation_results"
    __table_args__ = (
        CheckConstraint(
            "match_score >= 0 AND match_score <= 100",
            name="ck_result_match_score_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("recommendation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    # Real provider-supplied URLs -- persisted verbatim, never invented.
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    pinterest_url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    match_score: Mapped[int] = mapped_column(Integer, nullable=False)
    match_reason: Mapped[str] = mapped_column(Text, nullable=False)

    # External provider id (e.g. Pinterest pin id) where available.
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    # Ordering of this result within the session (0-based rank).
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    # Normalized characteristic tags for this result (from the candidate pin).
    # Persisted so feedback can derive preference keys deterministically instead
    # of brittle-parsing English from match_reason. server_default '[]' backfills
    # any pre-existing rows created before this column was added.
    tags: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["RecommendationSession"] = relationship(back_populates="results")
    feedback: Mapped[list["Feedback"]] = relationship(
        back_populates="result",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
