#!/usr/bin/env bash
# 品質確認: API lint / Client lint / API test / Client test を順に実行する。
# どれか1つでも失敗したら非0で終了する。
set -euo pipefail

echo "[1/4] API lint"
sh project_check.sh -al

echo "[2/4] Client lint"
sh project_check.sh -cl

echo "[3/4] API test"
uv run pytest -v

echo "[4/4] Client test"
(cd client && bun run test)

echo "All quality checks passed."
