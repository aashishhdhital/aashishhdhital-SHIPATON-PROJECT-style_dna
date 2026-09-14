"""Inspiration schemas.

Public shapes for supplying and returning inspiration sources. Pinterest *host*
validation (ensuring the URL is actually a Pinterest domain) is deliberately left
to route/service validation -- here we only assert it is a well-formed URL.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.schemas.common import InspirationStatus, SourceType


class PinterestLinkInput(BaseModel):
    """A user-provided Pinterest Pin URL used as inspiration."""

    # HttpUrl only guarantees a syntactically valid http(s) URL. Confirming the
    # host is Pinterest (and that the pin exists) happens later in the service.
    url: HttpUrl


class InspirationSourceOut(BaseModel):
    """Public representation of a stored inspiration source.

    Note: the internal local filesystem ``image_path`` is intentionally NOT
    exposed -- only the public ``image_url`` (where available) is returned.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: SourceType
    source_url: str | None = None
    image_url: str | None = None
    status: InspirationStatus
