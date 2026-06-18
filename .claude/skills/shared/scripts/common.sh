#!/bin/bash

# 共通関数ライブラリ
# 全スキルのシェルスクリプトで使用する共通関数を提供

# Locale settings for Japanese support
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8

# Colors (exported for use in sourcing scripts)
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[0;33m'
export CYAN='\033[0;36m'
export NC='\033[0m' # No Color

# Counters
ERROR_COUNT=0
WARN_COUNT=0

# Functions
log_error() {
    echo -e "${RED}❌ [ERROR] $1${NC}"
    ERROR_COUNT=$((ERROR_COUNT + 1))
}

log_warn() {
    echo -e "${YELLOW}⚠️  [WARN]  $1${NC}"
    WARN_COUNT=$((WARN_COUNT + 1))
}

log_pass() {
    echo -e "${GREEN}✅ [PASS]  $1${NC}"
}

print_separator() {
    echo "──────────────────────────────────────────────────"
}

# 結果サマリーを出力
# Usage: print_result_summary [reference_path]
print_result_summary() {
    local reference_path="${1:-}"

    print_separator
    echo ""

    if [ "$ERROR_COUNT" -eq 0 ]; then
        if [ "$WARN_COUNT" -gt 0 ]; then
            echo -e "${GREEN}✅ パス（警告: $WARN_COUNT）${NC}"
        else
            echo -e "${GREEN}✅ 全てのチェックをパス${NC}"
        fi
        return 0
    else
        echo -e "${RED}❌ ${ERROR_COUNT}件のエラーを検出（警告: $WARN_COUNT）${NC}"
        if [ -n "$reference_path" ]; then
            echo ""
            echo -e "${YELLOW}参照:${NC}"
            echo "  $reference_path"
        fi
        return 1
    fi
}

# ファイル存在チェック
# Usage: check_file_exists <file_path> <description>
check_file_exists() {
    local file_path="$1"
    local description="$2"

    if [ -f "$file_path" ]; then
        log_pass "$description: $file_path"
        return 0
    else
        log_error "$description が存在しません: $file_path"
        return 1
    fi
}

# セクション存在チェック（Markdown用）サイレントモード
# Usage: check_section <content> <pattern> <section_name>
check_section() {
    local content="$1"
    local section_pattern="$2"
    local section_name="$3"

    if echo "$content" | grep -qE "^## $section_pattern"; then
        return 0
    else
        log_error "必須セクション「$section_name」がありません"
        return 1
    fi
}

# セクション存在チェック（Markdown用）パス時も出力
# Usage: check_section_with_pass <content> <pattern> <section_name>
check_section_with_pass() {
    local content="$1"
    local section_pattern="$2"
    local section_name="$3"

    if echo "$content" | grep -qE "^## $section_pattern"; then
        log_pass "セクション「$section_name」あり"
        return 0
    else
        log_error "必須セクション「$section_name」がありません"
        return 1
    fi
}
