"""URL classification for inspiration inputs (Flickr vs Pinterest).

Kept separate so SSRF-safe host checks stay reusable and out of the router.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.providers.flickr_provider import is_flickr_page_url
_ALLOWED_PINTEREST_HOSTS = {"pinterest.com", "pin.it"}
_ALLOWED_PINTEREST_SUFFIXES = (".pinterest.com", ".pin.it")


def is_valid_pinterest_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
    except (ValueError, AttributeError):
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname
    if not host:
        return False
    host = host.lower()
    if host in _ALLOWED_PINTEREST_HOSTS:
        return True
    return any(host.endswith(suffix) for suffix in _ALLOWED_PINTEREST_SUFFIXES)


def classify_inspiration_url(url: str) -> str | None:
    """Return 'flickr', 'pinterest', or None."""
    if is_flickr_page_url(url):
        return "flickr"
    if is_valid_pinterest_url(url):
        return "pinterest"
    return None
