#!/usr/bin/env bash
# Worktree の dev API で access_token を発行する。
# 公式 playwright-cli で cookie を 1 つ注入するだけで protected page に入れるようにする。
#
# 背景:
#   senri は fastapi-users の Bearer token 方式。ログイン成功時、サーバは Cookie を Set せず
#   JSON で access_token を返すだけ。frontend は js-cookie で 非HttpOnly cookie `accessToken` に
#   手動保存し、axios が Authorization: Bearer で送る。Server Component の auth-check は
#   request の `accessToken` cookie を読んで検証する。
#
#   よって playwright では「login API を叩いて access_token を取得 → 同 origin の任意ページで
#   document.cookie に accessToken をセット → protected page へ navigate」で 1 発で入れる。
#   (skyme の /auth/callback のような中継ページは senri に無い)
#
# 引数:
#   $1 = worktree_path
#   $2 = email?     (省略時 admin0@example.com)
#   $3 = password?  (省略時 Password1@)
#
# 出力 (stdout):
#   ACCESS_TOKEN=<jwt>
#
# 使い方 (playwright-cli):
#   token=$(bash .claude/skills/worktree-dev-up/auto-login.sh "$worktree" | sed 's/^ACCESS_TOKEN=//')
#   client_port=$(grep '^NEXT_PORT=' "$worktree/.env" | cut -d= -f2)
#   playwright-cli goto "http://localhost:$client_port/login"
#   playwright-cli eval "document.cookie='accessToken=$token; path=/'"
#   playwright-cli goto "http://localhost:$client_port/<protected-path>"

set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
source "$script_dir/../setup-worktree/lib.sh"

worktree_path="${1:-}"
email="${2:-admin0@example.com}"
password="${3:-Password1@}"

if [ -z "$worktree_path" ]; then
  echo "usage: $0 <worktree_path> [email] [password]" >&2
  exit 1
fi
worktree_path="$(cd "$worktree_path" && pwd)" || { echo "auto-login: worktree_path が存在しない: $1" >&2; exit 1; }

if [ ! -f "$worktree_path/api/.env" ]; then
  echo "auto-login: $worktree_path/api/.env が無い (setup-worktree を先に実行しろ)" >&2
  exit 1
fi

uvicorn_port="$(read_env_value "$worktree_path/api/.env" UVICORN_PORT)"
if [ -z "$uvicorn_port" ]; then
  echo "auto-login: UVICORN_PORT が .env に無い" >&2
  exit 1
fi

# fastapi-users の login は OAuth2PasswordRequestForm (form-urlencoded, username/password)
response=$(curl -fsS -X POST \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=$email" \
  --data-urlencode "password=$password" \
  "http://localhost:$uvicorn_port/api/v1/auth/login" 2>/dev/null || echo "")

if [ -z "$response" ]; then
  echo "auto-login: POST /api/v1/auth/login 失敗 (dev server 起動済か / 認証情報を確認しろ)" >&2
  exit 1
fi

if command -v jq >/dev/null 2>&1; then
  token=$(printf '%s' "$response" | jq -r '.access_token // empty')
else
  token=$(printf '%s' "$response" | sed -n 's/.*"access_token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
fi

if [ -z "$token" ]; then
  echo "auto-login: response に access_token が無い: $response" >&2
  exit 1
fi

echo "ACCESS_TOKEN=$token"
