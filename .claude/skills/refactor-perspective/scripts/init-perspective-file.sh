#!/usr/bin/env bash
# 観点蓄積ファイル `.tmp/refactor-perspectives.md` を初期化する。
# 無ければ作成し、最終的にファイルパスを stdout に出力する。
set -euo pipefail

FILE=".tmp/refactor-perspectives.md"

mkdir -p .tmp
if [ ! -f "$FILE" ]; then
  touch "$FILE"
fi

echo "$FILE"
