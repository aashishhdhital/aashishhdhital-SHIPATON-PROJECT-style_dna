"""Profile router.

Thin HTTP layer for ``GET /profile/{user_id}``. Validates the path parameter,
delegates to ``profile_service``, and maps domain errors to HTTP responses.
No SQL or business logic here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.profile import ProfileResponse
from app.services import profile_service

router = APIRouter(tags=["profile"])


@router.get("/profile/{user_id}", response_model=ProfileResponse)
def get_profile(
    user_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    try:
        return profile_service.get_profile(db=db, user_id=user_id)
    except profile_service.UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except profile_service.ProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
