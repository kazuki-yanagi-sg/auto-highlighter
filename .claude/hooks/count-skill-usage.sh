#!/bin/bash
set -euo pipefail

# skill が使われた回数を skill 名ごとに累計するフック。
#
# skill の起動経路は2つあり、それぞれ別イベントで捕捉する (排他的なので二重計上しない):
#   経路A: ユーザーが /skill-name を直打ち   -> UserPromptExpansion (.command_name)
#   経路B: Claude が Skill tool を自律起動    -> PreToolUse matcher:Skill (.tool_input.skill)
# fork agent (subagent) 内の Skill tool 呼び出しも経路B として同じカウンタに合算される。
#
# カウンタは main worktree 側の .claude/skill-usage.json に集約する。
# worktree 内では --show-toplevel が worktree 自身を指すため、--git-common-dir で
# main の .git を解決し、全 worktree / 全セッションで 1 ファイルに累積させる。
# フォーマット: {"skill-name": 12, ...}。gitignore 済みでローカル限定。
#
# 並行する複数セッション / fork からの同時書き込みは mkdir ロックで直列化する
# (macOS に flock が無いため)。
#
# 中身を読む: jq -S . .claude/skill-usage.json

input="$(cat)"
event="$(printf '%s' "$input" | jq -r '.hook_event_name // empty')"

case "$event" in
  PreToolUse)
    skill_name="$(printf '%s' "$input" | jq -r '.tool_input.skill // empty')"
    ;;
  UserPromptExpansion)
    # slash command の展開のみ対象 (mcp_prompt 等は除外)
    [[ "$(printf '%s' "$input" | jq -r '.expansion_type // empty')" == "slash_command" ]] || exit 0
    skill_name="$(printf '%s' "$input" | jq -r '.command_name // empty')"
    ;;
  *)
    exit 0
    ;;
esac

[[ -n "$skill_name" ]] || exit 0

# worktree をまたいで累積させるため main worktree に集約する
main_root="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)")"
[[ -d "$main_root" ]] || exit 0
counter="$main_root/.claude/skill-usage.json"
lockdir="$counter.lock"

# mkdir ロックで直列化 (flock 非依存)。取得できなければ stale とみなし奪取する。
acquired=0
for _ in $(seq 1 100); do
  if mkdir "$lockdir" 2>/dev/null; then acquired=1; break; fi
  sleep 0.02
done
if [[ "$acquired" -eq 0 ]]; then
  rmdir "$lockdir" 2>/dev/null || true
  mkdir "$lockdir" 2>/dev/null || exit 0
fi
trap 'rmdir "$lockdir" 2>/dev/null || true' EXIT

[[ -f "$counter" ]] || printf '{}\n' > "$counter"

tmp="$(mktemp "${counter}.XXXXXX")"
if jq --arg name "$skill_name" '.[$name] = ((.[$name] // 0) + 1)' "$counter" > "$tmp" 2>/dev/null; then
  mv "$tmp" "$counter"
else
  rm -f "$tmp"
fi

exit 0
