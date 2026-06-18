#!/bin/bash

# カスタムコマンド検出スクリプト
# UserPromptSubmitフックから呼び出される

# 標準入力からJSONペイロードを読み込む
INPUT=$(cat)

# ユーザーのプロンプトからコマンドを抽出
USER_PROMPT=$(echo "$INPUT" | jq -r '.prompt // ""')

# スラッシュで始まるコマンドを検出
if [[ "$USER_PROMPT" =~ ^/([a-zA-Z0-9_:.-]+) ]]; then
    COMMAND="${BASH_REMATCH[1]}"

    # コマンドが登録済みカスタムコマンドかチェック
    DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    REGISTRY_FILE="${DIR}/../commands/registry.json"

    if [ -f "$REGISTRY_FILE" ] && command -v jq >/dev/null 2>&1; then
        # registry.jsonにコマンドが存在するかチェック
        if jq -e ".commands[\"$COMMAND\"]" "$REGISTRY_FILE" >/dev/null 2>&1; then
            # コマンド使用を記録
            "${DIR}/track-command.sh" "$COMMAND"
        fi
    fi
fi

# 何も出力しない（フックの実行を妨げない）
exit 0