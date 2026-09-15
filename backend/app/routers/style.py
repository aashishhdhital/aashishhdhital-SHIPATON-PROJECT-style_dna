"""Style analysis router.

Thin HTTP layer for ``POST /style/analyze``. Accepts uploaded images plus
inspiration URLs. The legacy ``pinterest_urls`` field is preserved; Flickr
album URLs may be sent there or as ``inspiration_urls``.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BeforeValidator
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.providers.flickr_provider import (
    FlickrProviderError,
    FlickrRateLimitError,
    FlickrUserError,
)
from app.schemas.style import AnalyzeResponse
from app.services import style_service
from app.services.gemini_analyzer import GeminiAnalyzerError
from app.services.style_service import ImageBlob
from app.storage.local_storage import detect_image_type

router = APIRouter(tags=["style"])


def _absent_if_empty_files(value: Any) -> Any:
    """Treat Swagger's empty optional file input as omitted, not invalid.

    Swagger/OpenAPI often submits unused file fields as ``images=`` (an empty
    string). FastAPI then 422s because it expected an UploadFile. Empty values
    are dropped; any non-empty non-file value is left unchanged so validation
    still rejects it.
    """
    if value is None or value == "" or value == b"":
        return None
    if isinstance(value, list):
        kept = [item for item in value if item not in (None, "", b"")]
        return kept or None
    return value


def _absent_if_empty_form_strings(value: Any) -> Any:
    """Treat empty optional text form fields (``pinterest_urls=``) as omitted."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, list):
        kept = [
            item
            for item in value
            if not (isinstance(item, str) and not item.strip())
        ]
        return kept or None
    return value


OptionalImages = Annotated[
    list[UploadFile] | None,
    BeforeValidator(_absent_if_empty_files),
    File(),
]
OptionalUrlList = Annotated[
    list[str] | None,
    BeforeValidator(_absent_if_empty_form_strings),
    Form(),
]


@router.post("/style/analyze", response_model=AnalyzeResponse)
async def analyze_style(
    user_id: int = Form(...),
    images: OptionalImages = None,
    pinterest_urls: OptionalUrlList = None,
    inspiration_urls: OptionalUrlList = None,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    images = images or []
    urls = [u for u in (pinterest_urls or []) + (inspiration_urls or []) if u.strip()]

    if not images and not urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one inspiration source (images, pinterest_urls, or inspiration_urls).",
        )

    if len(images) > settings.max_upload_images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many images (max {settings.max_upload_images}).",
        )

    blobs: list[ImageBlob] = []
    for upload in images:
        data = await upload.read()
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image upload.",
            )
        if len(data) > settings.max_image_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image exceeds max size of {settings.max_image_bytes} bytes.",
            )
        detected = detect_image_type(data)
        if detected is None or detected[0] not in settings.allowed_image_mime:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported image type. Allowed: JPEG, PNG, WebP.",
            )
        mime, ext = detected
        blobs.append(ImageBlob(data=data, extension=ext, mime=mime))

    try:
        return style_service.analyze_inspiration(
            db=db,
            user_id=user_id,
            images=blobs,
            urls=urls,
        )
    except style_service.UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except style_service.InvalidInspirationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except FlickrRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except FlickrUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except FlickrProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    except GeminiAnalyzerError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    except style_service.InspirationProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
