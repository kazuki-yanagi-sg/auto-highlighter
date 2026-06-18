#!/usr/bin/env bash
# Worktree の docker stack を停止し volume (= DB) を削除する。
# `git worktree remove` 自体は呼ばない (呼び出し元の責務)。
#
# 引数:
#   $1 = worktree_path  (worktree の絶対 path)
#
# 保護:
#   project 名が `senri-wt-` prefix でない場合は停止 (main / クローンを絶対に down しない)。

set -uo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
source "$script_dir/lib.sh"

worktree_path="${1:-}"
if [[ -z "$worktree_path" ]]; then
  echo "usage: $0 <worktree_path>" >&2
  exit 1
fi
worktree_path="$(cd "$worktree_path" && pwd)" || { echo "teardown: worktree_path が存在しない: $1" >&2; exit 1; }

root_env="$worktree_path/.env"
if [[ ! -f "$root_env" ]]; then
  echo "teardown: $root_env が無い (既に teardown 済みか setup 未実行)" >&2
  exit 0
fi

project_name="$(read_env_value "$root_env" PROJECT_NAME)"
if [[ "$project_name" != senri-wt-* ]]; then
  echo "teardown: project 名が senri-wt- prefix でない ('$project_name')。main / クローン保護のため停止" >&2
  exit 1
fi

# `down -v --rmi local`:
#   - この project (worktree) の container / volume(DB) / network を削除
#   - --rmi local: この project が build した image (api、`image:` 無指定 = local) のみ削除
#     postgres / mailpit / pgadmin など `image:` 指定の共有 base image は消さない
#   - 対象は `-p $project_name` 配下のみ。他 worktree / 他 session / main には一切触れない
echo "teardown: docker stack down -v --rmi local (project=$project_name)" >&2
worktree_compose "$worktree_path" down -v --rmi local --remove-orphans \
  || echo "teardown: ⚠️ docker compose down に失敗。'docker ps' で残コンテナを確認しろ" >&2

echo "teardown: ============================================" >&2
echo "  ✅ teardown done: $project_name" >&2
echo "     この worktree の container / volume (DB) / network / 自前 image を削除した" >&2
echo "     (他 worktree / 他 session / main / 共有 base image には未干渉)" >&2
echo "  ℹ️  worktree dir 自体は 'git worktree remove $worktree_path' で削除しろ" >&2
echo "teardown: ============================================" >&2
