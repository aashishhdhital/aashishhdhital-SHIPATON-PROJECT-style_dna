"""Style analysis orchestration (business logic for POST /style/analyze).

Coordinates the full vertical slice while staying HTTP-agnostic: it raises
plain domain exceptions that the router maps to HTTP responses.

Inspiration URLs may be Pinterest (legacy field) or Flickr album URLs.
When INSPIRATION_PROVIDER=flickr, Flickr albums are resolved via the official
API, image bytes are downloaded, and (when ANALYZER_PROVIDER=gemini) Gemini
Vision produces one StyleDNA for the collection.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings
from app.models.inspiration_source import InspirationSource
from app.models.style_profile import StyleProfile
from app.models.user import User
from app.providers import flickr_provider
from app.providers.flickr_provider import FlickrProviderError, FlickrRateLimitError
from app.schemas.style import AnalyzeResponse, StyleDNA
from app.services import analyzer
from app.services.gemini_analyzer import GeminiAnalyzerError
from app.services.style_service_urls import classify_inspiration_url
from app.storage import local_storage


class UserNotFoundError(Exception):
    """Raised when the supplied user_id has no matching User row."""


class InvalidInspirationError(Exception):
    """Raised when an inspiration input is invalid."""


class InspirationProviderError(Exception):
    """Raised when a real inspiration provider fails (Flickr, downloads, ...)."""


@dataclass(frozen=True)
class ImageBlob:
    """A validated, in-memory uploaded image ready to be stored."""

    data: bytes
    extension: str
    mime: str = "image/jpeg"


def analyze_inspiration(
    db: Session,
    user_id: int,
    images: list[ImageBlob],
    urls: list[str],
) -> AnalyzeResponse:
    """Run the analyze vertical slice and return an ``AnalyzeResponse``.

    ``urls`` may mix Flickr album URLs and Pinterest URLs; they are classified
    by hostname. At least one image or URL must be present (router-enforced).
    """
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} does not exist")

    flickr_urls: list[str] = []
    pinterest_urls: list[str] = []
    for url in urls:
        kind = classify_inspiration_url(url)
        if kind == "flickr":
            flickr_urls.append(url)
        elif kind == "pinterest":
            pinterest_urls.append(url)
        else:
            raise InvalidInspirationError(f"Not a valid Flickr or Pinterest URL: {url}")

    # Vision input collected for Gemini (uploads + Flickr album photos).
    vision_images: list[tuple[bytes, str]] = [
        (blob.data, blob.mime) for blob in images
    ]

    written_paths: list[str] = []
    try:
        sources: list[InspirationSource] = []

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

        for url in pinterest_urls:
            # Still no Pinterest fetch -- persist the original URL as pending.
            sources.append(
                InspirationSource(
                    user_id=user_id,
                    source_type="pinterest",
                    source_url=url,
                    status="pending",
                )
            )

        for url in flickr_urls:
            if settings.inspiration_provider == "flickr":
                photos, photo_bytes = _ingest_flickr_album(url)
                vision_images.extend(photo_bytes)
                # One InspirationSource row for the album itself (provenance).
                sources.append(
                    InspirationSource(
                        user_id=user_id,
                        source_type="flickr",
                        source_url=url,
                        image_url=photos[0].image_url if photos else None,
                        external_id=photos[0].external_id if photos else None,
                        status="processed",
                    )
                )
            elif settings.inspiration_provider == "mock":
                sources.append(
                    InspirationSource(
                        user_id=user_id,
                        source_type="flickr",
                        source_url=url,
                        status="pending",
                    )
                )
            else:
                raise InspirationProviderError(
                    f"Unknown INSPIRATION_PROVIDER: {settings.inspiration_provider}"
                )

        db.add_all(sources)

        style_dna = _run_analyzer(vision_images)

        profile = StyleProfile(
            user_id=user_id,
            style_data=style_dna.model_dump(),
        )
        db.add(profile)
        db.flush()

        for source in sources:
            source.style_profile_id = profile.id

        db.commit()
    except (FlickrProviderError, GeminiAnalyzerError, InspirationProviderError):
        db.rollback()
        for path in written_paths:
            local_storage.delete_file(path)
        raise
    except Exception:
        db.rollback()
        for path in written_paths:
            local_storage.delete_file(path)
        raise

    return AnalyzeResponse(
        profile_id=profile.id,
        style_dna=style_dna,
        sources_processed=len(images) + len(urls),
        sources_failed=0,
    )


def _ingest_flickr_album(
    album_url: str,
) -> tuple[list, list[tuple[bytes, str]]]:
    """Resolve album URL -> official photoset photos -> download image bytes."""
    try:
        user_id, photoset_id = flickr_provider.resolve_album_url(album_url)
        limit = min(settings.max_upload_images, 8)
        photos = flickr_provider.fetch_inspiration_photos(
            user_id, photoset_id, limit=limit
        )
        downloaded: list[tuple[bytes, str]] = []
        # Only pull bytes when Gemini will actually consume them.
        if settings.analyzer_provider == "gemini":
            for photo in photos:
                data, mime = flickr_provider.download_image(
                    photo.image_url, max_bytes=settings.max_image_bytes
                )
                downloaded.append((data, mime))
        return photos, downloaded
    except FlickrRateLimitError:
        raise
    except FlickrProviderError:
        raise


def _run_analyzer(vision_images: list[tuple[bytes, str]]) -> StyleDNA:
    """Dispatch to mock or Gemini. Real mode never falls back to mock."""
    try:
        return analyzer.analyze_inspiration(vision_images)
    except GeminiAnalyzerError:
        raise
