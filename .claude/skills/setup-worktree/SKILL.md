---
name: setup-worktree
description: worktree を hash port + 専用 docker stack + main DB コピーで main から完全分離する仕組みのエントリポイント。setup.sh / teardown.sh / lib.sh と connected hooks の全体マップを提供する。worktree setup、worktree 初期化、worktree 環境構築、git worktree add の後始末、worktree port、worktree DB。
user-invocable: true
---

# setup-worktree

## 概要

worktree を main から分離する **port-isolation 機構**の中核 skill。本体ロジックの SoT は 3 ファイル:

| ファイル | 役割 |
|---|---|
| `lib.sh` | port hash 採番 / 3 つの .env 生成 / docker stack / main DB コピーの共通関数 |
| `setup.sh` | worktree の port / .env / docker stack / DB を一括 setup する SoT |
| `teardown.sh` | docker stack down + volume(DB) 削除 (git worktree remove は呼ばない) |
| `test_lib.sh` | `lib.sh` 純粋関数の自己テスト (docker 不要) |

## 機構全体図

```text
.claude/worktrees/<name>/                  ← worktree 本体 (.gitignore 済)
  ├── .env / api/.env / client/.env ← port 書き換えコピー (gitignore)
  └── docker stack: senri-wt-<slug> ← COMPOSE_PROJECT_NAME で container/volume/network 分離

.claude/
├── hooks/
│   ├── worktree-create.sh   → setup-worktree/setup.sh に委譲
│   └── worktree-remove.sh   → setup-worktree/teardown.sh に委譲 (git worktree remove は Claude Code 本体)
├── skills/
│   ├── setup-worktree/      ← ★ 本 skill (setup / teardown / lib の SoT)
│   ├── worktree-dev-up/     ← bun next dev 起動 + auto-login
│   ├── verify-screen/       ← 公式 playwright-cli で動作確認 + HTML レポート
│   └── playwright-cli/      ← Microsoft 公式 (setup 時に npx install、gitignore)
└── settings.json           ← WorktreeCreate / WorktreeRemove hook 登録
```

## 鉄則

- **port は branch slug の SHA-256 hash で deterministic 採番** (同じブランチ = 同じ port)
- **6 万番台に固定** (既存クローン並列が 1/2/4 万番台を使うため衝突回避)。NEXT 60xxx / UVICORN 61xxx / POSTGRES 62xxx / MAILPIT_SMTP 63xxx / MAILPIT_WEB 64xxx
- **worktree の 3 つの .env は port 行のみ書き換えた実ファイル** (skyme と違い symlink ではない。senri は root/api/client で .env の中身が違う)
- **docker stack は `COMPOSE_PROJECT_NAME=senri-wt-<slug>` で完全分離** (container / volume / network が別物)。**DB は volume 分離で自動的に別 DB**
- **DB は main の docker Postgres から pg_dump コピー** → `alembic upgrade heads` でブランチ分を上乗せ (現実に近いデータで始める)
- **docker compose は critical var を shell export してから実行**しろ (`lib.sh::worktree_compose`)。compose の .env 補間機構の曖昧さを排除する
- **pgAdmin は worktree では起動しない** (RAM / build 時間節約。検証に不要)
- **teardown は `senri-wt-` prefix 以外を絶対に down しない** (main / クローン保護)

## 前提

- main の docker stack が起動している (`docker compose ps` で db が healthy)。DB copy 元になる
- worktree は `.claude/worktrees/<name>/` 配下に作る

## setup.sh の使い方

WorktreeCreate hook 経由なら自動。手動 (`git worktree add` 直接ルート) では:

```bash
parent="$(git rev-parse --show-toplevel)"
worktree="$parent/.claude/worktrees/<name>"

git worktree add "$worktree" -b feature/<name> develop
bash "$parent/.claude/skills/setup-worktree/setup.sh" "$worktree"
```

setup.sh が行うこと:

1. branch slug → 6 万番台 port / project 名 (`senri-wt-<slug>`) を採番
2. root / api / client の 3 つの .env を port 書き換えコピーで生成
3. `client/` で `bun install --frozen-lockfile` + `bun run generate-prisma`
4. Microsoft 公式 `@playwright/cli` skill を install + `playwright-cli` を global 導入 (bare コマンド解決のため)
5. worktree 専用 docker stack の db を起動 → healthy 待ち
6. main DB を worktree DB へ pg_dump コピー → `alembic upgrade heads`
7. api / mailpit を起動 → ポート早見表を banner 出力

## teardown.sh の使い方

WorktreeRemove hook 経由なら自動。手動:

```bash
bash "$parent/.claude/skills/setup-worktree/teardown.sh" "$worktree"
```

`docker compose down -v --rmi local` で **その worktree の** container / volume(DB) / network / 自前 build image (api) を削除する。`-p senri-wt-<slug>` 配下のみが対象で、他 worktree / 他 session / main / 共有 base image (postgres 等) には触れない。`git worktree remove` は呼ばない。

## 検証チェックリスト

setup.sh 実行後:

- [ ] `$worktree/.env` の `NEXT_PORT` / `PROJECT_NAME` が 6 万番台 / `senri-wt-<slug>`
- [ ] `$worktree/api/.env` / `$worktree/client/.env` が実ファイルで port 書き換え済
- [ ] `docker ps` に `senri-wt-<slug>-db` / `senri-wt-<slug>-api-1` が listen
- [ ] worktree DB に main のデータがコピーされている (`docker exec senri-wt-<slug>-db psql -c '\dt'`)
- [ ] `curl http://localhost:$UVICORN_PORT/api/v1/...` が応答

teardown.sh 実行後:

- [ ] `docker ps` から `senri-wt-<slug>-*` が消失
- [ ] `docker images` から `senri-wt-<slug>-api` が消失 (共有 base image は残る)
- [ ] main / クローン / 他 worktree の stack は無傷

## 危険信号 - 停止

- `worktree_path` が main repo root を指している → 停止
- branch が `develop` / `main` / 空 → 停止
- main の docker stack が未起動 (DB copy 元が無い) → main で `docker compose up -d` してから再実行
- project 名が `senri-wt-` prefix でない状態で teardown → 停止 (保護)

## アンチパターン

| ❌ NG | ✅ OK |
|---|---|
| port を手で番号指定 | branch slug から deterministic 採番 |
| worktree で `docker compose up` を素で打つ (project 名がディレクトリ名になる) | `lib.sh::worktree_compose` 経由で project 名を明示 |
| main の DB に migration を当てる | worktree の分離 DB に当てる |
| 3 つの .env を 1 つに symlink | senri は中身が違うので 3 つ個別生成 |
| hook の中に全ロジックを書く | hook は契約のみ、ロジックは setup-worktree/ に集約 |

## 連携

- **hook**: `.claude/hooks/worktree-create.sh` / `worktree-remove.sh`
- **後続 skill**: `worktree-dev-up` (bun next dev + auto-login)、`verify-screen` (動作確認 + レポート)
