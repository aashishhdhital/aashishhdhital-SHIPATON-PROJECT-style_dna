"""Style analysis router.

Thin HTTP layer for ``POST /style/analyze``. It parses the multipart request,
performs input-level validation of uploaded images (count / size / real MIME
type), delegates all business logic to ``style_service``, and maps domain
errors to HTTP responses. No SQL, file persistence, or Style DNA logic here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.style import AnalyzeResponse
from app.services import style_service
from app.services.style_service import ImageBlob
from app.storage.local_storage import detect_image_type

router = APIRouter(tags=["style"])


@router.post("/style/analyze", response_model=AnalyzeResponse)
async def analyze_style(
    user_id: int = Form(...),
    images: list[UploadFile] | None = File(None),
    pinterest_urls: list[str] | None = Form(None),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    images = images or []
    # Drop empty form entries (an empty pinterest_urls field can arrive as "").
    pinterest_urls = [u for u in (pinterest_urls or []) if u.strip()]

    # Require at least one inspiration source.
    if not images and not pinterest_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one inspiration source (images or pinterest_urls).",
        )

    # Enforce max image count.
    if len(images) > settings.max_upload_images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many images (max {settings.max_upload_images}).",
        )

    # Validate each upload by content, not by filename/Content-Type.
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
        blobs.append(ImageBlob(data=data, extension=detected[1]))

    # Delegate to the service; map domain errors to HTTP responses.
    try:
        return style_service.analyze_inspiration(
            db=db,
            user_id=user_id,
            images=blobs,
            pinterest_urls=pinterest_urls,
        )
    except style_service.UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except style_service.InvalidInspirationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
