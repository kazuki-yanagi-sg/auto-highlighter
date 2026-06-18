"""API 入出力の Pydantic DTO とドメイン→DTOの変換。

マーカー色は frontend が扱いやすいよう小文字名(red/yellow/blue/green)で入出力する。
"""

from __future__ import annotations

from pydantic import BaseModel

from datetime import datetime

from app.domain.models import Color, Document, DocumentSummary, StickyNote


def color_to_api(color: Color | None) -> str | None:
    return color.name.lower() if color is not None else None


def color_from_api(value: str) -> Color | None:
    """"red"/"yellow"/"blue"/"green" を Color に変換。未知なら None。"""
    try:
        return Color[value.strip().upper()]
    except (KeyError, AttributeError):
        return None


class CreateDocumentIn(BaseModel):
    url: str


class CreateNoteIn(BaseModel):
    body: str
    segment_id: int | None = None
    page: int = 0
    x: float = 0.0
    y: float = 0.0
    w: float = 176.0
    h: float = 150.0


class UpdateNoteIn(BaseModel):
    body: str | None = None
    x: float | None = None
    y: float | None = None
    w: float | None = None
    h: float | None = None


class SegmentOut(BaseModel):
    id: int
    order: int
    text: str
    marker: str | None
    page: int
    block: int
    kind: str = "text"


class NoteOut(BaseModel):
    id: int
    document_id: int
    segment_id: int | None
    body: str
    page: int
    x: float
    y: float
    w: float
    h: float


class DocumentOut(BaseModel):
    id: int
    url: str
    title: str
    category: str | None
    segments: list[SegmentOut]
    notes: list[NoteOut]


class CreateDocumentOut(BaseModel):
    document: DocumentOut
    job_id: str


class JobProgressOut(BaseModel):
    status: str
    done: int
    total: int
    percent: int
    eta_seconds: int | None
    category: str | None
    markers: dict[int, str]
    detail: str | None


class DocumentSummaryOut(BaseModel):
    id: int
    url: str
    title: str
    category: str | None
    created_at: datetime | None
    marker_counts: dict[str, int]
    note_count: int


class PageOut(BaseModel):
    items: list[DocumentSummaryOut]
    total: int
    page: int
    size: int


def summary_to_out(summary: DocumentSummary) -> DocumentSummaryOut:
    return DocumentSummaryOut(
        id=summary.id,
        url=summary.url,
        title=summary.title,
        category=summary.category,
        created_at=summary.created_at,
        marker_counts=summary.marker_counts,
        note_count=summary.note_count,
    )


def note_to_out(note: StickyNote) -> NoteOut:
    return NoteOut(
        id=note.id,
        document_id=note.document_id,
        segment_id=note.segment_id,
        body=note.body,
        page=note.page,
        x=note.x,
        y=note.y,
        w=note.w,
        h=note.h,
    )


def document_to_out(document: Document) -> DocumentOut:
    return DocumentOut(
        id=document.id,
        url=document.url,
        title=document.title,
        category=document.category,
        segments=[
            SegmentOut(
                id=s.id,
                order=s.order,
                text=s.text,
                marker=color_to_api(s.marker),
                page=s.page,
                block=s.block,
                kind=s.kind,
            )
            for s in document.segments
        ],
        notes=[note_to_out(n) for n in document.notes],
    )
