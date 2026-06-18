#!/usr/bin/env bash
# Claude Code `WorktreeCreate` hook.
#
# 仕様: stdin から JSON ({session_id, transcript_path, hook_event_name, cwd, name}) を受け、
# worktree 作成後に絶対 path を stdout に 1 行出力する。非ゼロ exit / path 不在で失敗扱い。
# hook がある場合 Claude Code 本体は git worktree add を行わない (hook が default 挙動を置換)。
#
# 本 hook は契約のみを満たし、環境 setup は setup-worktree skill に委譲する。
# 全体仕様: .claude/skills/setup-worktree/SKILL.md
#
# 失敗時: worktree 作成失敗のみ exit 1。setup 失敗は warning で継続 (worktree は残る)。

set -euo pipefail

input=$(cat)

session_id=$(echo "$input" | jq -r '.session_id // empty')
name=$(echo "$input" | jq -r '.name // empty')
caller_cwd=$(echo "$input" | jq -r '.cwd // empty')

if [ -z "$caller_cwd" ]; then
  echo "WorktreeCreate hook: input JSON に cwd が無い" >&2
  exit 1
fi

# worktree 識別子: name 優先、無ければ session_id から hex 16 文字を切り出す
if [ -n "$name" ]; then
  wt_id="$name"
elif [ -n "$session_id" ]; then
  wt_id="agent-$(echo "$session_id" | tr -d '-' | tr '[:upper:]' '[:lower:]' | head -c 16)"
else
  echo "WorktreeCreate hook: session_id も name も無く識別子を生成できない" >&2
  exit 1
fi

# 運用ルール: worktree は .claude/worktrees/ 配下 (公式デフォルトと同じ場所)、branch は feature/ prefix。
# 分岐元は HEAD = 作成時に checkout している branch が親になる (develop で作れば develop 起点、
# feature branch 上で作ればその子 branch としてスタックできる)
target_path="$caller_cwd/.claude/worktrees/$wt_id"
branch="feature/$wt_id"

# stdout は最終 path 専用なので git 出力は stderr へ
if ! git -C "$caller_cwd" worktree add "$target_path" -b "$branch" HEAD >&2; then
  echo "WorktreeCreate hook: git worktree add 失敗" >&2
  exit 1
fi

# 環境 setup は setup-worktree skill に委譲
# (hook と skill は同じ .claude/ 配下の sibling として配置されている)
hook_dir="$(cd "$(dirname "$0")" && pwd)"
setup_script="$(cd "$hook_dir/.." && pwd)/skills/setup-worktree/setup.sh"
if [ -x "$setup_script" ]; then
  "$setup_script" "$target_path" "$caller_cwd" "$branch" >&2 \
    || echo "WorktreeCreate hook: setup-worktree 部分失敗 (worktree は作成済)" >&2
else
  echo "WorktreeCreate hook: setup-worktree skill が見つからない: $setup_script (worktree は作成済)" >&2
fi

# 仕様により stdout は worktree の絶対 path 1 行のみ
echo "$target_path"
