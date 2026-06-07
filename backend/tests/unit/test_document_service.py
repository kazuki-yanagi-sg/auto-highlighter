"""F1: DocumentService の prepare(即保存) と annotate(バッチ注釈＋進捗) の検証。"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.models import Segment
from app.repositories.orm import Base
from app.repositories.sqlalchemy_repo import SqlAlchemyDocumentRepository
from app.services.annotator import Annotator
from app.services.categorizer import Categorizer
from app.services.document_service import ANNOTATE_BATCH, DocumentService
from app.services.scraper import Block, ScrapedContent, Scraper


@pytest.fixture()
def repo():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    return SqlAlchemyDocumentRepository(session)


class ManyScraper(Scraper):
    def __init__(self, n: int):
        self._n = n

    def fetch(self, url: str) -> ScrapedContent:
        text = "".join(f"文{i}。" for i in range(self._n))
        return ScrapedContent(title="長文", text=text, blocks=[Block("text", text)])


class CountingAnnotator(Annotator):
    def __init__(self):
        self.batches = 0

    def _suggest(self, segments):
        self.batches += 1
        return []


class MarkAllRed(Annotator):
    def _suggest(self, segments):
        return [{"segment_id": s.order, "color": "red"} for s in segments]


class FixedCategorizer(Categorizer):
    def _suggest(self, title, segments):
        return "技術"


def test_prepare_saves_without_calling_llm(repo):
    annotator = CountingAnnotator()
    service = DocumentService(ManyScraper(5), annotator, FixedCategorizer(), repo)
    doc = service.prepare_from_url("https://x.com/a")
    assert doc.id is not None
    assert len(doc.segments) == 5
    assert all(s.marker is None for s in doc.segments)
    assert doc.category is None
    assert annotator.batches == 0  # prepare では LLM を呼ばない


def test_annotate_runs_in_batches_with_progress_and_persists(repo):
    n = ANNOTATE_BATCH * 2 + 3  # 3バッチ
    service = DocumentService(ManyScraper(n), MarkAllRed(), FixedCategorizer(), repo)
    doc = service.prepare_from_url("https://x.com/long")

    events: list[tuple[int, int]] = []
    service.annotate_document(doc, progress=lambda d, t, m: events.append((d, t)))

    # 進捗は 0..3 の計4回
    assert events[0][0] == 0
    assert events[-1] == (3, 3)
    # DBにマーカーとカテゴリが反映されている
    saved = repo.get(doc.id)
    assert all(s.marker is not None for s in saved.segments)
    assert saved.category == "技術"
