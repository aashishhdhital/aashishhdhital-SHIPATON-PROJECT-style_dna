"""User model.

The account that owns style profiles, inspiration sources, and recommendation
sessions. No authentication fields yet (deliberately out of scope for the MVP).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.inspiration_source import InspirationSource
    from app.models.recommendation_session import RecommendationSession
    from app.models.style_profile import StyleProfile


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # A user accumulates style profiles over time (latest = current Style DNA).
    style_profiles: Mapped[list["StyleProfile"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    inspiration_sources: Mapped[list["InspirationSource"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    recommendation_sessions: Mapped[list["RecommendationSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
