"""ドメインエンティティ。外部依存を持たない純粋なデータ構造。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Color(str, Enum):
    """マーカーの色と意味。AIへのプロンプトでもこの定義をそのまま使う。"""

    RED = "重要"  # 主張の核・重要
    YELLOW = "注意"  # なぜ?・根拠が薄い・要検証
    BLUE = "参照"  # 出典・引用候補
    GREEN = "具体例"  # 事例・具体例


@dataclass
class Segment:
    """本文を文単位に分割した1単位。order で順序、page で所属ページを表す。"""

    order: int
    text: str
    marker: Color | None = None
    page: int = 0
    id: int | None = None
    document_id: int | None = None


@dataclass
class StickyNote:
    """ユーザーが手動で貼る正方形付箋。紙上の座標(x,y)に置く(segmentへの紐付けは任意)。"""

    body: str
    segment_id: int | None = None
    page: int = 0
    x: float = 0.0
    y: float = 0.0
    w: float = 176.0
    h: float = 150.0
    id: int | None = None
    document_id: int | None = None
    created_at: datetime | None = None


@dataclass
class DocumentSummary:
    """一覧表示用の軽量サマリ(本文 segments を含まない)。"""

    id: int
    url: str
    title: str
    category: str | None
    created_at: datetime | None = None
    # カード表示用の集計。color名(red/yellow/blue/green) -> 件数。
    marker_counts: dict[str, int] = field(default_factory=dict)
    note_count: int = 0


@dataclass
class Document:
    """1つの記事。複数の Segment と StickyNote を持つ。"""

    url: str
    title: str
    category: str | None = None
    id: int | None = None
    created_at: datetime | None = None
    segments: list[Segment] = field(default_factory=list)
    notes: list[StickyNote] = field(default_factory=list)
