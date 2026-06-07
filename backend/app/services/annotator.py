"""本文に4色マーカーを付ける Annotator。

- Annotator(ABC): annotate() に「検証して反映」する共通ロジックを置く(テンプレートメソッド)。
  実装は _suggest() で生のアノテーション([{segment_id, color, reason}])を返すだけでよい(OCP)。
- GeminiAnnotator: Gemini Flash を呼ぶ具象。要約はせず、該当文に色を付けるだけ。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from app.domain.models import Color, Segment

# LLM が返す色文字列 → ドメインの Color。これ以外は無視する。
_COLOR_MAP = {
    "red": Color.RED,
    "yellow": Color.YELLOW,
    "blue": Color.BLUE,
    "green": Color.GREEN,
}


class AiError(Exception):
    """AI(Gemini)呼び出しに失敗したことを表す(クォータ超過・レート制限・通信失敗など)。"""


def _extract_marks(data: object) -> list:
    """LLM応答からマーク配列を取り出す。配列/オブジェクト/単一マークのどれでも対応。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # {"marks": [...]} 等、最初に見つかった配列を使う
        for value in data.values():
            if isinstance(value, list):
                return value
        # 単一マークオブジェクト {"segment_id":..,"color":..} の場合
        if "color" in data and "segment_id" in data:
            return [data]
    return []


def _parse_color(value: object) -> Color | None:
    if not isinstance(value, str):
        return None
    return _COLOR_MAP.get(value.strip().lower())


class Annotator(ABC):
    @abstractmethod
    def _suggest(self, segments: list[Segment]) -> list[dict]:
        """[{"segment_id": int, "color": str, "reason": str}] の生データを返す。"""

    def annotate(self, segments: list[Segment]) -> list[Segment]:
        by_order = {s.order: s for s in segments}
        for raw in self._suggest(segments):
            color = _parse_color(raw.get("color"))
            if color is None:
                continue
            segment = by_order.get(raw.get("segment_id"))
            if segment is None:
                continue
            segment.marker = color
        return segments


_PROMPT_HEADER = """あなたはハイライト係です。各文(行頭に番号)を読み、下の4種に当てはまる文だけ色を付けます。
当てはまらない説明文は飛ばします。要約はしません。

【色を付ける(該当したら必ず付ける)】
- red    = 主張の核: 段落の結論・定義・最も言いたい主張(段落につき多くて1〜2)
- green  = 具体例: 「例えば」「具体的には」など、事例・代表例・数値で示す文(否定的な内容でも例示なら green)
- blue   = 参照: 出典・文献・引用元(著者名・論文名・年・教科書・URL)を示す文
- yellow = 注意: 危険・批判・問題点・「根拠が弱い/未解明/議論がある」と述べる文(「例えば」で始まる例示は green を優先)

【色を付けない(飛ばす)】
仕組み・手順・計算方法の説明、言い換え・補足、歴史や経緯、つなぎ・案内(「次節では」)、雑談。
「重要そう」なだけの説明文や繰り返しには付けない。

例(12文。説明・経緯・案内は飛ばす):
入力:
0: 教師あり学習は入力と正解の組からモデルを学ぶ手法である。
1: モデルは予測と正解の誤差が小さくなるよう更新される。
2: 誤差の指標には平均二乗誤差などがある。
3: 例えば住宅価格の予測では、面積や築年数から価格を学ぶ。
4: 過学習が起きると未知データでの精度が落ちるという大きな問題がある。
5: これを防ぐために正則化や交差検証が用いられる。
6: ただし正則化の強さの調整は経験に頼る面があり難しいという課題がある。
7: この枠組みは Vapnik らの統計的学習理論で基礎づけられている。
8: 例えば、学習率が大きすぎると学習が発散してしまう。
9: 歴史的には1990年代に広く使われた。
10: なお、深層学習との優劣は問題設定により議論がある。
11: 次節では教師なし学習を扱う。
出力:
{"marks":[{"segment_id":0,"color":"red"},{"segment_id":3,"color":"green"},{"segment_id":4,"color":"red"},{"segment_id":6,"color":"yellow"},{"segment_id":7,"color":"blue"},{"segment_id":8,"color":"green"},{"segment_id":10,"color":"yellow"}]}
(1,2,5 は説明、9 は経緯、11 は案内なので飛ばす)

同じ形式の JSON {"marks":[{"segment_id":<番号>,"color":"red|yellow|blue|green"}]} のみ出力。
文章:
"""


class PromptAnnotator(Annotator):
    """プロンプト生成・JSON解析・失敗ハンドリングを共通化した基底。

    具象は LLM を呼ぶ `_call_model` だけ実装すればよい(OCP)。
    """

    def _suggest(self, segments: list[Segment]) -> list[dict]:
        if not segments:
            return []
        try:
            text = self._call_model(self._build_prompt(segments))
        except Exception as exc:  # クォータ/レート/通信失敗などを 500 にしない
            raise AiError("AIの解析に失敗しました(混雑/上限の可能性)") from exc
        return self._parse(text)

    def _build_prompt(self, segments: list[Segment]) -> str:
        lines = [f"{s.order}: {s.text}" for s in segments]
        return _PROMPT_HEADER + "\n".join(lines)

    @abstractmethod
    def _call_model(self, prompt: str) -> str:
        """プロンプトをLLMに渡し、JSON文字列を返す。"""

    @staticmethod
    def _parse(text: str) -> list[dict]:
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return []
        items = _extract_marks(data)
        return [item for item in items if isinstance(item, dict)]


class GeminiAnnotator(PromptAnnotator):
    def __init__(self, api_key: str, model: str = "gemini-flash-latest"):
        self._api_key = api_key
        self._model_name = model

    def _call_model(self, prompt: str) -> str:
        # google-generativeai はここでだけ使う(テスト時は import 不要)。
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(self._model_name)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        return response.text


# Ollama に渡す構造強制スキーマ(配列を確実に返させ、単一オブジェクト化を防ぐ)。
_MARKS_SCHEMA = {
    "type": "object",
    "properties": {
        "marks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "segment_id": {"type": "integer"},
                    "color": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["segment_id", "color"],
            },
        }
    },
    "required": ["marks"],
}


class OllamaAnnotator(PromptAnnotator):
    def __init__(self, base_url: str, model: str = "llama3", client=None):
        self._base_url = base_url
        self._model = model
        self._client = client

    def _call_model(self, prompt: str) -> str:
        from app.services.ollama import generate

        return generate(
            self._base_url, self._model, prompt, fmt=_MARKS_SCHEMA, client=self._client
        )
