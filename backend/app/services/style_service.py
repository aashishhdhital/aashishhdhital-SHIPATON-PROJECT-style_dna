"""Style analysis orchestration (business logic for POST /style/analyze).

Coordinates the full vertical slice while staying HTTP-agnostic: it raises
plain domain exceptions that the router maps to HTTP responses.

Flow:
    1. confirm the user exists
    2. validate + save uploaded images via local storage
    3. persist InspirationSource rows (images + Pinterest URLs)
    4. run the MOCK analyzer and validate its StyleDNA output
    5. persist a StyleProfile
    6. link the request's InspirationSource rows to that profile
    7. commit (rolling back + cleaning up files on failure)
    8. return an AnalyzeResponse
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inspiration_source import InspirationSource
from app.models.style_profile import StyleProfile
from app.models.user import User
from app.schemas.style import AnalyzeResponse
from app.services import analyzer
from app.storage import local_storage


# --------------------------------------------------------------------------- #
# Domain exceptions (mapped to HTTP status codes by the router).
# --------------------------------------------------------------------------- #
class UserNotFoundError(Exception):
    """Raised when the supplied user_id has no matching User row."""


class InvalidInspirationError(Exception):
    """Raised when an inspiration input is invalid (e.g. a non-Pinterest URL)."""


@dataclass(frozen=True)
class ImageBlob:
    """A validated, in-memory uploaded image ready to be stored."""

    data: bytes
    extension: str


# --------------------------------------------------------------------------- #
# Pinterest URL validation (host-based; SSRF-safe). We do NOT fetch the URL.
# --------------------------------------------------------------------------- #
# Exact hosts + suffix rules. Suffix checks require a leading dot so that
# "evilpinterest.com" or "pinterest.com.evil.com" can never match.
_ALLOWED_PINTEREST_HOSTS = {"pinterest.com", "pin.it"}
_ALLOWED_PINTEREST_SUFFIXES = (".pinterest.com", ".pin.it")


def is_valid_pinterest_url(url: str) -> bool:
    """Return True only for well-formed http(s) URLs on a real Pinterest host.

    Uses proper hostname parsing (not substring matching) so look-alike domains
    are rejected. ``urlparse`` also correctly ignores userinfo tricks such as
    ``https://pinterest.com@evil.com`` (hostname there is ``evil.com``).
    """
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


# --------------------------------------------------------------------------- #
# Orchestration.
# --------------------------------------------------------------------------- #
def analyze_inspiration(
    db: Session,
    user_id: int,
    images: list[ImageBlob],
    pinterest_urls: list[str],
) -> AnalyzeResponse:
    """Run the analyze vertical slice and return an ``AnalyzeResponse``.

    ``images`` are already-validated blobs (MIME/size checked at the HTTP layer).
    ``pinterest_urls`` are validated here for host safety before persistence.
    Callers must ensure at least one source is present.
    """
    # 1. Confirm the user exists (never auto-create users here).
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} does not exist")

    # Validate Pinterest URLs up front so we reject bad input before writing any
    # files or rows (keeps the request atomic and avoids orphaned files).
    for url in pinterest_urls:
        if not is_valid_pinterest_url(url):
            raise InvalidInspirationError(f"Not a valid Pinterest URL: {url}")

    written_paths: list[str] = []
    try:
        sources: list[InspirationSource] = []

        # 2 + 3. Save each image and create a "processed" image source. Uploaded
        # images ARE fully ingested locally, so "processed" is accurate.
        for blob in images:
            path = local_storage.save_image(user_id, blob.data, blob.extension)
            written_paths.append(path)
            sources.append(
                InspirationSource(
                    user_id=user_id,
                    source_type="image",
                    image_path=path,
                    status="processed",
                )
            )

        # 4. Persist Pinterest URL sources WITHOUT fetching them. Status is
        # "pending": the pin has been accepted but not yet resolved/analyzed by
        # a real provider, so claiming "processed" would be dishonest.
        for url in pinterest_urls:
            sources.append(
                InspirationSource(
                    user_id=user_id,
                    source_type="pinterest",
                    source_url=url,
                    status="pending",
                )
            )

        db.add_all(sources)

        # 5. Run the MOCK analyzer and validate its output as StyleDNA.
        # NOTE (temporary): even though Pinterest pins are unresolved at this
        # stage, the mock analyzer still produces a StyleDNA so the end-to-end
        # flow is testable. Real analysis will consume resolved pin media later.
        style_dna = analyzer.analyze_inspiration()

        # 6. Persist the StyleProfile (style_data as JSONB). preference_weights
        # stays NULL -- feedback logic is out of scope for this step.
        profile = StyleProfile(
            user_id=user_id,
            style_data=style_dna.model_dump(),
        )
        db.add(profile)
        db.flush()  # assign profile.id

        # 7. Link this request's sources to the generated profile (provenance).
        for source in sources:
            source.style_profile_id = profile.id

        # 8. Commit the whole unit of work.
        db.commit()
    except Exception:
        # Do not swallow DB errors: roll back, clean up any files we wrote this
        # request, then re-raise so the failure surfaces.
        db.rollback()
        for path in written_paths:
            local_storage.delete_file(path)
        raise

    # 9. Build the response. sources_processed = number of inspiration inputs
    # successfully accepted/persisted for this request (images + Pinterest URLs).
    # It intentionally does NOT imply the Pinterest pins were externally resolved
    # -- that happens once the real provider exists. sources_failed is 0 because
    # any invalid input rejects the whole request at validation time.
    return AnalyzeResponse(
        profile_id=profile.id,
        style_dna=style_dna,
        sources_processed=len(images) + len(pinterest_urls),
        sources_failed=0,
    )
