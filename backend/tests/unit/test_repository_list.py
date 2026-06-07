"""P4: 一覧/検索/カテゴリ/ページネーションのリポジトリテスト。"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.models import Color, Document, Segment, StickyNote
from app.repositories.orm import Base
from app.repositories.sqlalchemy_repo import (
    SqlAlchemyDocumentRepository,
    SqlAlchemyNoteRepository,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()


def _seed(repo):
    repo.add(Document(url="https://a.com/python", title="Python入門", category="技術",
                      segments=[Segment(order=0, text="x。")]))
    repo.add(Document(url="https://b.com/economy", title="経済の話", category="ビジネス",
                      segments=[Segment(order=0, text="y。")]))
    repo.add(Document(url="https://c.com/python-web", title="Web開発", category="技術",
                      segments=[Segment(order=0, text="z。")]))


def test_list_summaries_returns_lightweight_items_newest_first(session):
    repo = SqlAlchemyDocumentRepository(session)
    _seed(repo)
    items = repo.list_summaries(page=1, size=10, query=None, category=None)
    assert [i.title for i in items] == ["Web開発", "経済の話", "Python入門"]
    # サマリは id/title/url/category を持つ(segmentsは持たない=軽量)
    assert items[0].category == "技術"
    assert not hasattr(items[0], "segments")


def test_pagination(session):
    repo = SqlAlchemyDocumentRepository(session)
    _seed(repo)
    page1 = repo.list_summaries(page=1, size=2, query=None, category=None)
    page2 = repo.list_summaries(page=2, size=2, query=None, category=None)
    assert len(page1) == 2
    assert len(page2) == 1
    assert repo.count(query=None, category=None) == 3


def test_query_matches_title_or_url_partial(session):
    repo = SqlAlchemyDocumentRepository(session)
    _seed(repo)
    # url 部分一致("python" は a.com/python と c.com/python-web)
    by_url = repo.list_summaries(page=1, size=10, query="python", category=None)
    assert {i.title for i in by_url} == {"Python入門", "Web開発"}
    # title 部分一致
    by_title = repo.list_summaries(page=1, size=10, query="経済", category=None)
    assert [i.title for i in by_title] == ["経済の話"]
    assert repo.count(query="python", category=None) == 2


def test_category_filter(session):
    repo = SqlAlchemyDocumentRepository(session)
    _seed(repo)
    tech = repo.list_summaries(page=1, size=10, query=None, category="技術")
    assert {i.title for i in tech} == {"Python入門", "Web開発"}
    assert repo.count(query=None, category="技術") == 2


def test_query_and_category_combined(session):
    repo = SqlAlchemyDocumentRepository(session)
    _seed(repo)
    items = repo.list_summaries(page=1, size=10, query="python", category="技術")
    assert {i.title for i in items} == {"Python入門", "Web開発"}


def test_list_categories_distinct(session):
    repo = SqlAlchemyDocumentRepository(session)
    _seed(repo)
    assert sorted(repo.list_categories()) == ["ビジネス", "技術"]


def test_summary_includes_marker_counts_and_note_count(session):
    repo = SqlAlchemyDocumentRepository(session)
    notes = SqlAlchemyNoteRepository(session)
    doc = repo.add(
        Document(
            url="https://x.com/a",
            title="記事",
            category="技術",
            segments=[
                Segment(order=0, text="a。", marker=Color.RED),
                Segment(order=1, text="b。", marker=Color.RED),
                Segment(order=2, text="c。", marker=Color.GREEN),
                Segment(order=3, text="d。", marker=None),
            ],
        )
    )
    saved = repo.get(doc.id)
    notes.add(StickyNote(document_id=doc.id, segment_id=saved.segments[0].id, body="m"))

    summary = repo.list_summaries(page=1, size=10, query=None, category=None)[0]
    assert summary.marker_counts["red"] == 2
    assert summary.marker_counts["green"] == 1
    assert summary.marker_counts["yellow"] == 0
    assert summary.marker_counts["blue"] == 0
    assert summary.note_count == 1


def test_summary_counts_default_to_zero(session):
    repo = SqlAlchemyDocumentRepository(session)
    _seed(repo)  # マーカー/付箋なしのドキュメント
    summary = repo.list_summaries(page=1, size=1, query=None, category=None)[0]
    assert summary.marker_counts == {"red": 0, "yellow": 0, "blue": 0, "green": 0}
    assert summary.note_count == 0
