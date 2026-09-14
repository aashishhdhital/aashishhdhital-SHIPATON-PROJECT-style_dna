"""Health check router.

Exposes `GET /health`, used to quickly verify that the backend is running.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple liveness payload."""
    return {"status": "ok"}
