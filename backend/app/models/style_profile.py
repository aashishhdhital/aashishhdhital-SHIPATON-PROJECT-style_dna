"""StyleProfile model.

Stores a user's inspiration-derived Style DNA in a single extensible ``JSONB``
column (``style_data``) so new style dimensions can be added without schema
changes. ``preference_weights`` is kept deliberately SEPARATE from ``style_data``
so feedback-driven adjustments never overwrite the inspiration-derived DNA.

Feedback weighting logic is NOT implemented here yet.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.inspiration_source import InspirationSource
    from app.models.user import User


class StyleProfile(Base):
    __tablename__ = "style_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Inspiration-derived Style DNA (styles/colors/garments/fits/patterns/
    # materials/traits). Extensible by design -- no fixed per-style columns.
    style_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Feedback-adjusted recommendation preferences. Separate from style_data.
    preference_weights: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="style_profiles")

    # Which inspiration sources produced this profile. Sources outlive a profile
    # (their FK is set NULL on profile deletion), so no delete-orphan here.
    inspiration_sources: Mapped[list["InspirationSource"]] = relationship(
        back_populates="style_profile"
    )
