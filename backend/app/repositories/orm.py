"""SQLAlchemy テーブル定義。ドメインモデルとは分離する(永続化の都合をdomainに漏らさない)。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(2048))
    title: Mapped[str] = mapped_column(String(512))
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    segments: Mapped[list["SegmentRow"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="SegmentRow.order",
    )
    notes: Mapped[list["NoteRow"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="NoteRow.id",
    )


class SegmentRow(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    order: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    marker: Mapped[str | None] = mapped_column(String(16), nullable=True)
    page: Mapped[int] = mapped_column(Integer, default=0)

    document: Mapped[DocumentRow] = relationship(back_populates="segments")


class NoteRow(Base):
    __tablename__ = "sticky_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    segment_id: Mapped[int | None] = mapped_column(
        ForeignKey("segments.id"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text)
    page: Mapped[int] = mapped_column(Integer, default=0)
    x: Mapped[float] = mapped_column(Float, default=0.0)
    y: Mapped[float] = mapped_column(Float, default=0.0)
    w: Mapped[float] = mapped_column(Float, default=176.0)
    h: Mapped[float] = mapped_column(Float, default=150.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    document: Mapped[DocumentRow] = relationship(back_populates="notes")
