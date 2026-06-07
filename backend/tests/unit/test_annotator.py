"""ステップ3: Annotator のテスト。

LLM呼び出しは抽象メソッド _suggest に隔離し、テストはフェイクで差し替える(DIP/LSP)。
不正color・範囲外idの除外ロジックは共通の annotate() 側に持たせ、全実装が恩恵を受ける。
"""

from app.domain.models import Color, Segment
from app.services.annotator import Annotator


class FakeAnnotator(Annotator):
    def __init__(self, raw):
        self._raw = raw

    def _suggest(self, segments):
        return self._raw


def _segments():
    return [
        Segment(order=0, text="重要な主張。"),
        Segment(order=1, text="ただの説明。"),
        Segment(order=2, text="例えば〜。"),
    ]


def test_applies_markers_by_segment_id():
    annotator = FakeAnnotator(
        [
            {"segment_id": 0, "color": "red", "reason": "核心"},
            {"segment_id": 2, "color": "green", "reason": "具体例"},
        ]
    )
    result = annotator.annotate(_segments())
    assert [s.marker for s in result] == [Color.RED, None, Color.GREEN]


def test_ignores_invalid_color():
    annotator = FakeAnnotator([{"segment_id": 0, "color": "purple"}])
    result = annotator.annotate(_segments())
    assert all(s.marker is None for s in result)


def test_ignores_out_of_range_segment_id():
    annotator = FakeAnnotator([{"segment_id": 99, "color": "red"}])
    result = annotator.annotate(_segments())  # 例外を出さない
    assert all(s.marker is None for s in result)


def test_color_matching_is_case_insensitive_and_reason_optional():
    annotator = FakeAnnotator([{"segment_id": 1, "color": "YELLOW"}])
    result = annotator.annotate(_segments())
    assert result[1].marker is Color.YELLOW


def test_last_annotation_wins_for_same_segment():
    annotator = FakeAnnotator(
        [
            {"segment_id": 0, "color": "red"},
            {"segment_id": 0, "color": "blue"},
        ]
    )
    result = annotator.annotate(_segments())
    assert result[0].marker is Color.BLUE


def test_gemini_annotator_wraps_api_error_as_aierror():
    """Gemini呼び出しが失敗したら AiError に包んで投げる(500化させない)。"""
    import pytest

    from app.services.annotator import AiError, GeminiAnnotator

    class Boom(GeminiAnnotator):
        def _call_model(self, prompt):
            raise RuntimeError("429 ResourceExhausted quota")

    with pytest.raises(AiError):
        Boom("key").annotate([Segment(order=0, text="本文。")])
