"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import articles, inventory


def create_app() -> FastAPI:
    app = FastAPI(
        title="TrackFlow Inventory Manager",
        version="0.1.0",
        description="Unified inventory API — stock derived from movement ledger",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(articles.router)
    app.include_router(inventory.router)

    return app


app = create_app()