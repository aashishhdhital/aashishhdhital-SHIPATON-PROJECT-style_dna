"""Local filesystem storage for uploaded inspiration images (MVP).

This is the minimum storage abstraction. It:
  * detects the real image type from file bytes (never trusts filename/MIME),
  * generates collision-safe UUID filenames,
  * organizes files per user,
  * writes bytes to ``backend/uploads/`` and returns the local path.

The storage boundary is deliberately narrow so it can later be swapped for
Supabase Storage / S3 without touching the service logic. Supabase/S3 are NOT
implemented here.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from app.config import settings

# Magic-byte signatures -> (mime, extension). We identify images by content,
# not by the client-supplied filename or Content-Type header.
_JPEG_SIG = b"\xff\xd8\xff"
_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def detect_image_type(data: bytes) -> tuple[str, str] | None:
    """Return ``(mime, extension)`` for supported images, else ``None``.

    Detection is based purely on the leading bytes of the file.
    Supported: JPEG, PNG, WebP.
    """
    if data.startswith(_JPEG_SIG):
        return "image/jpeg", "jpg"
    if data.startswith(_PNG_SIG):
        return "image/png", "png"
    # WebP: "RIFF" .... "WEBP"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", "webp"
    return None


def save_image(user_id: int, data: bytes, extension: str) -> str:
    """Persist image ``data`` for ``user_id`` and return the absolute path.

    The filename is a fresh UUID (user-supplied names are never used), stored
    under ``<upload_dir>/<user_id>/``.
    """
    user_dir = Path(settings.upload_dir) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{extension}"
    path = user_dir / filename
    path.write_bytes(data)
    return str(path)


def delete_file(path: str) -> None:
    """Best-effort deletion used for cleanup when a DB transaction rolls back."""
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        # Cleanup is best-effort; never mask the original error with a new one.
        pass
