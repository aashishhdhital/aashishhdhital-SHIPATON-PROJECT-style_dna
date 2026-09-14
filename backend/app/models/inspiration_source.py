"""InspirationSource model.

Represents BOTH uploaded-image inspiration and Pinterest Pin inspiration in a
single table (no polymorphic inheritance). ``source_type`` distinguishes them.

We use plain string columns guarded by CHECK constraints instead of native
Postgres ENUM types. For an MVP this keeps the controlled vocabularies enforced
at the DB level while remaining trivial to extend (no ``ALTER TYPE`` dance that
native enums require).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.style_profile import StyleProfile
    from app.models.user import User

# Controlled vocabularies (kept here as the single source of truth).
SOURCE_TYPES = ("image", "pinterest")
INSPIRATION_STATUSES = ("pending", "processed", "failed")


class InspirationSource(Base):
    __tablename__ = "inspiration_sources"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('image', 'pinterest')",
            name="ck_inspiration_source_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'processed', 'failed')",
            name="ck_inspiration_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Nullable until analysis produces a StyleProfile this source contributed to.
    style_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("style_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    source_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Original Pinterest Pin URL (preserved verbatim) for pinterest sources.
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Local filesystem path for uploaded images (MVP storage).
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Provider-supplied media URL where available (e.g. Pinterest pin image).
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # External provider id (e.g. Pinterest pin id) where resolvable.
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="inspiration_sources")
    style_profile: Mapped["StyleProfile | None"] = relationship(
        back_populates="inspiration_sources"
    )
