"""API テスト用の共通フィクスチャ。

外部I/O(Scraper / Annotator)はフェイクを注入し、DBは SQLite in-memory を使う。
"""

import io
import wave

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.db import Database
from app.main import create_app
from app.services.annotator import Annotator
from app.services.categorizer import Categorizer
from app.services.scraper import ScrapedContent, Scraper
from app.services.tts import TtsService


def _tiny_wav(nframes: int = 50) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(b"\x00\x00" * nframes)
    return buf.getvalue()


class FakeTts(TtsService):
    """チャンクごとに有効な tiny WAV を返す(ストリーミング検証用)。"""

    def synthesize(self, text: str) -> bytes:
        return _tiny_wav()


class FakeCategorizer(Categorizer):
    def _suggest(self, title, segments):
        return "技術"


class FakeScraper(Scraper):
    def fetch(self, url: str) -> ScrapedContent:
        return ScrapedContent(
            title="記事", text="重要な主張。ただの説明。例えば〜。"
        )


class FakeAnnotator(Annotator):
    def _suggest(self, segments):
        return [
            {"segment_id": 0, "color": "red"},
            {"segment_id": 2, "color": "green"},
        ]


@pytest.fixture()
def app_db():
    return Database("sqlite://")


@pytest.fixture()
def client(app_db):
    app = create_app(database=app_db)
    app.dependency_overrides[deps.get_scraper] = lambda: FakeScraper()
    app.dependency_overrides[deps.get_annotator] = lambda: FakeAnnotator()
    app.dependency_overrides[deps.get_categorizer] = lambda: FakeCategorizer()
    app.dependency_overrides[deps.get_tts] = lambda: FakeTts()
    return TestClient(app)
