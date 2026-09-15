"""Pinterest provider boundary.

All Pinterest I/O lives behind this module. The rest of the app depends only on
the normalized ``PinCandidate`` shape below, never on Pinterest's raw API format,
so the real integration can be dropped in later without touching services.

============================ TEMPORARY MOCK ============================
``search()`` currently returns a small, DETERMINISTIC set of clearly-labeled
LOCAL DEV FIXTURES. These are NOT real Pinterest pins. They exist only so the
recommendation flow can be exercised end-to-end before the real integration.

When the real provider is implemented it will:
    query -> Pinterest Search API -> real pins -> normalize to PinCandidate
and the production path MUST return real pins (never fabricated URLs served to
users). The fixture URLs below use an obvious ``mock.invalid`` host so they can
never be mistaken for real pin links.
=======================================================================
"""

from __future__ import annotations

from app.providers.candidates import PinCandidate, ProviderError as PinterestProviderError


# Deterministic local-dev fixtures. Host is intentionally ``mock.invalid`` so
# these can never be confused with real pins. Replace with real API results.
_MOCK_PINS: tuple[PinCandidate, ...] = (
    PinCandidate(
        external_id="mock-1",
        title="Minimal black streetwear outfit",
        image_url="https://mock.invalid/pins/mock-1.jpg",
        pinterest_url="https://mock.invalid/pin/mock-1",
        description="Oversized black tee, relaxed trousers, chunky sneakers.",
        tags=("streetwear", "minimalist", "black", "oversized", "relaxed"),
    ),
    PinCandidate(
        external_id="mock-2",
        title="Neutral minimalist capsule look",
        image_url="https://mock.invalid/pins/mock-2.jpg",
        pinterest_url="https://mock.invalid/pin/mock-2",
        description="Cream knit, wide-leg trousers, clean silhouette.",
        tags=("minimalist", "cream", "wide-leg trousers", "neutral palette"),
    ),
    PinCandidate(
        external_id="mock-3",
        title="Vintage denim streetwear fit",
        image_url="https://mock.invalid/pins/mock-3.jpg",
        pinterest_url="https://mock.invalid/pin/mock-3",
        description="Washed denim jacket, graphic tee, retro sneakers.",
        tags=("vintage", "streetwear", "denim", "oversized jacket"),
    ),
    PinCandidate(
        external_id="mock-4",
        title="Gray tailored smart-casual",
        image_url="https://mock.invalid/pins/mock-4.jpg",
        pinterest_url="https://mock.invalid/pin/mock-4",
        description="Gray blazer, straight trousers, minimal accessories.",
        tags=("minimalist", "gray", "tailored", "solid"),
    ),
    PinCandidate(
        external_id="mock-5",
        title="Cozy relaxed neutral layers",
        image_url="https://mock.invalid/pins/mock-5.jpg",
        pinterest_url="https://mock.invalid/pin/mock-5",
        description="Beige overshirt, cotton tee, relaxed fit.",
        tags=("relaxed", "cotton", "neutral palette", "beige"),
    ),
    PinCandidate(
        external_id="mock-6",
        title="Bold patterned statement outfit",
        image_url="https://mock.invalid/pins/mock-6.jpg",
        pinterest_url="https://mock.invalid/pin/mock-6",
        description="Printed shirt, colorful trousers, standout accessories.",
        tags=("maximalist", "patterned", "colorful", "bold"),
    ),
)


def search(query: str, limit: int = 10) -> list[PinCandidate]:
    """Return candidate pins for a search ``query`` (MOCK: deterministic fixtures).

    The real implementation will call the Pinterest Search API with ``query``.
    The mock ignores the query content and returns the fixture set (sliced to
    ``limit``) so ranking against the user's Style DNA can be demonstrated.
    """
    if limit <= 0:
        return []
    return list(_MOCK_PINS[:limit])
