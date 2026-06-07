"""P3: Categorizer のテスト。

LLM呼び出しは _suggest に隔離し、検証/フォールバックは共通の classify に持たせる(DIP/テンプレートメソッド)。
許可カテゴリ外や失敗は「その他」にフォールバックする。
"""

from app.domain.models import Segment
from app.services.categorizer import ALLOWED_CATEGORIES, FALLBACK_CATEGORY, Categorizer


class FakeCategorizer(Categorizer):
    def __init__(self, raw):
        self._raw = raw

    def _suggest(self, title, segments):
        return self._raw


_SEGMENTS = [Segment(order=0, text="本文。")]


def test_valid_category_passes_through():
    cat = FakeCategorizer("技術").classify("タイトル", _SEGMENTS)
    assert cat == "技術"
    assert "技術" in ALLOWED_CATEGORIES


def test_unknown_category_falls_back():
    assert FakeCategorizer("宇宙人").classify("t", _SEGMENTS) == FALLBACK_CATEGORY


def test_whitespace_is_trimmed():
    assert FakeCategorizer("  科学 ").classify("t", _SEGMENTS) == "科学"


def test_empty_or_none_falls_back():
    assert FakeCategorizer("").classify("t", _SEGMENTS) == FALLBACK_CATEGORY
    assert FakeCategorizer(None).classify("t", _SEGMENTS) == FALLBACK_CATEGORY


def test_gemini_categorizer_falls_back_on_api_error():
    """分類のGemini呼び出しが失敗しても「その他」にフォールバックする。"""
    from app.services.categorizer import FALLBACK_CATEGORY, GeminiCategorizer

    class Boom(GeminiCategorizer):
        def _call_model(self, prompt):
            raise RuntimeError("429 quota")

    assert Boom("key").classify("t", [Segment(order=0, text="本文。")]) == FALLBACK_CATEGORY
