#!/usr/bin/env bash
# Claude Code `WorktreeRemove` hook.
#
# 仕様: stdin から JSON ({session_id, transcript_path, hook_event_name, cwd, worktree_path}) を受け、
# worktree 削除前の cleanup を行う。git worktree remove は Claude Code 本体が実行するため
# 本 hook では行わない (hook の責務は cleanup のみで、削除のブロックも不可)。
#
# 本 hook は契約のみを満たし、teardown (dev 環境の後始末) は setup-worktree skill の
# teardown.sh に委譲する。全体仕様: .claude/skills/setup-worktree/SKILL.md
#
# 失敗時: teardown 失敗は warning で継続 (hook の失敗は debug mode でのみ log される)。

set -euo pipefail

input=$(cat)
worktree_path=$(echo "$input" | jq -r '.worktree_path // empty')

if [ -z "$worktree_path" ]; then
  echo "WorktreeRemove hook: input JSON に worktree_path が無い" >&2
  exit 1
fi

# teardown (dev 環境の後始末) を skill に委譲
# (hook と skill は同じ .claude/ 配下の sibling として配置されている)
hook_dir="$(cd "$(dirname "$0")" && pwd)"
teardown_script="$(cd "$hook_dir/.." && pwd)/skills/setup-worktree/teardown.sh"
if [ -x "$teardown_script" ]; then
  "$teardown_script" "$worktree_path" >&2 \
    || echo "WorktreeRemove hook: teardown 部分失敗 (継続)" >&2
else
  echo "WorktreeRemove hook: teardown.sh が見つからない: $teardown_script (継続)" >&2
fi

echo "WorktreeRemove hook: done (path=$worktree_path)" >&2
