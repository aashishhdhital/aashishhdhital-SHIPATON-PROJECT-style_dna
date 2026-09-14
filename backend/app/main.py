"""StyleDNA API application entrypoint.

`main.py` is responsible for application wiring only:
  * creating the FastAPI application
  * configuring CORS
  * registering routers

It intentionally contains no endpoint business logic. Individual endpoints live
in the `routers/` package.

Run locally with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import health, outfits, profile, style


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown.

    On startup we create any missing tables via ``create_all``. For a one-day
    hackathon MVP this is the cleanest approach: the schema follows the models
    with zero migration overhead. The tradeoff is that ``create_all`` only
    CREATES missing tables -- it does not ALTER existing ones, so later column
    changes won't be picked up automatically. When the schema starts evolving,
    we'll introduce Alembic (deliberately out of scope now).

    Errors are not caught here: if the database is unreachable, startup fails
    loudly rather than hiding the problem.
    """
    init_db()
    yield


def create_app() -> FastAPI:
    """Application factory: build and configure the FastAPI app."""
    app = FastAPI(title="StyleDNA API", lifespan=lifespan)

    # CORS so the Expo mobile client can call the API during development.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers.
    app.include_router(health.router)
    app.include_router(style.router)
    app.include_router(profile.router)
    app.include_router(outfits.router)

    # Table creation is handled on startup by the `lifespan` handler above
    # (Base.metadata.create_all). See its docstring for the MVP tradeoff.

    return app


app = create_app()
