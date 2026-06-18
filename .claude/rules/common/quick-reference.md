# プロジェクト固有コマンド クイックリファレンス

## 全体チェック

```bash
sh project_check.sh -h               # ヘルプ
sh project_check.sh -s               # client / api 完全再構築
sh project_check.sh -e               # .env を .env.sample から同期（cp 禁止）
```

## Frontend (Client / bun) — local 実行必須（Docker 禁止）

```bash
# Lint / 生成
sh project_check.sh -cl              # biome fix + typecheck
sh project_check.sh -cg              # OpenAPI 型生成 + Prisma 型生成 + fix
sh project_check.sh -cr              # node_modules 再構築

# 開発
cd client && bun run dev             # 開発サーバー（port は .env の NEXT_PORT）
cd client && bun run typecheck       # 型チェック
cd client && bun run fix             # biome --write
cd client && bun run test            # vitest
cd client && bun run test:e2e        # playwright
cd client && bun run build           # プロダクションビルド
```

## Backend (API / Python uv) — 必ず `uv run` 経由

```bash
# Lint / Test
sh project_check.sh -al              # black + pyright + ruff fix
cd api && uv run pytest -v           # test（local 推奨）
sh project_check.sh -atest           # test（同上を project_check 経由で）
sh project_check.sh -acheck          # alembic autogenerate ドリフト検査

# DB（実行前にユーザー承認必須）
sh project_check.sh -ad              # DB 初期化 + Seed
sh project_check.sh -aa              # alembic 初期化
sh project_check.sh -ar              # api 一括初期化（venv 再構築 + Docker rebuild）
sh project_check.sh -ap              # api pip セットアップ

# 翻訳
sh project_check.sh -at              # 翻訳ファイル抽出と更新

# DB 操作（個別）
docker compose exec -T api uv run alembic revision --autogenerate -m "message"
docker compose exec -T api uv run alembic upgrade head
```

## Docker 操作

プロジェクトルートから実行。`.env` 変更後は `down && up -d` 必須。

```bash
docker compose up -d                 # 全サービス起動
docker compose down                  # 停止
docker compose logs -f api           # API ログ
docker compose down -v               # ボリューム含む完全削除
docker compose build --no-cache      # キャッシュなしビルド
```

## 環境

- **Client (bun)**: 必ず local 実行（Docker 禁止）
- **Python**: 必ず `uv run` 経由（直接 `pytest` / `mypy` / `ruff` 禁止）
- **Docker Compose**: プロジェクトルートから実行
- **ポート番号**: 人によって異なるため必ず `.env` を確認（`NEXT_PORT` / `UVICORN_PORT` / `POSTGRES_PORT` 等）

## DB 変更手順

詳細は `database-operations` skill 参照。概要のみ:

1. `client/prisma/schema.prisma` を編集
2. `cd client && bunx prisma format && bun run generate-prisma`
3. `api/src/<domain>/models.py` を更新（SQLModel 側）
4. `docker compose exec -T api uv run alembic revision --autogenerate -m "..."`
5. `docker compose exec -T api uv run alembic upgrade head`

## 開発用認証情報

| 役割 | メール | パスワード |
|---|---|---|
| Admin | `admin0@example.com` | `Password1@` |
| Member | `member1@example.com` | `Password1@` |

## AWS（読み取り専用調査）

- AWS CLI プロファイル: `senri-core-system`
- ECS Exec: `./api/scripts/ecs/exec.sh -e {development|preview|production}`
- 詳細は `aws-environment-investigation` skill を参照
