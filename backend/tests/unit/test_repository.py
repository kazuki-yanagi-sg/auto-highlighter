"""ステップ2: Repository のテスト。SQLite in-memory で永続化の往復を検証する。"""

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
def session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


@pytest.fixture()
def session(session_factory):
    s = session_factory()
    yield s
    s.close()


def _sample_document() -> Document:
    return Document(
        url="https://example.com/article",
        title="サンプル記事",
        segments=[
            Segment(order=0, text="重要な主張。", marker=Color.RED),
            Segment(order=1, text="ただの説明。", marker=None),
            Segment(order=2, text="例えば〜。", marker=Color.GREEN),
        ],
    )


def test_save_and_get_document_roundtrips_segments_and_markers(session):
    repo = SqlAlchemyDocumentRepository(session)

    saved = repo.add(_sample_document())
    assert saved.id is not None

    fetched = repo.get(saved.id)
    assert fetched is not None
    assert fetched.url == "https://example.com/article"
    assert fetched.title == "サンプル記事"
    assert [s.order for s in fetched.segments] == [0, 1, 2]
    assert [s.text for s in fetched.segments] == ["重要な主張。", "ただの説明。", "例えば〜。"]
    assert [s.marker for s in fetched.segments] == [Color.RED, None, Color.GREEN]
    # segment は永続化後に id を持つ
    assert all(s.id is not None for s in fetched.segments)


def test_get_missing_document_returns_none(session):
    repo = SqlAlchemyDocumentRepository(session)
    assert repo.get(999) is None


def test_note_crud(session):
    doc_repo = SqlAlchemyDocumentRepository(session)
    note_repo = SqlAlchemyNoteRepository(session)
    doc = doc_repo.add(_sample_document())
    target_segment = doc.segments[0]

    note = note_repo.add(
        StickyNote(
            document_id=doc.id,
            segment_id=target_segment.id,
            body="ここ疑問",
            x=10.0,
            y=20.0,
        )
    )
    assert note.id is not None
    assert note.created_at is not None

    listed = note_repo.list_for_document(doc.id)
    assert [n.body for n in listed] == ["ここ疑問"]

    note.body = "やっぱり重要"
    updated = note_repo.update(note)
    assert note_repo.get(note.id).body == "やっぱり重要"
    assert updated.body == "やっぱり重要"

    note_repo.delete(note.id)
    assert note_repo.get(note.id) is None
    assert note_repo.list_for_document(doc.id) == []


def test_document_get_includes_notes(session):
    doc_repo = SqlAlchemyDocumentRepository(session)
    note_repo = SqlAlchemyNoteRepository(session)
    doc = doc_repo.add(_sample_document())
    note_repo.add(
        StickyNote(document_id=doc.id, segment_id=doc.segments[1].id, body="メモ")
    )

    fetched = doc_repo.get(doc.id)
    assert [n.body for n in fetched.notes] == ["メモ"]
