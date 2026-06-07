# マーカー

時間がない中で長文の WEB 記事 / 論文を読むためのリーダーです。**要約はしません。** 原文を残したまま、AI が 4 色マーカーで「読む補助線」だけを引きます。

| 色 | 意味 |
| :-: | --- |
| 🔴 赤 | 重要（主張の核） |
| 🟡 黄 | 注意（なぜ?・根拠が薄い・要検証） |
| 🔵 青 | 参照（出典・引用候補） |
| 🟢 緑 | 具体例（事例） |

- URL を貼ると本文を取り込み、文単位に分割して AI が色を付けます。
- ユーザーは正方形の付箋（コメント）を自分で貼れます。
- マーカー部分は色ごとに VOICEVOX で音声再生できます。

---

## 技術スタック

- **バックエンド**: FastAPI / SQLAlchemy / Pydantic / httpx / BeautifulSoup4
- **AI（注釈）**: Ollama（既定 `phi4`）または Gemini Flash を切り替え可能
- **音声**: VOICEVOX Engine
- **フロント**: React + Vite + TypeScript
- **DB**: PostgreSQL（本番） / SQLite（ローカル・テスト）
- **実行環境**: Docker Compose

## ディレクトリ構成

依存方向は `domain → repositories → services → api`。

```
backend/
  app/
    domain/        純粋なエンティティ（外部依存ゼロ）
    repositories/  永続化の抽象 + SQLAlchemy 実装
    services/      scraper / segmenter / annotator / tts ほか（抽象 + 具象）
    api/           薄い router と DI（deps.py）
    main.py        create_app / FastAPI 本体
  tests/           pytest（外部 I/O はフェイク注入、DB は SQLite in-memory）
frontend/
  src/
    pages/         LibraryPage（一覧） / ReaderPage（リーダー）
    reader/        リーダー UI（マーカー設定・付箋・音声プレイヤー）
    components/     HighlightedText / StickyNote
    api/client.ts  バックエンド API クライアント
docker-compose.yml
```

---

## セットアップ（Docker Compose 推奨）

### 1. 前提

- Docker / Docker Compose
- AI に **Ollama を使う場合**: ホストに [Ollama](https://ollama.com/) を入れ、モデルを取得しておく
  ```bash
  ollama pull phi4
  ```
- AI に **Gemini を使う場合**: [API キー](https://aistudio.google.com/app/apikey)を取得

### 2. 環境変数

```bash
cp .env.example .env
# Gemini を使う場合は GEMINI_API_KEY を記入
```

### 3. 起動

```bash
docker compose up --build
```

| サービス | URL |
| --- | --- |
| フロント | http://localhost:5173 |
| バックエンド API | http://localhost:8000 （Swagger: `/docs`） |
| VOICEVOX | http://localhost:50021 |

> AI プロバイダの既定は **Ollama**。Gemini に切り替えるには起動時に `LLM_PROVIDER=gemini` を渡します。
> ```bash
> LLM_PROVIDER=gemini docker compose up --build
> ```

---

## 使い方

1. フロント（http://localhost:5173）を開く。
2. 記事の URL を貼って「解析する」。本文の取り込みと分割はすぐ終わり、AI による色付けはバックグラウンドで進みます。
3. リーダー画面で 4 色マーカーが引かれた原文を読む。
4. 気になる箇所に正方形の付箋（コメント）を貼る。
5. 色ごとのマーカー部分を VOICEVOX で音声再生する。

---

## 主な API

| メソッド | パス | 用途 |
| --- | --- | --- |
| GET | `/health` | ヘルスチェック |
| POST | `/documents` | URL を取り込み（202、ジョブ開始） |
| GET | `/documents/progress/{job_id}` | 注釈ジョブの進捗 |
| GET | `/documents` | ドキュメント一覧（ページング） |
| GET | `/documents/{document_id}` | ドキュメント取得 |
| DELETE | `/documents/{document_id}` | ドキュメント削除 |
| GET | `/categories` | カテゴリ一覧 |
| POST | `/documents/{document_id}/notes` | 付箋の作成 |
| GET | `/documents/{document_id}/notes` | 付箋の取得 |
| PATCH | `/notes/{note_id}` | 付箋の更新 |
| DELETE | `/notes/{note_id}` | 付箋の削除 |
| GET | `/documents/{document_id}/tts` | マーカーの音声合成 |

詳細・スキーマは起動後の Swagger UI（http://localhost:8000/docs）を参照。

---

## ローカル開発（Docker を使わない場合）

### バックエンド

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

既定の DB は SQLite（`marker.db`）。VOICEVOX / Ollama はそれぞれ別途起動が必要です。

### フロント

```bash
cd frontend
npm install
npm run dev
```

---

## テスト

TDD（Red → Green → Refactor）を必須としています。外部 I/O はフェイク実装を注入し、DB は SQLite in-memory を使います。

```bash
# バックエンド
docker compose exec backend pytest
# または
cd backend && pytest

# フロント
docker compose exec frontend npm test
# または
cd frontend && npm test
```

---

## 環境変数一覧

| 変数 | 既定値 | 説明 |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./marker.db` | DB 接続先（Compose では PostgreSQL を注入） |
| `LLM_PROVIDER` | `ollama` | 注釈に使う AI：`ollama` / `gemini` |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Ollama のエンドポイント |
| `OLLAMA_MODEL` | `phi4` | 使用する Ollama モデル |
| `GEMINI_API_KEY` | （空） | Gemini 利用時のみ必須 |
| `GEMINI_MODEL` | `gemini-flash-latest` | 使用する Gemini モデル |
| `VOICEVOX_URL` | `http://voicevox:50021` | VOICEVOX Engine のエンドポイント |

`.env`（秘密情報）はコミットしないでください。テンプレートは `.env.example`。

---

## 設計メモ

- マーカー → 本文のマッピングは **文単位の採番（segment_id）** で行い、文字オフセットや AI の引用文字列には依存しません。
- 外部 I/O（AI / HTTP / VOICEVOX / DB）はすべて抽象（ABC）越しに呼び、具象は FastAPI の `Depends` で注入します（DIP）。
- 開発規約の詳細は [`CLAUDE.md`](./CLAUDE.md) を参照。
