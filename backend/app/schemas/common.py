"""Shared schema building blocks.

Small reusable Annotated constraint types and Literals used across multiple
schema modules, so identical validation isn't duplicated. These are pure
Pydantic v2 types with no dependency on the SQLAlchemy models.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, StringConstraints

# A non-empty, whitespace-stripped string (rejects "" and "   ").
NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

# An integer score constrained to the 0-100 range.
Score = Annotated[int, Field(ge=0, le=100)]

# Identifiers are always positive.
PositiveInt = Annotated[int, Field(gt=0)]

# Counts / positions are never negative.
NonNegativeInt = Annotated[int, Field(ge=0)]

# Controlled vocabularies mirrored from the SQLAlchemy CHECK constraints.
# (Kept in sync manually; the DB remains the enforcing authority.)
ProviderStatus = Literal["ok", "degraded", "failed"]
Reaction = Literal["like", "maybe", "dislike"]
SourceType = Literal["image", "pinterest"]
InspirationStatus = Literal["pending", "processed", "failed"]
