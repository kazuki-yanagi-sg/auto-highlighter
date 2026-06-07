"""P1: 見出し単位でページ採番する segment_blocks のテスト。"""

from app.services.scraper import Block
from app.services.segmenter import segment_blocks


def test_pages_increment_at_headings():
    blocks = [
        Block("heading", "はじめに"),
        Block("text", "導入の文。もう一文。"),
        Block("heading", "本論"),
        Block("text", "本論の文。"),
    ]
    segs = segment_blocks(blocks)
    pages = {s.text: s.page for s in segs}
    assert pages["はじめに"] == 0
    assert pages["導入の文。"] == 0
    assert pages["もう一文。"] == 0
    assert pages["本論"] == 1
    assert pages["本論の文。"] == 1


def test_leading_heading_does_not_create_empty_page():
    blocks = [Block("heading", "タイトル見出し"), Block("text", "最初の文。")]
    segs = segment_blocks(blocks)
    assert all(s.page == 0 for s in segs)


def test_order_is_sequential_across_pages():
    blocks = [
        Block("heading", "A"),
        Block("text", "一。二。"),
        Block("heading", "B"),
        Block("text", "三。"),
    ]
    segs = segment_blocks(blocks)
    assert [s.order for s in segs] == [0, 1, 2, 3, 4]


def test_safety_cap_breaks_long_page_without_headings():
    # 見出し無しで大量の文 → 安全弁でページが複数に分かれる
    blocks = [Block("text", "。".join(f"文{i}" for i in range(200)) + "。")]
    segs = segment_blocks(blocks, max_per_page=80)
    assert max(s.page for s in segs) >= 1
