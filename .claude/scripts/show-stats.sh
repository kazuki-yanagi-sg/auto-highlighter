#!/bin/bash

# カスタムコマンド使用統計表示スクリプト

set -e

# 設定
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
STATS_FILE="${DIR}/../command-stats.json"

# stats.jsonが存在しない場合
if [ ! -f "$STATS_FILE" ]; then
    echo "📊 統計情報がまだありません"
    exit 0
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 カスタムコマンド使用統計"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v jq >/dev/null 2>&1; then
    # 総実行回数
    TOTAL=$(jq -r '.total_executions // 0' "$STATS_FILE")
    LAST_UPDATED=$(jq -r '.last_updated // "N/A"' "$STATS_FILE")

    echo ""
    echo "📈 総実行回数: $TOTAL"
    echo "🕐 最終更新: $LAST_UPDATED"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 コマンド別統計（使用回数順）"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # コマンドを使用回数順でソート
    jq -r '
        .commands |
        to_entries |
        sort_by(-.value.count) |
        .[] |
        "  \(.key):\n    使用回数: \(.value.count)\n    初回使用: \(.value.first_used)\n    最終使用: \(.value.last_used)\n"
    ' "$STATS_FILE"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # トップ5のコマンド
    echo "🏆 最も使用されたコマンド TOP 5:"
    echo ""
    jq -r '
        .commands |
        to_entries |
        sort_by(-.value.count) |
        .[0:5] |
        to_entries |
        .[] |
        "  \(.key + 1). \(.value.key) (\(.value.value.count)回)"
    ' "$STATS_FILE"

else
    # jqがない場合は簡易表示
    echo ""
    cat "$STATS_FILE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"