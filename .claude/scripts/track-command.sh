#!/bin/bash

# カスタムコマンド使用回数トラッキングスクリプト
# 使用方法: ./track-command.sh "コマンド名"

set -e

# 設定
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
STATS_FILE="${DIR}/../command-stats.json"
COMMAND_NAME="$1"

# コマンド名が空の場合は終了
if [ -z "$COMMAND_NAME" ]; then
    exit 0
fi

# stats.jsonが存在しない場合は初期化
if [ ! -f "$STATS_FILE" ]; then
    echo '{
  "version": "1.0.0",
  "commands": {},
  "total_executions": 0,
  "last_updated": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
}' > "$STATS_FILE"
fi

# 現在のタイムスタンプ
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# jqを使用してJSONを更新
if command -v jq >/dev/null 2>&1; then
    # コマンドが既に存在するかチェック
    if jq -e ".commands[\"$COMMAND_NAME\"]" "$STATS_FILE" >/dev/null 2>&1; then
        # 既存コマンドの場合：カウントを増やして最終使用時刻を更新
        jq --arg cmd "$COMMAND_NAME" --arg ts "$TIMESTAMP" '
            .commands[$cmd].count += 1 |
            .commands[$cmd].last_used = $ts |
            .total_executions += 1 |
            .last_updated = $ts
        ' "$STATS_FILE" > "${STATS_FILE}.tmp" && mv "${STATS_FILE}.tmp" "$STATS_FILE"
    else
        # 新規コマンドの場合：エントリを作成
        jq --arg cmd "$COMMAND_NAME" --arg ts "$TIMESTAMP" '
            .commands[$cmd] = {
                "count": 1,
                "first_used": $ts,
                "last_used": $ts
            } |
            .total_executions += 1 |
            .last_updated = $ts
        ' "$STATS_FILE" > "${STATS_FILE}.tmp" && mv "${STATS_FILE}.tmp" "$STATS_FILE"
    fi
else
    # jqがない場合は簡易的にログファイルに記録
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") - Command executed: $COMMAND_NAME" >> "${STATS_FILE}.log"
fi