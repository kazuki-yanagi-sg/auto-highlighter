"""永続化の抽象(DIP)。サービス/APIはこの抽象だけに依存する。

ISP: ドキュメントと付箋で別インターフェースに分ける。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import Color, Document, DocumentSummary, StickyNote


class DocumentRepository(ABC):
    @abstractmethod
    def add(self, document: Document) -> Document:
        """ドキュメントと配下のSegment(markerを含む)を保存し、id付きで返す。"""

    @abstractmethod
    def get(self, document_id: int) -> Document | None:
        """id でドキュメントを取得(segments と notes を含む)。無ければ None。"""

    @abstractmethod
    def apply_markers(self, document_id: int, markers: dict[int, Color]) -> None:
        """order→Color のマップで該当 segment のマーカーを更新(増分・ストリーミング用)。"""

    @abstractmethod
    def set_category(self, document_id: int, category: str) -> None:
        """ドキュメントのカテゴリを更新。"""

    @abstractmethod
    def delete(self, document_id: int) -> None:
        """ドキュメントを削除(配下の segments・notes も連動)。無ければ何もしない。"""

    @abstractmethod
    def list_summaries(
        self, page: int, size: int, query: str | None, category: str | None
    ) -> list[DocumentSummary]:
        """一覧用サマリを新しい順で返す(本文は含まない)。query は title/url 部分一致。"""

    @abstractmethod
    def count(self, query: str | None, category: str | None) -> int:
        """list_summaries と同じ絞り込み条件での総件数。"""

    @abstractmethod
    def list_categories(self) -> list[str]:
        """保存済みドキュメントに付いているカテゴリの一覧(重複なし)。"""


class NoteRepository(ABC):
    @abstractmethod
    def add(self, note: StickyNote) -> StickyNote:
        ...

    @abstractmethod
    def get(self, note_id: int) -> StickyNote | None:
        ...

    @abstractmethod
    def list_for_document(self, document_id: int) -> list[StickyNote]:
        ...

    @abstractmethod
    def update(self, note: StickyNote) -> StickyNote:
        ...

    @abstractmethod
    def delete(self, note_id: int) -> None:
        ...
