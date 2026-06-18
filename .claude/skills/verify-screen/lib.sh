#!/usr/bin/env bash
# verify-screen skill の共通関数ライブラリ。
#
# 役割:
#   - skill 起動時の前提検証 (worktree 内か / dev server 起動済か / 公式 cli install 済か)
#   - レポート出力先 path の deterministic 採番 (時系列 + ticket + slug)
#   - worktree の NEXT_PORT / UVICORN_PORT を .env から読み取る
#
# 出力先設計:
#   レポートは **main worktree の `.tmp/verify-screen/`** に出す。
#   worktree (.claude/worktrees/<name>/) は削除されると同時にレポートも消えるため、main 側を SoT にする。
#
# read_env_value / main_repo_root は setup-worktree/lib.sh を再利用する (DRY)。

set -uo pipefail

# このファイルは source して使う。BASH_SOURCE は zsh で未設定のため使わず、
# git repo root 経由で setup-worktree/lib.sh を取り込む (bash/zsh 両対応)。
_verify_repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$_verify_repo_root" ] || [ ! -f "$_verify_repo_root/.claude/skills/setup-worktree/lib.sh" ]; then
  echo "verify-screen/lib: setup-worktree/lib.sh を解決できない (worktree root で source しろ)" >&2
  return 1 2>/dev/null || exit 1
fi
source "$_verify_repo_root/.claude/skills/setup-worktree/lib.sh"

# ─────────────────────────────────────────
# is_worktree
# ─────────────────────────────────────────
# 与えられた絶対 path が main repo ではなく .claude/worktrees/ 配下の worktree であることを確認する。
is_worktree() {
  local repo_root="${1:-}"
  if [[ -z "$repo_root" ]]; then
    echo "verify-screen/lib: is_worktree: 第 1 引数 repo_root が必須" >&2
    return 1
  fi
  if [[ "$repo_root" != *"/.claude/worktrees/"* ]]; then
    echo "verify-screen/lib: main repo では verify-screen を起動できない (repo_root=$repo_root)" >&2
    echo "verify-screen/lib: .claude/worktrees/<name>/ の worktree を作成してから再実行しろ" >&2
    return 1
  fi
  return 0
}

# ─────────────────────────────────────────
# resolve_ports
# ─────────────────────────────────────────
# worktree の .env から NEXT_PORT / UVICORN_PORT を抜き、eval で取り込める形で stdout に出す。
#   eval "$(resolve_ports "$worktree_path")"   # → NEXT_PORT / UVICORN_PORT 環境変数化
resolve_ports() {
  local worktree_path="${1:-}"
  if [[ -z "$worktree_path" ]]; then
    echo "verify-screen/lib: resolve_ports: 第 1 引数 worktree_path が必須" >&2
    return 1
  fi
  if [[ ! -f "$worktree_path/.env" || ! -f "$worktree_path/api/.env" ]]; then
    echo "verify-screen/lib: .env 不在。setup-worktree skill を先に流せ" >&2
    return 1
  fi
  local next_port uvicorn_port
  next_port=$(read_env_value "$worktree_path/.env" NEXT_PORT)
  uvicorn_port=$(read_env_value "$worktree_path/api/.env" UVICORN_PORT)
  if [[ -z "$next_port" || -z "$uvicorn_port" ]]; then
    echo "verify-screen/lib: NEXT_PORT / UVICORN_PORT が見つからない" >&2
    return 1
  fi
  echo "NEXT_PORT=$next_port"
  echo "UVICORN_PORT=$uvicorn_port"
}

# ─────────────────────────────────────────
# extract_ticket
# ─────────────────────────────────────────
# branch 名から PR / issue 番号 (最初の数字列) を抽出する。取れなければ "unknown"。
extract_ticket() {
  local branch="${1:-}"
  if [[ -z "$branch" ]]; then
    echo "verify-screen/lib: extract_ticket: 第 1 引数 branch が必須" >&2
    return 1
  fi
  local ticket
  ticket=$(echo "$branch" | grep -oE '[0-9]+' | head -n 1)
  [[ -z "$ticket" ]] && echo "unknown" || echo "$ticket"
}

# ─────────────────────────────────────────
# report_dir
# ─────────────────────────────────────────
# <main-repo>/.tmp/verify-screen/<YYYYMMDDHHMMSS>-<ticket>-<slug>/ を
# snapshots/ screenshots/ 付きで作成し、絶対 path を stdout に出す。
report_dir() {
  local worktree_path="${1:-}" scenario_slug="${2:-}"
  if [[ -z "$worktree_path" || -z "$scenario_slug" ]]; then
    echo "verify-screen/lib: report_dir: worktree_path / scenario_slug が必須" >&2
    return 1
  fi
  local main_root branch ticket ts dir
  main_root=$(main_repo_root "$worktree_path") || return 1
  branch=$(git -C "$worktree_path" branch --show-current 2>/dev/null)
  ticket=$(extract_ticket "${branch:-unknown}") || return 1
  ts=$(date +%Y%m%d%H%M%S)
  dir="$main_root/.tmp/verify-screen/${ts}-${ticket}-${scenario_slug}"
  mkdir -p "$dir/snapshots" "$dir/screenshots" || {
    echo "verify-screen/lib: report_dir: mkdir 失敗 ($dir)" >&2
    return 1
  }
  echo "$dir"
}

# ─────────────────────────────────────────
# assert_dev_up
# ─────────────────────────────────────────
# worktree の frontend (next dev) が listen しているか curl で確認する。
assert_dev_up() {
  local worktree_path="${1:-}"
  if [[ -z "$worktree_path" ]]; then
    echo "verify-screen/lib: assert_dev_up: 第 1 引数 worktree_path が必須" >&2
    return 1
  fi
  local next_port
  next_port=$(read_env_value "$worktree_path/.env" NEXT_PORT)
  if curl -fsS --max-time 5 "http://localhost:${next_port}/" >/dev/null 2>&1; then
    return 0
  fi
  echo "verify-screen/lib: dev server (http://localhost:${next_port}/) に届かない" >&2
  echo "verify-screen/lib: 次で起動してから再実行しろ:" >&2
  echo "  bash .claude/skills/worktree-dev-up/up.sh \"$worktree_path\"" >&2
  return 1
}

# ─────────────────────────────────────────
# assert_playwright_cli_skill
# ─────────────────────────────────────────
# Microsoft 公式 @playwright/cli の SKILLS が install 済か確認する。
assert_playwright_cli_skill() {
  local worktree_path="${1:-}"
  if [[ -z "$worktree_path" ]]; then
    echo "verify-screen/lib: assert_playwright_cli_skill: 第 1 引数 worktree_path が必須" >&2
    return 1
  fi
  local skill_file="$worktree_path/.claude/skills/playwright-cli/SKILL.md"
  if [[ -f "$skill_file" ]]; then
    return 0
  fi
  echo "verify-screen/lib: 公式 @playwright/cli skill 未 install ($skill_file)" >&2
  echo "verify-screen/lib: 次で install してから再実行しろ:" >&2
  echo "  (cd \"$worktree_path\" && npx -y @playwright/cli@latest install --skills)" >&2
  return 1
}
