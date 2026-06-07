"""記事を1つのカテゴリに自動分類する Categorizer。

- Categorizer(ABC): classify() で検証＋フォールバックを共通化(テンプレートメソッド)。
  実装は _suggest() で生のカテゴリ文字列を返すだけ(OCP)。
- GeminiCategorizer: Gemini Flash で分類する具象。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from app.domain.models import Segment

# 一覧フィルタで使う固定カテゴリ集合。LLMにもこの中から選ばせる。
ALLOWED_CATEGORIES = [
    "技術",
    "科学",
    "ビジネス",
    "ニュース",
    "教育",
    "健康",
    "エンタメ",
    "その他",
]
FALLBACK_CATEGORY = "その他"

# 分類に使う本文の先頭文字数(長文全部は送らない)。
_SAMPLE_CHARS = 1500


class Categorizer(ABC):
    @abstractmethod
    def _suggest(self, title: str, segments: list[Segment]) -> str | None:
        """生のカテゴリ文字列を返す(検証前)。"""

    def classify(self, title: str, segments: list[Segment]) -> str:
        raw = (self._suggest(title, segments) or "").strip()
        return raw if raw in ALLOWED_CATEGORIES else FALLBACK_CATEGORY


_PROMPT = """次の記事を、下記カテゴリのちょうど1つに分類してください。
カテゴリ: {categories}
必ずこの中の語をそのまま使うこと。出力はJSONのみ: {{"category": "<カテゴリ>"}}

タイトル: {title}
本文(冒頭):
{body}
"""


class PromptCategorizer(Categorizer):
    """プロンプト生成・JSON解析・失敗フォールバックを共通化した基底。具象は _call_model のみ。"""

    def _suggest(self, title: str, segments: list[Segment]) -> str | None:
        body = "\n".join(s.text for s in segments)[:_SAMPLE_CHARS]
        prompt = _PROMPT.format(
            categories=" / ".join(ALLOWED_CATEGORIES), title=title, body=body
        )
        try:
            return self._parse(self._call_model(prompt))
        except Exception:
            # 分類は副次機能。失敗しても classify 側で「その他」にフォールバックする。
            return None

    @abstractmethod
    def _call_model(self, prompt: str) -> str:
        ...

    @staticmethod
    def _parse(text: str) -> str | None:
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None
        if isinstance(data, dict):
            value = data.get("category")
            return value if isinstance(value, str) else None
        return None


class GeminiCategorizer(PromptCategorizer):
    def __init__(self, api_key: str, model: str = "gemini-flash-latest"):
        self._api_key = api_key
        self._model_name = model

    def _call_model(self, prompt: str) -> str:
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(self._model_name)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        return response.text


_CATEGORY_SCHEMA = {
    "type": "object",
    "properties": {"category": {"type": "string"}},
    "required": ["category"],
}


class OllamaCategorizer(PromptCategorizer):
    def __init__(self, base_url: str, model: str = "llama3", client=None):
        self._base_url = base_url
        self._model = model
        self._client = client

    def _call_model(self, prompt: str) -> str:
        from app.services.ollama import generate

        return generate(
            self._base_url,
            self._model,
            prompt,
            fmt=_CATEGORY_SCHEMA,
            client=self._client,
        )
