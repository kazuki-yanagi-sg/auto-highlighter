"""本文を文単位に分割し、連番(order)を振る純粋関数。

文字オフセットに依存せず order だけでマーカー/付箋を紐づけるため、
分割ロジックはここに一元化する(SRP)。
"""

from __future__ import annotations

import re

from app.domain.models import Segment

# 「意味のある」文字 = 数字・英字・ひらがな・カタカナ・漢字・全角英数。
# これを1つも含まない断片(空白や記号のみ)は1セグメントとして扱わない。
_MEANINGFUL = re.compile(
    r"[0-9A-Za-z぀-ヿ㐀-鿿０-９Ａ-ｚｦ-ﾟ]"
)


def segment_text(raw: str) -> list[Segment]:
    if not raw:
        return []

    segments: list[Segment] = []
    order = 0
    for fragment in _iter_fragments(raw):
        cleaned = fragment.strip()
        if not cleaned:
            continue
        if not _MEANINGFUL.search(cleaned):
            continue
        segments.append(Segment(order=order, text=cleaned))
        order += 1
    return segments


def _iter_fragments(raw: str):
    """改行で行に分け、各行を句点(。)の直後で文に分割して列挙する。"""
    for line in raw.split("\n"):
        # 「。」を残したまま、その直後で分割する
        yield from re.split(r"(?<=。)", line)


def _sentences(text: str) -> list[str]:
    out: list[str] = []
    for fragment in _iter_fragments(text):
        cleaned = fragment.strip()
        if cleaned and _MEANINGFUL.search(cleaned):
            out.append(cleaned)
    return out


def segment_blocks(blocks, max_per_page: int = 80) -> list["Segment"]:
    """ブロック列を文に分割し、見出しでページを区切って採番する。

    - 見出しブロックに来たら(先頭以外は)新しいページにする。
    - 見出しが無い/ページが長すぎる場合は max_per_page 文で安全に区切る。
    """
    segments: list[Segment] = []
    order = 0
    page = 0
    on_page = 0  # 現ページに積んだ文数
    block_id = 0  # 入力ブロックごとに採番(同段落の文をまとめる識別子)
    has_content = False
    for block in blocks:
        kind = getattr(block, "kind", "text")
        if kind == "heading" and has_content:
            page += 1
            on_page = 0
        # コードは文分割せず、改行・字下げを保ったまま1セグメントにする。
        if kind == "code":
            if on_page >= max_per_page:
                page += 1
                on_page = 0
            segments.append(
                Segment(
                    order=order,
                    text=block.text,
                    page=page,
                    block=block_id,
                    kind="code",
                )
            )
            order += 1
            on_page += 1
            has_content = True
            block_id += 1
            continue
        for sentence in _sentences(block.text):
            if on_page >= max_per_page:
                page += 1
                on_page = 0
            segments.append(
                Segment(order=order, text=sentence, page=page, block=block_id)
            )
            order += 1
            on_page += 1
            has_content = True
        block_id += 1
    return segments
