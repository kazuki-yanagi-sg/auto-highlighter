#!/bin/bash
set -euo pipefail

# PreToolUse / Edit|Write:
# worktree (.claude/worktrees/<name>/、.git がファイル) 内の `.claude/` 配下への書き込みを自動許可する。
# Claude Code は `.claude/` を sensitive file として既定でブロックするが、worktree では
# playwright-cli skill の install や skill 編集で `.claude/` を書く必要があるため即許可する。
# クローン (main、.git がディレクトリ) には作用しない。

input="$(cat)"
file_path="$(echo "$input" | jq -r '.tool_input.file_path // empty')"
[[ -z "$file_path" ]] && exit 0

file_dir="$(dirname "$file_path")"
[[ -d "$file_dir" ]] || exit 0

repo_root="$(cd "$file_dir" && git rev-parse --show-toplevel 2>/dev/null || echo "")"
[[ -z "$repo_root" ]] && exit 0

# .git がファイル = worktree のみ対象 (クローン/main は .git がディレクトリ → 素通り)
[[ -f "$repo_root/.git" ]] || exit 0

case "$file_path" in
  "$repo_root/.claude/"*)
    jq -nc '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "worktree 内 .claude/ 配下の書き込みを自動許可"}}'
    ;;
esac

exit 0
