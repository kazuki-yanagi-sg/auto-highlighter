#!/usr/bin/env bash
# 変更を全て add → commit（英語）→ push → develop ベースで PR 作成。
# 最後に gh pr create の出力（PR URL）を stdout に流す。
#
# 使い方:
#   scripts/commit-push-pr.sh <english-commit-summary> <perspective-name-jp> <pr-body-file>
#
# 例:
#   scripts/commit-push-pr.sh \
#     "remove all 'as' casts from TypeScript files" \
#     "TypeScript as cast の一掃" \
#     .tmp/pr-body.md
#
# commit message は "refactor: <english-commit-summary>"、
# PR title は "refactor: <perspective-name-jp>"、
# PR body は <pr-body-file> の中身（日本語）。
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <english-commit-summary> <perspective-name-jp> <pr-body-file>" >&2
  exit 1
fi

COMMIT_SUMMARY="$1"
PERSPECTIVE="$2"
BODY_FILE="$3"

if [ ! -f "$BODY_FILE" ]; then
  echo "PR body file not found: $BODY_FILE" >&2
  exit 1
fi

git add .
git commit -m "refactor: ${COMMIT_SUMMARY}"
git push -u origin HEAD
gh pr create --base develop --title "refactor: ${PERSPECTIVE}" --body "$(cat "$BODY_FILE")"
