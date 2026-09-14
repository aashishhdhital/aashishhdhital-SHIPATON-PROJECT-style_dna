"""RecommendationSession model.

Represents one recommendation-generation request. This is the entity that the
API contract's ``outfit_id`` refers to (``POST /outfits/{outfit_id}/feedback``).

``provider_status`` records how the Pinterest provider behaved for this session
(ok / degraded / failed) and is guarded by a CHECK constraint.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.recommendation_result import RecommendationResult
    from app.models.user import User

PROVIDER_STATUSES = ("ok", "degraded", "failed")


class RecommendationSession(Base):
    __tablename__ = "recommendation_sessions"
    __table_args__ = (
        CheckConstraint(
            "provider_status IN ('ok', 'degraded', 'failed')",
            name="ck_session_provider_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    occasion: Mapped[str] = mapped_column(String(255), nullable=False)
    # Optional free-form context supplied with the request.
    context: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # The Pinterest search query/intent generated for this session.
    search_intent: Mapped[str] = mapped_column(Text, nullable=False)
    provider_status: Mapped[str] = mapped_column(String(20), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="recommendation_sessions")
    results: Mapped[list["RecommendationResult"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RecommendationResult.position",
    )
    feedback: Mapped[list["Feedback"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
