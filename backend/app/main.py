from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import deps
from app.api.routers import documents, notes, tts
from app.config import get_settings
from app.db import Database


def create_app(database: Database | None = None) -> FastAPI:
    settings = get_settings()
    db = database or Database(settings.database_url)
    db.create_all()
    deps.set_database(db)

    app = FastAPI(title="マーカ支援アプリ API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(documents.router)
    app.include_router(documents.categories_router)
    app.include_router(notes.router)
    app.include_router(tts.router)
    return app


app = create_app()
