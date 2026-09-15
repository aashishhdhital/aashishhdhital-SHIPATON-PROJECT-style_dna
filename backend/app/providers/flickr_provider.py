"""Flickr REST provider (official API only -- no HTML scraping).

Responsibilities:
  * SSRF-safe short-URL resolution (flic.kr -> flickr.com)
  * photoset/album lookup via flickr.photosets.getPhotos
  * public photo search via flickr.photos.search
  * HTTPS image-byte download from Flickr static hosts only

The rest of the app consumes ``FlickrPhoto`` / ``VisualCandidate``, never raw
Flickr JSON.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx

from app.config import settings
from app.providers.candidates import ProviderError, VisualCandidate
from app.storage.local_storage import detect_image_type

_FLICKR_REST = "https://www.flickr.com/services/rest/"

# Exact hosts + suffix rules (leading-dot) so evilflickr.com cannot pass.
_PAGE_HOSTS = {"flickr.com", "www.flickr.com", "flic.kr", "www.flic.kr"}
_PAGE_SUFFIXES = (".flickr.com",)
_IMAGE_HOSTS = {"live.staticflickr.com", "staticflickr.com"}
_IMAGE_SUFFIXES = (".staticflickr.com",)

_ALBUM_PATH = re.compile(
    r"/photos/([^/]+)/(?:albums|sets)/(\d+)", re.IGNORECASE
)

# Flickr extras that yield real image URLs (prefer larger, skip original to
# keep Gemini payloads reasonable).
_SIZE_KEYS = ("url_c", "url_l", "url_z", "url_m", "url_n", "url_s")
_EXTRAS = ",".join((*_SIZE_KEYS, "url_o", "description", "tags", "owner_name", "path_alias"))

_HTTP_TIMEOUT = httpx.Timeout(12.0, connect=8.0)
_MAX_REDIRECTS = 5
_SEARCH_POOL = 20
_USER_AGENT = "StyleDNA/1.0 (hackathon demo; Flickr API client)"
_HTTP_HEADERS = {"User-Agent": _USER_AGENT, "Accept": "application/json,text/html"}

_USER_STREAM_PATH = re.compile(r"^/photos/([^/]+)/?$", re.IGNORECASE)


class FlickrProviderError(ProviderError):
    """Flickr-specific failure (invalid URL, private album, API error, ...)."""


class FlickrUserError(FlickrProviderError):
    """Caller/input problem: bad URL, missing album, empty/private set."""


class FlickrRateLimitError(FlickrProviderError):
    """Flickr returned a rate-limit / 429 response."""


@dataclass(frozen=True)
class FlickrPhoto:
    """Normalized album/search photo for internal use."""

    external_id: str
    image_url: str
    source_page_url: str
    title: str
    description: str | None
    tags: tuple[str, ...]
    owner: str | None = None


def _require_api_key() -> str:
    key = settings.flickr_api_key
    if not key:
        raise FlickrProviderError("FLICKR_API_KEY is not configured")
    return key


def is_flickr_page_url(url: str) -> bool:
    """True for http(s) URLs on Flickr page hosts (not image CDNs)."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname
    if not host:
        return False
    host = host.lower()
    if host in _PAGE_HOSTS:
        return True
    return any(host.endswith(suffix) for suffix in _PAGE_SUFFIXES)


def is_flickr_image_host(url: str) -> bool:
    """True only for Flickr static image CDNs (used before downloading bytes)."""
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        return False
    host = parsed.hostname
    if not host:
        return False
    host = host.lower()
    if host in _IMAGE_HOSTS:
        return True
    return any(host.endswith(suffix) for suffix in _IMAGE_SUFFIXES)


def _raise_for_flickr_stat(payload: dict) -> None:
    if payload.get("stat") == "ok":
        return
    code = payload.get("code")
    message = payload.get("message") or "Flickr API error"
    if code in (105,) or "rate" in str(message).lower():
        raise FlickrRateLimitError(f"Flickr rate limit: {message}")
    # 1 = not found, 2 = permission denied (private / inaccessible)
    if code in (1, 2):
        raise FlickrUserError(f"Flickr API error ({code}): {message}")
    raise FlickrProviderError(f"Flickr API error ({code}): {message}")


