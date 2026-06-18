"""URL → スクレイピング → 文分割 → (保存) → 注釈/分類 を束ねるユースケース。

UX向上のため2段階に分ける:
- prepare_from_url: scrape+分割して即保存(LLMを呼ばない=速い)。本文をすぐ開ける。
- annotate_document: 保存済みドキュメントをバッチ注釈し、各バッチ後にDBへ反映＋進捗通知。

依存(scraper/annotator/categorizer/repository)はすべて抽象で受け取る(DIP)。
"""

from __future__ import annotations

from collections.abc import Callable

from app.domain.models import Document
from app.repositories.interfaces import DocumentRepository
from app.services.annotator import Annotator
from app.services.categorizer import Categorizer
from app.services.scraper import Block, Scraper
from app.services.segmenter import segment_blocks

# 1回の注釈で LLM に渡すセグメント数。小さめにすると1回が速く落ちにくく、色がこまめに付く
# (phi4 は40文で約95秒。20文なら約半分で、タイムアウトや待ち時間を抑えられる)。
ANNOTATE_BATCH = 20

# progress(done_batches, total_batches, markers: order->color名)
ProgressFn = Callable[[int, int, dict[int, str]], None]


class DocumentService:
    def __init__(
        self,
        scraper: Scraper | None,
        annotator: Annotator,
        categorizer: Categorizer,
        repository: DocumentRepository,
    ):
        self._scraper = scraper
        self._annotator = annotator
        self._categorizer = categorizer
        self._repository = repository

    def prepare_from_url(self, url: str) -> Document:
        """scrape+分割して即保存(マーカー/カテゴリ無し)。"""
        content = self._scraper.fetch(url)
        blocks = content.blocks or [Block(kind="text", text=content.text)]
        segments = segment_blocks(blocks)
        document = Document(url=url, title=content.title, category=None, segments=segments)
        return self._repository.add(document)

    def annotate_document(
        self, document: Document, progress: ProgressFn | None = None
    ) -> None:
        """バッチ注釈→各バッチ後にDB反映＋進捗通知。最後にカテゴリ分類。"""
        # コードブロックはマーカー対象外(地の文だけを注釈する)。
        segments = [s for s in document.segments if s.kind != "code"]
        total = max(1, (len(segments) + ANNOTATE_BATCH - 1) // ANNOTATE_BATCH)
        accumulated: dict[int, str] = {}
        if progress:
            progress(0, total, dict(accumulated))

        done = 0
        for start in range(0, len(segments), ANNOTATE_BATCH):
            batch = segments[start : start + ANNOTATE_BATCH]
            self._annotator.annotate(batch)
            marked = {s.order: s.marker for s in batch if s.marker is not None}
            self._repository.apply_markers(document.id, marked)
            accumulated.update({o: c.name.lower() for o, c in marked.items()})
            done += 1
            if progress:
                progress(done, total, dict(accumulated))

        category = self._categorizer.classify(document.title, segments)
        self._repository.set_category(document.id, category)

    def get(self, document_id: int) -> Document | None:
        return self._repository.get(document_id)
