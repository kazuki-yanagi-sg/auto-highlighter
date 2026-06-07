"""Ollama 版の注釈/分類のテスト。Ollamaサーバは httpx.MockTransport で差し替える。"""

import httpx
import pytest

from app.domain.models import Color, Segment
from app.services.annotator import AiError, OllamaAnnotator
from app.services.categorizer import FALLBACK_CATEGORY, OllamaCategorizer


def _client(response_text: str, status: int = 200) -> httpx.Client:
    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.path == "/api/generate"
        return httpx.Response(status, json={"response": response_text})

    return httpx.Client(transport=httpx.MockTransport(handler))


def _segments():
    return [
        Segment(order=0, text="重要な主張。"),
        Segment(order=1, text="ただの説明。"),
    ]


def test_ollama_annotator_applies_markers_from_object_form():
    # llama3 は {"marks":[...]} のオブジェクト形式で返す
    client = _client('{"marks": [{"segment_id": 0, "color": "red"}]}')
    annotator = OllamaAnnotator("http://ollama:11434", "llama3", client=client)
    result = annotator.annotate(_segments())
    assert result[0].marker is Color.RED
    assert result[1].marker is None


def test_ollama_annotator_accepts_plain_array():
    client = _client('[{"segment_id": 1, "color": "blue"}]')
    annotator = OllamaAnnotator("http://ollama:11434", "llama3", client=client)
    result = annotator.annotate(_segments())
    assert result[1].marker is Color.BLUE


def test_ollama_annotator_accepts_single_object():
    # スキーマ無しで単一オブジェクトを返すケースも拾う
    client = _client('{"segment_id": 0, "color": "green"}')
    annotator = OllamaAnnotator("http://ollama:11434", "llama3", client=client)
    result = annotator.annotate(_segments())
    assert result[0].marker is Color.GREEN


def test_ollama_annotator_http_error_raises_aierror():
    client = _client("", status=500)
    annotator = OllamaAnnotator("http://ollama:11434", "llama3", client=client)
    with pytest.raises(AiError):
        annotator.annotate(_segments())


def test_ollama_categorizer_classifies():
    client = _client('{"category": "技術"}')
    cat = OllamaCategorizer("http://ollama:11434", "llama3", client=client)
    assert cat.classify("タイトル", _segments()) == "技術"


def test_ollama_categorizer_falls_back_on_error():
    client = _client("", status=500)
    cat = OllamaCategorizer("http://ollama:11434", "llama3", client=client)
    assert cat.classify("タイトル", _segments()) == FALLBACK_CATEGORY
