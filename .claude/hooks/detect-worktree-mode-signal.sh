#!/bin/bash
set -euo pipefail

# UserPromptSubmit:
# worktree モード (enforce-worktree-mode.sh のブロック) を user の明示シグナルで toggle する。
# このフックは user が Enter を押した時のみ発火するため、Claude が勝手に切り替えられない。
#
#   [WORKTREE MODE]     → マーカー作成 (クローン root 編集をブロック開始、sticky)
#   [WORKTREE MODE OFF] → マーカー削除 (通常のクローン編集に戻す)
#   どちらも無し         → 現状維持 (default はマーカー不在 = OFF)

input="$(cat)"
prompt="$(echo "$input" | jq -r '.prompt // empty')"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
[[ -z "$repo_root" ]] && exit 0

marker_dir="$repo_root/.tmp"
marker="$marker_dir/.worktree-mode"

# OFF を先に判定 ([WORKTREE MODE OFF] は [WORKTREE MODE] を部分一致で含むため)
if [[ "$prompt" == *"[WORKTREE MODE OFF]"* ]]; then
  rm -f "$marker"
  echo "🔓 worktree モード OFF: クローン root 編集の制限を解除した" >&2
  exit 0
fi

if [[ "$prompt" == *"[WORKTREE MODE]"* ]]; then
  mkdir -p "$marker_dir"
  printf 'on since %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$marker"
  echo "🔒 worktree モード ON: クローン root の編集をブロックする ($marker)" >&2
fi

exit 0
