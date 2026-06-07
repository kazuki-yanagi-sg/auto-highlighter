"""依存性注入(DIP)。router は抽象を Depends で受け取り、ここで具象を組み立てる。

具象を差し替えたいテストでは app.dependency_overrides で各 getter を上書きする。
"""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import Database
from app.repositories.interfaces import DocumentRepository, NoteRepository
from app.repositories.sqlalchemy_repo import (
    SqlAlchemyDocumentRepository,
    SqlAlchemyNoteRepository,
)
from app.services.annotator import Annotator, GeminiAnnotator, OllamaAnnotator
from app.services.categorizer import (
    Categorizer,
    GeminiCategorizer,
    OllamaCategorizer,
)
from app.services.scraper import HttpScraper, Scraper
from app.services.tts import TtsService, VoicevoxTts

# create_app() が初期化する。テストでも create_app(database=...) 経由で差し替わる。
_database: Database | None = None


def set_database(database: Database) -> None:
    global _database
    _database = database


def get_settings_dep() -> Settings:
    return get_settings()


def get_database() -> Database:
    """バックグラウンドスレッドが新規 session を作るために Database 本体を渡す。"""
    if _database is None:
        raise RuntimeError("Database が初期化されていません")
    return _database


def get_session() -> Iterator[Session]:
    if _database is None:
        raise RuntimeError("Database が初期化されていません")
    session = _database.session()
    try:
        yield session
    finally:
        session.close()


def get_document_repository(
    session: Session = Depends(get_session),
) -> DocumentRepository:
    return SqlAlchemyDocumentRepository(session)


def get_note_repository(
    session: Session = Depends(get_session),
) -> NoteRepository:
    return SqlAlchemyNoteRepository(session)


def get_scraper() -> Scraper:
    return HttpScraper()


def get_annotator(settings: Settings = Depends(get_settings_dep)) -> Annotator:
    if settings.llm_provider == "ollama":
        return OllamaAnnotator(settings.ollama_url, settings.ollama_model)
    return GeminiAnnotator(settings.gemini_api_key, settings.gemini_model)


def get_categorizer(settings: Settings = Depends(get_settings_dep)) -> Categorizer:
    if settings.llm_provider == "ollama":
        return OllamaCategorizer(settings.ollama_url, settings.ollama_model)
    return GeminiCategorizer(settings.gemini_api_key, settings.gemini_model)


def get_tts(settings: Settings = Depends(get_settings_dep)) -> TtsService:
    return VoicevoxTts(settings.voicevox_url, settings.voicevox_speaker)
