"""DocumentRepository / NoteRepository の SQLAlchemy 実装。

ドメインのdataclass ⇔ ORM行 の変換をこの層に閉じ込める。
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.models import (
    Color,
    Document,
    DocumentSummary,
    Segment,
    StickyNote,
)
from app.repositories.interfaces import DocumentRepository, NoteRepository
from app.repositories.orm import DocumentRow, NoteRow, SegmentRow


def _zero_counts() -> dict[str, int]:
    return {"red": 0, "yellow": 0, "blue": 0, "green": 0}


def _marker_to_db(marker: Color | None) -> str | None:
    return marker.name if marker is not None else None


def _marker_from_db(value: str | None) -> Color | None:
    return Color[value] if value else None


def _segment_from_row(row: SegmentRow) -> Segment:
    return Segment(
        id=row.id,
        document_id=row.document_id,
        order=row.order,
        text=row.text,
        marker=_marker_from_db(row.marker),
        page=row.page,
    )


def _note_from_row(row: NoteRow) -> StickyNote:
    return StickyNote(
        id=row.id,
        document_id=row.document_id,
        segment_id=row.segment_id,
        body=row.body,
        page=row.page,
        x=row.x,
        y=row.y,
        w=row.w,
        h=row.h,
        created_at=row.created_at,
    )


def _document_from_row(row: DocumentRow) -> Document:
    return Document(
        id=row.id,
        url=row.url,
        title=row.title,
        category=row.category,
        created_at=row.created_at,
        segments=[_segment_from_row(s) for s in row.segments],
        notes=[_note_from_row(n) for n in row.notes],
    )


class SqlAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, session: Session):
        self._session = session

    def add(self, document: Document) -> Document:
        row = DocumentRow(
            url=document.url,
            title=document.title,
            category=document.category,
            segments=[
                SegmentRow(
                    order=s.order,
                    text=s.text,
                    marker=_marker_to_db(s.marker),
                    page=s.page,
                )
                for s in document.segments
            ],
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _document_from_row(row)

    def get(self, document_id: int) -> Document | None:
        row = self._session.get(DocumentRow, document_id)
        if row is None:
            return None
        return _document_from_row(row)

    def apply_markers(self, document_id: int, markers: dict[int, Color]) -> None:
        if not markers:
            return
        rows = (
            self._session.query(SegmentRow)
            .filter(SegmentRow.document_id == document_id)
            .filter(SegmentRow.order.in_(list(markers.keys())))
            .all()
        )
        for row in rows:
            row.marker = _marker_to_db(markers.get(row.order))
        self._session.commit()

    def set_category(self, document_id: int, category: str) -> None:
        row = self._session.get(DocumentRow, document_id)
        if row is None:
            return
        row.category = category
        self._session.commit()

    def delete(self, document_id: int) -> None:
        row = self._session.get(DocumentRow, document_id)
        if row is None:
            return
        self._session.delete(row)  # segments/notes は cascade で連動削除
        self._session.commit()

    def list_summaries(
        self, page: int, size: int, query: str | None, category: str | None
    ) -> list[DocumentSummary]:
        stmt = self._apply_filters(
            self._session.query(DocumentRow), query, category
        ).order_by(DocumentRow.id.desc())
        offset = max(page - 1, 0) * size
        rows = stmt.offset(offset).limit(size).all()

        doc_ids = [r.id for r in rows]
        markers = self._marker_counts_for(doc_ids)
        notes = self._note_counts_for(doc_ids)
        return [
            DocumentSummary(
                id=r.id,
                url=r.url,
                title=r.title,
                category=r.category,
                created_at=r.created_at,
                marker_counts=markers.get(r.id, _zero_counts()),
                note_count=notes.get(r.id, 0),
            )
            for r in rows
        ]

    def _marker_counts_for(self, doc_ids: list[int]) -> dict[int, dict[str, int]]:
        if not doc_ids:
            return {}
        rows = (
            self._session.query(
                SegmentRow.document_id, SegmentRow.marker, func.count()
            )
            .filter(SegmentRow.document_id.in_(doc_ids))
            .filter(SegmentRow.marker.isnot(None))
            .group_by(SegmentRow.document_id, SegmentRow.marker)
            .all()
        )
        result: dict[int, dict[str, int]] = {}
        for document_id, marker, count in rows:
            counts = result.setdefault(document_id, _zero_counts())
            counts[Color[marker].name.lower()] = count
        return result

    def _note_counts_for(self, doc_ids: list[int]) -> dict[int, int]:
        if not doc_ids:
            return {}
        rows = (
            self._session.query(NoteRow.document_id, func.count())
            .filter(NoteRow.document_id.in_(doc_ids))
            .group_by(NoteRow.document_id)
            .all()
        )
        return {document_id: count for document_id, count in rows}

    def count(self, query: str | None, category: str | None) -> int:
        return self._apply_filters(
            self._session.query(DocumentRow), query, category
        ).count()

    def list_categories(self) -> list[str]:
        rows = (
            self._session.query(DocumentRow.category)
            .filter(DocumentRow.category.isnot(None))
            .distinct()
            .all()
        )
        return [r[0] for r in rows]

    @staticmethod
    def _apply_filters(stmt, query: str | None, category: str | None):
        if query:
            like = f"%{query}%"
            stmt = stmt.filter(
                DocumentRow.title.ilike(like) | DocumentRow.url.ilike(like)
            )
        if category:
            stmt = stmt.filter(DocumentRow.category == category)
        return stmt


class SqlAlchemyNoteRepository(NoteRepository):
    def __init__(self, session: Session):
        self._session = session

    def add(self, note: StickyNote) -> StickyNote:
        row = NoteRow(
            document_id=note.document_id,
            segment_id=note.segment_id,
            body=note.body,
            page=note.page,
            x=note.x,
            y=note.y,
            w=note.w,
            h=note.h,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _note_from_row(row)

    def get(self, note_id: int) -> StickyNote | None:
        row = self._session.get(NoteRow, note_id)
        if row is None:
            return None
        return _note_from_row(row)

    def list_for_document(self, document_id: int) -> list[StickyNote]:
        rows = (
            self._session.query(NoteRow)
            .filter(NoteRow.document_id == document_id)
            .order_by(NoteRow.id)
            .all()
        )
        return [_note_from_row(r) for r in rows]

    def update(self, note: StickyNote) -> StickyNote:
        row = self._session.get(NoteRow, note.id)
        if row is None:
            raise ValueError(f"note {note.id} が存在しません")
        row.body = note.body
        row.x = note.x
        row.y = note.y
        row.w = note.w
        row.h = note.h
        self._session.commit()
        self._session.refresh(row)
        return _note_from_row(row)

    def delete(self, note_id: int) -> None:
        row = self._session.get(NoteRow, note_id)
        if row is None:
            return
        self._session.delete(row)
        self._session.commit()
