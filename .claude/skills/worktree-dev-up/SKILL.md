---
name: worktree-dev-up
description: worktree 内で docker stack (BE/DB/mailpit) を確認起動し frontend (next dev) を local bun で立ち上げる。動作確認 (verify-screen) の前段。Mock 認証 auto-login も提供。worktree dev 起動、worktree server 起動、next dev 起動、worktree 動作確認準備、auto-login。
user-invocable: true
---

# worktree-dev-up

## 概要

worktree の `.env` から `NEXT_PORT` / `UVICORN_PORT` を読み、

1. docker stack (db / api / mailpit) を idempotent に起動 (setup 済なら no-op)
2. API `/healthcheck` が 200 を返すまで wait
3. next dev を local bun で background 起動 (`--port` は worktree の NEXT_PORT)
4. frontend `/` が 200 を返すまで wait
5. 起動 URL を stdout に出力

senri は **BE/DB が docker、FE が local bun**。BE の lifecycle は `setup-worktree` が持つので、本 skill は「念のため up -d」+ FE 起動 + auto-login に専念する。

## 鉄則

- **FE port は worktree の `NEXT_PORT` を `--port` で明示**しろ。`next dev` は `-p` 無しだと 3000 に落ちる
- **docker は `lib.sh::worktree_compose` 経由**で起動しろ (project 名を明示し main / クローンを誤操作しない)
- **API health は `/healthcheck`** (senri は `/api/v1/health` ではない)
- **worktree から素の `docker compose up` を打つな** (project 名がディレクトリ名になり分離が崩れる)

## 前提

- `setup-worktree` skill 完了済み (worktree の .env / docker stack / DB が揃っている)

## 手順

```bash
parent="$(git rev-parse --show-toplevel)"
bash "$parent/.claude/skills/worktree-dev-up/up.sh" "$worktree"
```

## Mock Auth auto-login (playwright-cli で protected page に 1 発で入る)

senri は fastapi-users の **Bearer token 方式**。login 成功時サーバは Cookie を Set せず JSON で
`access_token` を返すだけ。frontend は 非HttpOnly cookie `accessToken` に保存し、Server Component の
auth-check が request の `accessToken` cookie を読む。

`auto-login.sh` は `POST /api/v1/auth/login` (form) を叩いて `access_token` を取り echo する。
playwright で **同 origin の任意ページを開いて `document.cookie` に注入 → protected page へ navigate**
すれば 1 発で入れる (skyme の `/auth/callback` 中継は senri に無い)。

```bash
token=$(bash "$parent/.claude/skills/worktree-dev-up/auto-login.sh" "$worktree" | sed 's/^ACCESS_TOKEN=//')
client_port=$(grep '^NEXT_PORT=' "$worktree/.env" | cut -d= -f2)
session="verify-$(basename "$worktree")"   # worktree ごとに一意 (session はマシン全体で名前管理)
playwright-cli -s=$session open "http://localhost:$client_port/login"
playwright-cli -s=$session eval "document.cookie='accessToken=$token; path=/'"
playwright-cli -s=$session goto "http://localhost:$client_port/home"   # → 認証済みで着地 (ロール別 landing)
```

- 第 2 引数で email、第 3 引数で password を指定できる (省略時 `admin0@example.com` / `Password1@`)
- token は短命なので navigate 直前に発行しろ

## 停止方法

```bash
bash "$parent/.claude/skills/worktree-dev-up/down.sh" "$worktree"
```

- next dev を PID / port 経由で停止する
- **docker stack (BE/DB) は止めない**。DB ごと消すなら `setup-worktree/teardown.sh` を使え

## 検証チェックリスト

- [ ] `curl http://localhost:$UVICORN_PORT/healthcheck` が `{"status":"ok"}`
- [ ] `curl http://localhost:$NEXT_PORT/` が 200 (Next.js の HTML)
- [ ] `lsof -i :$NEXT_PORT` で node (next dev) が listen
- [ ] `docker ps` に `senri-wt-<slug>-api-1` / `-db` が listen

## アンチパターン

| ❌ NG | ✅ OK |
|---|---|
| `bun run dev` を port 指定なしで起動 (3000 に落ちる) | `bun run dev -- --port $NEXT_PORT` |
| `http://localhost:13100` をハードコード | `.env` の `$NEXT_PORT` / `$UVICORN_PORT` を読む |
| 素の `docker compose up` | `worktree_compose` 経由 |
| login dialog を click して遷移待ち (loop 誤判定) | `auto-login.sh` で token 取得 → cookie 注入 |

## 連携

- 前段: `setup-worktree` (.env / docker stack / DB)
- 後続: `verify-screen` (公式 playwright-cli で UI 確認 + レポート)
