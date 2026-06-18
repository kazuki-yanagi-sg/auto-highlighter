#!/usr/bin/env bash
# session-handoff: 引き継ぎ指示書の決定論パート。
# メタ情報を shell redirect で集め、FILL 付き skeleton を .tmp/handoff-<slug>.md に生成する。
# 長ペイロードの tool call を避け、壊れた streaming 戻り経路を経由させないために shell に寄せる
# (出力破損 BUG-CC-49747 / issue #1195 対策)。
#
# 使い方: bash .claude/skills/session-handoff/gather.sh <slug>
# 出力:   <git-toplevel>/.tmp/handoff-<slug>.md (path を stdout に 1 行出力)
# printf 書式内の ``` は markdown コードフェンス。リテラルなので単一引用符のままでよい。
# shellcheck disable=SC2016
set -euo pipefail

slug="${1:-}"
if [ -z "$slug" ]; then
  echo "usage: gather.sh <slug>  (slug は作業内容を表す kebab-case)" >&2
  exit 2
fi

# 現在の作業ツリー root を取得 (worktree なら worktree、main repo なら main)。
# 新セッションは同じツリーに cd してこのファイルを cat する設計なので、ツリー内の .tmp に置く。
# (worktree 隔離下では Edit ツールが自ツリー外を編集できないため、ツリー内が必須)
tree_root="$(git rev-parse --show-toplevel)"

tmp_dir="$tree_root/.tmp"
mkdir -p "$tmp_dir"
out="$tmp_dir/handoff-${slug}.md"

# 決定論メタ (各コマンドは失敗しても skeleton 生成を止めない)
now="$(date '+%Y-%m-%d %H:%M:%S %Z')"
cwd="$(pwd)"
branch="$(git branch --show-current 2>/dev/null || echo '(detached)')"
worktrees="$(git worktree list 2>/dev/null || echo '(取得失敗)')"
commits="$(git log --oneline -10 2>/dev/null || echo '(取得失敗)')"
changes="$(git status --short 2>/dev/null || echo '(取得失敗)')"
if [ -z "$changes" ]; then changes='(未コミット変更なし)'; fi
prs="$(gh pr list --author '@me' --limit 15 --json number,title,url,state \
  --jq '.[] | "- #\(.number) [\(.state)] \(.title)\n  \(.url)"' 2>/dev/null || echo '(gh 取得失敗)')"
if [ -z "$prs" ]; then prs='(自分の PR なし)'; fi

{
  printf '# 引き継ぎ指示書: %s\n\n' "$slug"
  printf '> このファイルは現セッションの全状態を self-contained に記録したものだ。\n'
  printf '> 新セッションは **まずこのファイルを cat して** 文脈を復元しろ。チャット履歴は壊れている前提で読むな。\n'
  printf '> 生成元: .claude/skills/session-handoff (出力破損 BUG-CC-49747 / issue #1195 対策)\n\n'

  printf '## 0. メタ情報 (自動収集)\n\n'
  printf -- '- 生成日時: %s\n' "$now"
  printf -- '- 作業 cwd: %s\n' "$cwd"
  printf -- '- ブランチ: %s\n' "$branch"
  printf -- '- 対象 issue / PR: <FILL: このセッションが対象とする issue / PR 番号と URL>\n\n'

  printf '### worktree 一覧\n\n```\n%s\n```\n\n' "$worktrees"
  printf '### 直近 commit (cwd)\n\n```\n%s\n```\n\n' "$commits"
  printf '### 未コミット変更 (git status --short)\n\n```\n%s\n```\n\n' "$changes"
  printf '### 自分の PR (gh pr list --author @me)\n\n%s\n\n' "$prs"

  printf '## 1. このセッションの目的 (1 行)\n\n<FILL: 何をしているか 1 行>\n\n'
  printf '## 2. ゴール / 背景 / Out of Scope / DoD\n\n'
  printf -- '- ゴール: <FILL>\n- 背景: <FILL>\n- Out of Scope: <FILL>\n- DoD: <FILL>\n\n'
  printf '## 3. 確定した事実 (確証ベース / file:line)\n\n'
  printf '<FILL: grep で確認済みの事実だけ。推測を書くな。新セッションが再調査せずに済むよう file:line を添えろ>\n\n'
  printf '## 4. 完了したこと\n\n<FILL: 既に done の作業を PR / commit / ファイル単位で>\n\n'
  printf '## 5. 未解決・次の一手 (順序付き具体アクション)\n\n'
  printf '<FILL: 新セッションが最初にやる作業を順番に。判断待ちの論点があれば明記しろ>\n\n'
  printf '## 6. 落とし穴・注意\n\n<FILL: この作業特有のハマりどころ・矛盾・触るな箇所・既知バグ>\n\n'
  printf '## 7. 引き継ぎ後の最初のコマンド\n\n```bash\n<FILL: cwd を合わせ状態確認する最初の数コマンド>\n```\n'
} > "$out"

echo "$out"
