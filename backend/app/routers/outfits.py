"""Outfits router.

Thin HTTP layer for ``POST /outfits/generate``. Validates the request body via
``GenerateRequest``, delegates to ``recommendation_service``, and maps domain
errors to HTTP responses. No SQL, ranking, or provider logic here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.providers.flickr_provider import FlickrProviderError, FlickrRateLimitError
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.schemas.recommendation import GenerateRequest, GenerateResponse
from app.services import feedback_service, recommendation_service

router = APIRouter(tags=["outfits"])


@router.post("/outfits/generate", response_model=GenerateResponse)
def generate_outfits(
    payload: GenerateRequest,
    db: Session = Depends(get_db),
) -> GenerateResponse:
    try:
        return recommendation_service.generate(
            db=db,
            user_id=payload.user_id,
            occasion=payload.occasion,
            context=payload.context,
        )
    except recommendation_service.UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except recommendation_service.ProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except FlickrRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except FlickrProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    except recommendation_service.ProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc


@router.post("/outfits/{outfit_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    payload: FeedbackRequest,
    outfit_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    try:
        return feedback_service.submit_feedback(
            db=db,
            outfit_id=outfit_id,
            result_id=payload.result_id,
            reaction=payload.reaction,
        )
    except feedback_service.SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except feedback_service.ResultNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
