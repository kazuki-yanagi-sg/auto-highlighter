"""ステップ1: 文分割 Segmenter のテスト (Red → Green)。"""

from app.domain.models import Color
from app.services.segmenter import segment_text


def test_splits_on_japanese_period():
    segments = segment_text("これは一文目です。これは二文目です。")
    assert [s.text for s in segments] == ["これは一文目です。", "これは二文目です。"]


def test_assigns_sequential_order_starting_from_zero():
    segments = segment_text("一。二。三。")
    assert [s.order for s in segments] == [0, 1, 2]


def test_splits_on_newlines():
    segments = segment_text("見出し\n本文です。")
    assert [s.text for s in segments] == ["見出し", "本文です。"]


def test_excludes_empty_and_symbol_only_fragments():
    segments = segment_text("本文です。\n\n   \n。。\n次の文。")
    assert [s.text for s in segments] == ["本文です。", "次の文。"]


def test_segments_start_without_marker():
    segments = segment_text("マーカーはまだ無い。")
    assert all(s.marker is None for s in segments)
    # Color enum が import できること(後続ステップで使う)
    assert Color.RED.value == "重要"


def test_empty_input_returns_empty_list():
    assert segment_text("") == []
    assert segment_text("   \n  ") == []
