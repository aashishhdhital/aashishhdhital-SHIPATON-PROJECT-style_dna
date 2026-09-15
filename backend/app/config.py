"""Centralized application configuration.

All environment access lives here. The rest of the app imports `settings`
(via `get_settings()`) instead of calling `os.getenv()` directly, so there is
a single, typed source of truth for configuration.

We use `python-dotenv` to load a local `.env` file (already installed) and
`pydantic` to validate/coerce values. `pydantic-settings` is intentionally not
used because it is not part of the pinned dependencies.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load variables from a local `.env` (if present) into the process environment.
# In production the environment is expected to be populated by the platform,
# so a missing `.env` file is not an error.
load_dotenv()

# backend/ directory (config.py lives at backend/app/config.py).
_BACKEND_DIR = Path(__file__).resolve().parent.parent

# Upload defaults (overridable via env). Kept modest for an MVP.
_DEFAULT_UPLOAD_DIR = str(_BACKEND_DIR / "uploads")
_DEFAULT_MAX_UPLOAD_IMAGES = 10
_DEFAULT_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
_ALLOWED_IMAGE_MIME = ("image/jpeg", "image/png", "image/webp")


# Default points at a local Postgres instance so the app can start during
# development without any `.env`. It is only used when DATABASE_URL is unset.
_DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/styledna"


def _normalize_database_url(url: str) -> str:
    """Ensure the URL uses the psycopg (v3) driver that we actually install.

    A bare `postgresql://` URL makes SQLAlchemy default to psycopg2, which is
    not in our dependencies. We rewrite it to `postgresql+psycopg://` so the
    installed psycopg 3 driver is used.
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        # Some providers emit the legacy `postgres://` scheme.
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def _parse_cors_origins(raw: str | None) -> list[str]:
    """Parse a comma-separated CORS origins string into a list.

    Defaults to "*" (allow all) which is convenient for local Expo development.
    """
    if not raw or raw.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class Settings(BaseModel):
    """Typed, validated application settings."""

    # Only variables actually needed right now are configured. Pinterest / AI
    # credentials are deliberately NOT required so the app starts without them.
    database_url: str = Field(default=_DEFAULT_DATABASE_URL)
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # Toggles SQLAlchemy engine SQL echoing (useful while developing).
    sql_echo: bool = False

    # Image upload constraints for POST /style/analyze.
    upload_dir: str = Field(default=_DEFAULT_UPLOAD_DIR)
    max_upload_images: int = Field(default=_DEFAULT_MAX_UPLOAD_IMAGES, gt=0)
    max_image_bytes: int = Field(default=_DEFAULT_MAX_IMAGE_BYTES, gt=0)
    allowed_image_mime: tuple[str, ...] = Field(default=_ALLOWED_IMAGE_MIME)

    # External providers. "mock" keeps the original deterministic fixtures.
    # Real demo: ANALYZER_PROVIDER=gemini, INSPIRATION/RECOMMENDATION=flickr.
    analyzer_provider: str = Field(default="mock")
    inspiration_provider: str = Field(default="mock")
    recommendation_provider: str = Field(default="mock")

    # Secrets -- empty by default so the app still starts in mock mode.
    gemini_api_key: str = ""
    gemini_model: str = Field(default="gemini-3.6-flash")
    flickr_api_key: str = ""
    flickr_api_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return a cached `Settings` instance built from the environment.

    Centralizing `os.getenv` access here keeps configuration in one place.
    """
    return Settings(
        database_url=_normalize_database_url(
            os.getenv("DATABASE_URL", _DEFAULT_DATABASE_URL)
        ),
        cors_origins=_parse_cors_origins(os.getenv("CORS_ORIGINS")),
        sql_echo=os.getenv("SQL_ECHO", "false").lower() in {"1", "true", "yes"},
        upload_dir=os.getenv("UPLOAD_DIR", _DEFAULT_UPLOAD_DIR),
        max_upload_images=int(
            os.getenv("MAX_UPLOAD_IMAGES", str(_DEFAULT_MAX_UPLOAD_IMAGES))
        ),
        max_image_bytes=int(
            os.getenv("MAX_IMAGE_BYTES", str(_DEFAULT_MAX_IMAGE_BYTES))
        ),
        analyzer_provider=os.getenv("ANALYZER_PROVIDER", "mock").strip().lower(),
        inspiration_provider=os.getenv("INSPIRATION_PROVIDER", "mock").strip().lower(),
        recommendation_provider=os.getenv(
            "RECOMMENDATION_PROVIDER", "mock"
        ).strip().lower(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
        or "gemini-3.6-flash",
        flickr_api_key=os.getenv("FLICKR_API_KEY", "").strip(),
        flickr_api_secret=os.getenv("FLICKR_API_SECRET", "").strip(),
    )


# Convenient module-level handle for the common case.
settings = get_settings()
