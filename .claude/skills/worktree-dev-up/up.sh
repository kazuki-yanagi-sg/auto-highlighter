#!/usr/bin/env bash
# Worktree の docker stack (BE/DB/mailpit) を確認起動し、frontend (next dev) を local bun で起動する。
#
# 引数:
#   $1 = worktree_path  (worktree の絶対 path)
#
# 動作:
#   1. .env から NEXT_PORT / UVICORN_PORT を読む
#   2. docker stack (db api mailpit) を idempotent に起動 (setup 済なら no-op)
#   3. API /healthcheck が 200 を返すまで wait
#   4. next dev を bun で background 起動 (--port は worktree の NEXT_PORT)
#   5. frontend / が 200 を返すまで wait
#   6. 起動 URL を stdout に出力
#
# senri は BE/DB が docker、FE が local bun。BE の lifecycle は setup-worktree が持つので
# ここでは「念のため up -d」+ FE 起動に専念する。

set -uo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
source "$script_dir/../setup-worktree/lib.sh"

worktree_path="${1:-}"
if [ -z "$worktree_path" ]; then
  echo "usage: $0 <worktree_path>" >&2
  exit 1
fi
worktree_path="$(cd "$worktree_path" && pwd)" || { echo "worktree-dev-up: worktree_path が存在しない: $1" >&2; exit 1; }

if [ ! -f "$worktree_path/.env" ]; then
  echo "worktree-dev-up: $worktree_path/.env が無い (setup-worktree を先に実行しろ)" >&2
  exit 1
fi

next_port="$(read_env_value "$worktree_path/.env" NEXT_PORT)"
uvicorn_port="$(read_env_value "$worktree_path/api/.env" UVICORN_PORT)"
if [ -z "$next_port" ] || [ -z "$uvicorn_port" ]; then
  echo "worktree-dev-up: NEXT_PORT / UVICORN_PORT が .env に無い" >&2
  exit 1
fi

mkdir -p "$worktree_path/.tmp"

# Step 1: docker stack を idempotent 起動
echo "worktree-dev-up: docker stack up -d db api mailpit" >&2
worktree_compose "$worktree_path" up -d db api mailpit >&2 \
  || { echo "worktree-dev-up: docker stack 起動失敗" >&2; exit 1; }

# Step 2: API /healthcheck 待ち
echo "worktree-dev-up: waiting for backend http://localhost:$uvicorn_port/healthcheck" >&2
api_ok=0
for _ in $(seq 1 60); do
  if curl -fsS "http://localhost:$uvicorn_port/healthcheck" >/dev/null 2>&1; then
    api_ok=1; break
  fi
  sleep 1
done

# Step 3: next dev (local bun) 起動。FE port は --port で明示。
next_log="$worktree_path/.tmp/next-dev.log"
next_pid="$worktree_path/.tmp/next-dev.pid"

if lsof -ti ":$next_port" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "worktree-dev-up: port $next_port は既に listen 中 (next dev 起動 skip)" >&2
else
  ( cd "$worktree_path/client" && nohup bun run dev -- --port "$next_port" >"$next_log" 2>&1 & echo $! >"$next_pid" )
fi

# Step 4: frontend 疎通待ち
echo "worktree-dev-up: waiting for frontend http://localhost:$next_port/" >&2
client_ok=0
for _ in $(seq 1 90); do
  if curl -fsS -o /dev/null "http://localhost:$next_port/"; then
    client_ok=1; break
  fi
  sleep 1
done

# Step 5: 結果出力
echo "worktree-dev-up: ============================================" >&2
if [ "$api_ok" = "1" ]; then
  echo "  ✅ API     http://localhost:$uvicorn_port  (docker)" >&2
else
  echo "  ❌ API     http://localhost:$uvicorn_port  (healthcheck 失敗)" >&2
fi
if [ "$client_ok" = "1" ]; then
  echo "  ✅ CLIENT  http://localhost:$next_port" >&2
else
  echo "  ❌ CLIENT  http://localhost:$next_port  (起動失敗 / tail $next_log)" >&2
fi
echo "  ℹ️  log:    $next_log" >&2
echo "  ℹ️  stop:   bash $script_dir/down.sh $worktree_path" >&2
echo "worktree-dev-up: ============================================" >&2

if [ "$api_ok" = "1" ] && [ "$client_ok" = "1" ]; then
  echo "API_URL=http://localhost:$uvicorn_port CLIENT_URL=http://localhost:$next_port"
  exit 0
fi
exit 2
