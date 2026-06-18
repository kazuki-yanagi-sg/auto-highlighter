#!/usr/bin/env bash
# 観点蓄積ファイルの該当エントリ「PR:」行に PR 番号を追記する。
# 使い方: scripts/append-pr.sh <観点名> <PR番号>
#   例: scripts/append-pr.sh "TypeScript as cast の一掃" 2960
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <perspective-name> <pr-number>" >&2
  exit 1
fi

PERSPECTIVE="$1"
PR_NUMBER="$2"
FILE=".tmp/refactor-perspectives.md"

if [ ! -f "$FILE" ]; then
  echo "Perspective file not found: $FILE" >&2
  exit 1
fi

# 対象エントリ（## ... {観点名}）配下の最初の「- PR:」行を上書きする。
# awk で観点名の見出し以降の最初の PR 行のみ置換し、他の同名行には影響させない。
awk -v perspective="$PERSPECTIVE" -v pr="$PR_NUMBER" '
  BEGIN { in_block = 0; replaced = 0 }
  /^## / {
    in_block = (index($0, perspective) > 0) ? 1 : 0
  }
  in_block && !replaced && /^- PR:/ {
    print "- PR: #" pr
    replaced = 1
    next
  }
  { print }
  END {
    if (!replaced) {
      print "Failed to find PR line under perspective: " perspective > "/dev/stderr"
      exit 1
    }
  }
' "$FILE" > "${FILE}.tmp" && mv "${FILE}.tmp" "$FILE"

echo "Updated $FILE: $PERSPECTIVE -> PR #$PR_NUMBER"
