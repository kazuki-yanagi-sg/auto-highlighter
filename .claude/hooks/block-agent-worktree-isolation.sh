#!/bin/bash
set -euo pipefail

# PreToolUse / Agent:
# Agent tool の isolation: "worktree" を禁止する (公式機能だが破壊系バグ未修正)。
# 並列・分離が必要なら fork (isolation 指定なし) + `git worktree add` + setup-worktree skill
# のパターンを使う。詳細は .claude/rules/fork-agent-worktree.md を参照。

input="$(cat)"
isolation="$(echo "$input" | jq -r '.tool_input.isolation // empty')"

if [[ "$isolation" == "worktree" ]]; then
  cat >&2 <<'EOF'
BLOCKED: Agent tool の isolation: "worktree" は使用禁止 (公式バグ未修正)。

isolation パラメータを外して Agent を呼べ。
分離が必要なら fork + `git worktree add .claude/worktrees/<name>` + setup-worktree skill を使え。
詳細: .claude/rules/fork-agent-worktree.md
EOF
  exit 2
fi

exit 0
