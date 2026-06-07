# CLAUDE.md — 速読支援アプリ 開発規約

このリポジトリで作業するすべてのエージェント / 開発者が従う規約。

## プロダクト概要
時間がない中で長文のWEB記事/論文を読むためのツール。**要約はしない**。原文を残したまま、AIが4色マーカーで「読む補助線」だけを引く。

- 🔴 赤 = 重要（主張の核）
- 🟡 黄 = 注意（なぜ?・根拠が薄い・要検証）
- 🔵 青 = 参照（出典・引用候補）
- 🟢 緑 = 具体例（事例）

ユーザーは正方形付箋（コメント）を **自分で** 貼る。マーカー部分は色ごとにVOICEVOXで音声再生できる。

## 応答
- ユーザーへの応答は **日本語**。

## 開発フロー（厳守）
1. **planningを必ず行う**。非自明なタスクはplan modeで計画→承認を得てから着手。
2. **TDD必須**。実装前に必ず失敗するテストを書く（Red → Green → Refactor）。テストを後回しにしない。
3. **ネストを浅く保つ**。早期return・ガード節を使い、3段以上のネストは原則禁止。
4. **SOLID原則に従う**。

## SOLIDの適用方針
- **SRP**: 1クラス/1モジュール1責務。スクレイピング・解析・TTS・永続化は別々のサービスに分ける。
- **OCP**: 新しいScraper/Annotator/TTS実装は既存コードを変えずに「追加」で対応（ABCを継承）。
- **LSP**: 同一インターフェースの実装は差し替え可能に保つ（フェイク実装でテスト）。
- **ISP**: リポジトリ/サービスのインターフェースは用途ごとに小さく。
- **DIP**: routerやサービスは **抽象（ABC）に依存** し、具象はFastAPIの`Depends`で注入する。外部I/O（Gemini / HTTP / VOICEVOX / DB）は必ず抽象越しに呼ぶ。

## アーキテクチャ（依存方向）
```
domain → repositories → services → api
```
- `domain/`     : 純粋なエンティティ。外部依存ゼロ。
- `repositories/`: 永続化の抽象 + SQLAlchemy実装。
- `services/`   : scraper / segmenter / annotator / tts。abstract + 具象。
- `api/`        : 薄いrouter。`deps.py`でDI。

マーカー→本文のマッピングは **文単位に採番（segment_id）** して行う。文字オフセットやAIの引用文字列に依存しない。

## 技術スタック
- バックエンド: FastAPI / SQLAlchemy / Pydantic / httpx / BeautifulSoup4 / google-generativeai
- AI: Gemini Flash（`response_mime_type=application/json` でJSON強制）
- 音声: VOICEVOX Engine（docker-compose内サービス）
- フロント: React + Vite + TypeScript
- DB: PostgreSQL（本番） / SQLite in-memory（テスト）
- 実行環境: docker-compose

## テスト
- backend: `pytest`。外部I/Oはフェイク実装を注入。DBはSQLite in-memory。
  - 実行: `docker compose exec backend pytest` または `cd backend && pytest`
- frontend: `Vitest` + `@testing-library/react` + `msw`（APIモック）。
  - 実行: `docker compose exec frontend npm test` または `cd frontend && npm test`

## 秘密情報
- `GEMINI_API_KEY` などは `.env` に置きコミットしない（`.env.example` をテンプレとして用意）。
