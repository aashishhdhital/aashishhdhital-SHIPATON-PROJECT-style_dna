"""SQLAlchemy database foundation.

Provides the engine, session factory, declarative `Base`, and the `get_db()`
FastAPI dependency. Domain models are intentionally NOT defined here yet; they
will subclass `Base` in the `models/` package in a later step.

Uses SQLAlchemy 2.x conventions (typed `DeclarativeBase`) and PostgreSQL via
the psycopg (v3) driver.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# `create_engine` does not open a connection immediately, so the app can start
# even if the database is not reachable yet. `pool_pre_ping` avoids handing out
# stale connections after the DB restarts.
engine = create_engine(
    settings.database_url,
    echo=settings.sql_echo,
    pool_pre_ping=True,
    future=True,
)

# Session factory. One session is created per request via `get_db()`.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


def init_db() -> None:
    """Create all tables that are registered on ``Base.metadata``.

    Importing ``app.models`` ensures every model class is registered before we
    call ``create_all``. Errors are intentionally NOT swallowed so a failed DB
    connection surfaces loudly at startup.
    """
    import app.models  # noqa: F401  (registers all tables on Base.metadata)

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request.

    The session is always closed after the request completes, even on error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
