#!/usr/bin/env bash
# Worktree の frontend (next dev) を停止する。
# docker stack (BE/DB) は setup-worktree の teardown.sh が管理するため、ここでは触らない
# (DB を消さずに FE だけ止めたいケースに対応)。
#
# 引数:
#   $1 = worktree_path

set -uo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
source "$script_dir/../setup-worktree/lib.sh"

worktree_path="${1:-}"
if [ -z "$worktree_path" ]; then
  echo "usage: $0 <worktree_path>" >&2
  exit 1
fi
worktree_path="$(cd "$worktree_path" && pwd)" || { echo "worktree-dev-down: worktree_path が存在しない: $1" >&2; exit 1; }

next_pid_file="$worktree_path/.tmp/next-dev.pid"
next_port="$(read_env_value "$worktree_path/.env" NEXT_PORT 2>/dev/null)"

# PID 経由で停止
if [ -f "$next_pid_file" ]; then
  pid="$(cat "$next_pid_file")"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null && echo "worktree-dev-down: next dev (PID $pid) を停止" >&2
  fi
  rm -f "$next_pid_file"
fi

# port に残った process を始末
if [ -n "$next_port" ]; then
  for pid in $(lsof -ti ":$next_port" -sTCP:LISTEN 2>/dev/null); do
    kill "$pid" 2>/dev/null && echo "worktree-dev-down: port $next_port の残 process (PID $pid) を停止" >&2
  done
fi

echo "worktree-dev-down: done (docker stack は teardown.sh で削除しろ)" >&2