def _rest_get(method: str, **params: str) -> dict:
    """Call the official Flickr REST endpoint (JSON, nojsoncallback)."""
    query = {
        "method": method,
        "api_key": _require_api_key(),
        "format": "json",
        "nojsoncallback": "1",
        **params,
    }
    try:
        with httpx.Client(
            timeout=_HTTP_TIMEOUT, follow_redirects=False, headers=_HTTP_HEADERS
        ) as client:
            response = client.get(_FLICKR_REST, params=query)
    except httpx.HTTPError as exc:
        raise FlickrProviderError(f"Flickr request failed: {exc}") from exc

    if response.status_code == 429:
        raise FlickrRateLimitError("Flickr HTTP 429 rate limit")
    if response.status_code >= 400:
        raise FlickrProviderError(f"Flickr HTTP {response.status_code}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise FlickrProviderError("Flickr returned non-JSON") from exc
    if not isinstance(payload, dict):
        raise FlickrProviderError("Flickr returned unexpected JSON")
    _raise_for_flickr_stat(payload)
    return payload


def resolve_album_url(url: str) -> tuple[str, str | None]:
    """Resolve a Flickr album or photostream URL to ``(user_id, photoset_id|None)``.

    Short URLs such as ``https://flic.kr/ps/...`` do not contain a numeric
    photoset id. We follow HTTPS redirects with a hop cap, User-Agent, and host
    allow-list (SSRF-safe).

    After resolving:
      * ``/photos/<user>/albums|<sets>/<id>`` -> photoset
      * ``/photos/<user>/`` (photostream / profile) -> photoset_id is None;
        callers should use flickr.people.getPublicPhotos

    ``flic.kr/ps/...`` is Flickr's photostream short-link, not an album.
    """
    if not is_flickr_page_url(url):
        raise FlickrUserError(f"Not a valid Flickr URL: {url}")

    final_url = _follow_flickr_redirects(url.strip())
    path = urlparse(final_url).path or ""
    match = _ALBUM_PATH.search(path)
    if match:
        user_slug, photoset_id = match.group(1), match.group(2)
        user_id = _lookup_user_id(user_slug, final_url)
        return user_id, photoset_id
    stream = _USER_STREAM_PATH.match(path)
    if stream:
        user_id = _lookup_user_id(stream.group(1), final_url)
        return user_id, None
    raise FlickrUserError(
        "Could not determine Flickr album or photostream from URL "
        f"(resolved to {final_url})"
    )


def _follow_flickr_redirects(url: str) -> str:
    """Follow redirects manually so every hop is host-validated (SSRF)."""
    current = url
    with httpx.Client(timeout=_HTTP_TIMEOUT, follow_redirects=False, headers=_HTTP_HEADERS) as client:
        for _ in range(_MAX_REDIRECTS + 1):
            if not is_flickr_page_url(current):
                raise FlickrProviderError(
                    f"Refusing non-Flickr redirect target: {current}"
                )
            # Upgrade http->https before fetching.
            parsed = urlparse(current)
            if parsed.scheme == "http":
                current = parsed._replace(scheme="https").geturl()
            try:
                response = client.get(current)
            except httpx.HTTPError as exc:
                raise FlickrProviderError(f"Failed to resolve Flickr URL: {exc}") from exc
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location:
                    raise FlickrProviderError("Flickr redirect missing Location")
                current = urljoin(str(response.url), location)
                continue
            if response.status_code >= 400:
                raise FlickrProviderError(
                    f"Flickr URL resolve HTTP {response.status_code}"
                )
            return str(response.url)
    raise FlickrProviderError("Too many redirects while resolving Flickr URL")


def _lookup_user_id(user_slug: str, page_url: str) -> str:
    """Map a path alias to an NSID via flickr.urls.lookupUser when needed."""
    # NSIDs look like 12345678@N00; path aliases are usernames.
    if "@" in user_slug:
        return user_slug
    lookup_url = f"https://www.flickr.com/photos/{user_slug}/"
    try:
        payload = _rest_get("flickr.urls.lookupUser", url=lookup_url)
        user = payload.get("user") or {}
        user_id = user.get("id")
        if user_id:
            return str(user_id)
    except FlickrProviderError:
        # Fall back to the slug; some Flickr methods accept path_alias.
        pass
    return user_slug


def _photo_image_url(photo: dict) -> str | None:
    """Pick a real Flickr-provided size URL; never invent hosts."""
    for key in _SIZE_KEYS:
        value = photo.get(key)
        if isinstance(value, str) and value.startswith("https://"):
            return value
    # Official static-URL construction (Flickr docs): never used unless we
    # have server+id+secret from the API response itself.
    server = photo.get("server")
    photo_id = photo.get("id")
    secret = photo.get("secret")
    if server and photo_id and secret:
        return f"https://live.staticflickr.com/{server}/{photo_id}_{secret}_z.jpg"
    original = photo.get("url_o")
    if isinstance(original, str) and original.startswith("https://"):
        return original
    return None


def _description_text(raw: object) -> str | None:
    if isinstance(raw, dict):
        text = raw.get("_content")
        return str(text).strip() if text else None
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _tag_tuple(raw: object) -> tuple[str, ...]:
    """Flickr ``tags`` extra is a space-separated string of *Flickr* tags."""
    if not isinstance(raw, str) or not raw.strip():
        return ()
    return tuple(t.lower() for t in raw.split() if t.strip())


def _to_photo(photo: dict, default_owner: str | None) -> FlickrPhoto | None:
    image_url = _photo_image_url(photo)
    photo_id = photo.get("id")
    if not image_url or not photo_id:
        return None
    if not is_flickr_image_host(image_url):
        return None
    owner = photo.get("owner") or photo.get("pathalias") or default_owner
    source_page = (
        f"https://www.flickr.com/photos/{owner}/{photo_id}/"
        if owner
        else f"https://www.flickr.com/photo.gne?id={photo_id}"
    )
    title = str(photo.get("title") or "").strip() or f"Flickr photo {photo_id}"
    return FlickrPhoto(
        external_id=str(photo_id),
        image_url=image_url,
        source_page_url=source_page,
        title=title,
        description=_description_text(photo.get("description")),
        tags=_tag_tuple(photo.get("tags")),
        owner=str(owner) if owner else None,
    )


def _collect_photos(
    raw_photos: object, owner: str | None, limit: int, empty_message: str
) -> list[FlickrPhoto]:
    if isinstance(raw_photos, dict):
        raw_photos = [raw_photos]
    if not raw_photos:
        raise FlickrUserError(empty_message)
    photos: list[FlickrPhoto] = []
    for item in raw_photos:
        if not isinstance(item, dict):
            continue
        converted = _to_photo(item, default_owner=owner)
        if converted:
            photos.append(converted)
        if len(photos) >= limit:
            break
    if not photos:
        raise FlickrProviderError("Flickr photos had no usable image URLs")
    return photos


def get_album_photos(user_id: str, photoset_id: str, limit: int) -> list[FlickrPhoto]:
    """Public photos in a photoset via flickr.photosets.getPhotos."""
    if limit <= 0:
        return []
    payload = _rest_get(
        "flickr.photosets.getPhotos",
        photoset_id=photoset_id,
        user_id=user_id,
        extras=_EXTRAS,
        per_page=str(min(limit, 50)),
        page="1",
        privacy_filter="1",
    )
    photoset = payload.get("photoset") or {}
    owner = photoset.get("owner") or user_id
    return _collect_photos(
        photoset.get("photo") or [],
        owner,
        limit,
        "Flickr album is empty or has no public photos",
    )


def get_public_photos(user_id: str, limit: int) -> list[FlickrPhoto]:
    """Public photostream via flickr.people.getPublicPhotos (official API)."""
    if limit <= 0:
        return []
    payload = _rest_get(
        "flickr.people.getPublicPhotos",
        user_id=user_id,
        extras=_EXTRAS,
        per_page=str(min(limit, 50)),
        page="1",
    )
    photos = payload.get("photos") or {}
    return _collect_photos(
        photos.get("photo") or [],
        user_id,
        limit,
        "Flickr photostream is empty or has no public photos",
    )


def fetch_inspiration_photos(
    user_id: str, photoset_id: str | None, limit: int
) -> list[FlickrPhoto]:
    """Album photos when we have a photoset id; otherwise the public photostream."""
    if photoset_id:
        return get_album_photos(user_id, photoset_id, limit)
    return get_public_photos(user_id, limit)


def download_image(image_url: str, max_bytes: int) -> tuple[bytes, str]:
    """Fetch image bytes from a Flickr CDN URL. Returns (bytes, mime).

    SSRF controls: HTTPS + Flickr static hosts only + size cap + MIME sniff.
    """
    if not is_flickr_image_host(image_url):
        raise FlickrProviderError("Refusing to download non-Flickr image URL")
    try:
        with httpx.Client(
            timeout=_HTTP_TIMEOUT, follow_redirects=False, headers=_HTTP_HEADERS
        ) as client:
            response = client.get(image_url)
    except httpx.HTTPError as exc:
        raise FlickrProviderError(f"Flickr image download failed: {exc}") from exc
    if response.status_code >= 400:
        raise FlickrProviderError(f"Flickr image HTTP {response.status_code}")
    data = response.content
    if len(data) > max_bytes:
        raise FlickrProviderError("Flickr image exceeds maximum size")
    detected = detect_image_type(data)
    if detected is None:
        raise FlickrProviderError("Flickr image is not a supported JPEG/PNG/WebP")
    return data, detected[0]


def search(query: str, limit: int = _SEARCH_POOL) -> list[VisualCandidate]:
    """Public photo search via flickr.photos.search, normalized for ranking.

    Long StyleDNA intents often match zero Flickr text results, so we try the
    full intent then shorter fashion queries. Transient Flickr error 201 is
    retried; we never substitute mock fixtures.
    """
    if limit <= 0:
        return []
    extras = "url_c,url_l,url_z,url_m,url_n,url_s,tags,owner_name,path_alias"
    words = [w for w in query.split() if w]
    queries: list[str] = []
    for candidate in (
        query,
        " ".join([*words[:2], "outfit"]) if len(words) >= 2 else "",
        f"{words[0]} outfit" if words else "",
        "fashion outfit",
    ):
        if candidate and candidate not in queries:
            queries.append(candidate)

    last_error: Exception | None = None
    for text_query in queries:
        payload = None
        for attempt in range(2):
            try:
                payload = _rest_get(
                    "flickr.photos.search",
                    text=text_query,
                    media="photos",
                    safe_search="1",
                    sort="relevance",
                    extras=extras,
                    per_page=str(min(max(limit, 1), 50)),
                    page="1",
                )
                break
            except FlickrProviderError as exc:
                last_error = exc
                if "201" in str(exc) and attempt == 0:
                    continue
                if "201" in str(exc):
                    break
                raise
        if payload is None:
            continue
        photos = (payload.get("photos") or {}).get("photo") or []
        if isinstance(photos, dict):
            photos = [photos]
        candidates: list[VisualCandidate] = []
        for item in photos:
            if not isinstance(item, dict):
                continue
            converted = _to_photo(item, default_owner=item.get("owner"))
            if not converted:
                continue
            candidates.append(
                VisualCandidate(
                    external_id=converted.external_id,
                    title=converted.title,
                    image_url=converted.image_url,
                    pinterest_url=converted.source_page_url,
                    description=converted.description,
                    tags=converted.tags,
                )
            )
            if len(candidates) >= limit:
                break
        if candidates:
            return candidates
    if last_error and "201" in str(last_error):
        raise last_error
    return []
