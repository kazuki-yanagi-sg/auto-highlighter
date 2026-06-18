#!/bin/bash
set -euo pipefail

# PreToolUse / Edit|Write:
# worktree モードが ON の時だけ、クローン (main、.git がディレクトリ) root への
# 非 gitignored ファイル編集をブロックし、worktree での作業へ誘導する。
#
# 運用ルール (senri はクローン併用が主のため default OFF):
#   - worktree モードは opt-in。マーカー `.tmp/.worktree-mode` が無ければ一切ブロックしない。
#   - ON  にする: メッセージに [WORKTREE MODE] を含めて送る (detect-worktree-mode-signal.sh が作成)
#   - OFF にする: メッセージに [WORKTREE MODE OFF] を含めて送る
#
# 例外 (マーカー有でも素通り):
#   - worktree 内 (.git がファイル)
#   - gitignored ファイル (commit されない)
#   - Claude Code の job / session dir

input="$(cat)"
file_path="$(echo "$input" | jq -r '.tool_input.file_path // empty')"
[[ -z "$file_path" ]] && exit 0

if [[ -n "${CLAUDE_JOB_DIR:-}" ]] && [[ "$file_path" == "$CLAUDE_JOB_DIR"/* ]]; then
  exit 0
fi
if [[ "$file_path" == "${HOME}/.claude/jobs/"* ]] || [[ "$file_path" == "${HOME}/.claude/sessions/"* ]]; then
  exit 0
fi

file_dir="$(dirname "$file_path")"
[[ -d "$file_dir" ]] || exit 0

repo_root="$(cd "$file_dir" && git rev-parse --show-toplevel 2>/dev/null || echo "")"
[[ -z "$repo_root" ]] && exit 0

# default OFF: マーカー不在なら何もしない (通常のクローン作業を阻害しない)
[[ -f "$repo_root/.tmp/.worktree-mode" ]] || exit 0

# worktree 内は許可
[[ -f "$repo_root/.git" ]] && exit 0

# gitignored は許可
git -C "$repo_root" check-ignore --quiet "$file_path" 2>/dev/null && exit 0

# .git がディレクトリ = クローン/main root かつ worktree モード ON → ブロック
if [[ -d "$repo_root/.git" ]]; then
  cat >&2 <<EOF
BLOCKED: worktree モード中はクローン root の編集を禁止 (commit 帰属の混乱を防ぐ)。
worktree を作ってその中で編集しろ:
  git worktree add .claude/worktrees/<name> -b feature/<name> develop
  bash .claude/skills/setup-worktree/setup.sh "\$(pwd)/.claude/worktrees/<name>"

編集しようとしたファイル: $file_path

解除する場合のみ: 次のメッセージに [WORKTREE MODE OFF] を含めて送れ
EOF
  exit 2
fi

exit 0
