"""Provider-neutral visual recommendation candidate.

TECHNICAL DEBT: ranking originally consumed ``PinCandidate`` from the mock
Pinterest provider. Flickr recommendations reuse the same shape so we do not
rewrite ranking/feedback. ``pinterest_url`` is the photo *source page* URL
(Flickr photo page, or mock.invalid in mock mode). The public API field is
unchanged because the mobile app is not being modified in this task.
"""

from __future__ import annotations

from dataclasses import dataclass


class ProviderError(Exception):
    """Raised when an external visual provider cannot return results."""


@dataclass(frozen=True)
class VisualCandidate:
    """Normalized candidate used by the ranking engine.

    ``tags`` are ranking/feedback signals. For Flickr they are Flickr photo
    tags when present -- not a fashion taxonomy invented by us.
    """

    external_id: str
    title: str
    image_url: str
    pinterest_url: str  # source page URL (name kept for API compatibility)
    description: str | None
    tags: tuple[str, ...]


# Backwards-compatible alias so the mock Pinterest module can keep its name.
PinCandidate = VisualCandidate
