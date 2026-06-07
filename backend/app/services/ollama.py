"""ローカル Ollama サーバ呼び出しの共有ヘルパ。

`/api/generate` に format=json で投げ、応答のJSON文字列を返す。
注釈/分類の `_call_model` から使う(client を注入できテスト可能)。
"""

from __future__ import annotations

import httpx


def generate(
    base_url: str,
    model: str,
    prompt: str,
    fmt: object = "json",
    client: httpx.Client | None = None,
) -> str:
    """Ollamaにプロンプトを投げ、応答テキストを返す。

    fmt は "json"(緩い)か、JSONスキーマ(dict)。スキーマを渡すと構造を強制でき、
    配列や複数要素を確実に返させられる(小型モデルの単一オブジェクト化を防ぐ)。
    """
    owns_client = client is None
    # phi4 等の大きめモデルは1バッチ100秒前後かかるため、十分長いタイムアウトにする。
    http = client or httpx.Client(timeout=600.0)
    try:
        response = http.post(
            f"{base_url.rstrip('/')}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": fmt,
                # 抽出タスクは決定的に(ぶれを抑え精度を安定させる)
                "options": {"temperature": 0},
            },
        )
        response.raise_for_status()
        return response.json().get("response", "")
    finally:
        if owns_client:
            http.close()
