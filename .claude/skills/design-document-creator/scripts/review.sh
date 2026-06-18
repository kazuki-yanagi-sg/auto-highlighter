#!/bin/bash

# 設計書レビュースクリプト
# Usage: ./review.sh docs/design/[filename].md

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../shared/scripts/common.sh disable=SC1091
source "$SCRIPT_DIR/../../shared/scripts/common.sh"

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <design-document.md>"
    echo ""
    echo "Example:"
    echo "  $0 docs/design/my-feature-design.md"
    exit 1
fi

FILE_PATH="$1"

# Check file exists
if [ ! -f "$FILE_PATH" ]; then
    echo -e "${RED}❌ ファイルが見つかりません: $FILE_PATH${NC}"
    exit 1
fi

echo -e "${CYAN}📄 設計書レビュー: $FILE_PATH${NC}"
print_separator

CONTENT=$(cat "$FILE_PATH")

# Detect document type
IS_IMPLEMENTATION_PLAN=false
if [[ "$FILE_PATH" == *-implementation-plan.md ]]; then
    IS_IMPLEMENTATION_PLAN=true
    echo -e "${CYAN}📋 ドキュメントタイプ: 実装計画書（Stacked PR方式）${NC}"
fi

if [ "$IS_IMPLEMENTATION_PLAN" = true ]; then
    # Implementation plan required sections (5 sections, EARS not required)
    check_section "$CONTENT" "[0-9]*\\.?\\s*前提条件" "前提条件"
    check_section "$CONTENT" "[0-9]*\\.?\\s*ブランチ依存関係" "ブランチ依存関係"
    check_section "$CONTENT" "[0-9]*\\.?\\s*実装ブランチ詳細" "実装ブランチ詳細"
    check_section "$CONTENT" "[0-9]*\\.?\\s*実装進捗表" "実装進捗表"
    check_section "$CONTENT" "[0-9]*\\.?\\s*品質担保チェックリスト" "品質担保チェックリスト"
else
    # Design document required sections (6 sections total)
    check_section "$CONTENT" "1\\. 概要" "1. 概要"
    check_section "$CONTENT" "2\\. データベース設計" "2. データベース設計"
    check_section "$CONTENT" "3\\. 処理フロー" "3. 処理フロー"
    check_section "$CONTENT" "4\\. ディレクトリ構成" "4. ディレクトリ構成"
    check_section "$CONTENT" "5\\. バックエンド設計" "5. バックエンド設計"
    check_section "$CONTENT" "6\\. フロントエンド設計" "6. フロントエンド設計"
fi

# Design document specific checks
if [ "$IS_IMPLEMENTATION_PLAN" = false ]; then
    # Check database design section
    DB_SECTION=$(echo "$CONTENT" | sed -n '/^## 2\. データベース設計/,/^## [0-9]/p' | sed '$d')

    if [ -n "$DB_SECTION" ]; then
        # Check for change table or "修正なし"
        if ! echo "$DB_SECTION" | grep -qE '修正なし|追加|変更|削除'; then
            log_error "データベース設計に変更概要（追加/変更/削除）または「修正なし」の記載がありません"
        fi

        # If "修正なし", check for related table names
        if echo "$DB_SECTION" | grep -qE '修正なし'; then
            if ! echo "$DB_SECTION" | grep -qE '関連テーブル|関連:'; then
                log_warn "「修正なし」の場合でも関連テーブル名を記載してください"
            fi
        fi

        # If there's Enum mention without definition
        if echo "$DB_SECTION" | grep -qiE 'enum.*追加|enum.*変更|enum.*削除|新規.*enum'; then
            if ! echo "$DB_SECTION" | grep -qE 'class.*Enum|Enum定義'; then
                log_error "Enumの追加・変更・削除がある場合はEnum定義を記載してください"
            fi
        fi
    fi

    # Check EARS requirements in overview section
    OVERVIEW_SECTION=$(echo "$CONTENT" | sed -n '/^## 1\. 概要/,/^## [0-9]/p' | sed '$d')

    if [ -n "$OVERVIEW_SECTION" ]; then
        if ! echo "$OVERVIEW_SECTION" | grep -qE '要件分析.*EARS|EARS.*要件分析'; then
            log_error "概要セクションにEARS要件分析がありません（### 1.4 要件分析（EARS方式））"
        fi

        # Check for EARS categories
        if ! echo "$OVERVIEW_SECTION" | grep -qE 'Ubiquitous|常時有効'; then
            log_warn "EARS: Ubiquitous（常時有効）セクションがありません"
        fi
        if ! echo "$OVERVIEW_SECTION" | grep -qE 'Event-Driven|イベント駆動'; then
            log_warn "EARS: Event-Driven（イベント駆動）セクションがありません"
        fi
        if ! echo "$OVERVIEW_SECTION" | grep -qE 'Unwanted|異常系'; then
            log_warn "EARS: Unwanted Behavior（異常系）セクションがありません"
        fi
    fi

    # Directory references for new directories
    DIR_SECTION=$(echo "$CONTENT" | sed -n '/^## 4\. ディレクトリ構成/,/^## [0-9]/p' | sed '$d')

    if [ -n "$DIR_SECTION" ]; then
        NEW_DIRS=$(echo "$DIR_SECTION" | grep -E '#\s*新規' | grep -v '←.*既存' | grep -v '新規パターン' || true)
        if [ -n "$NEW_DIRS" ]; then
            while IFS= read -r line; do
                DIR_NAME=$(echo "$line" | grep -oE '[a-zA-Z0-9_-]+/\s*#' | sed 's/#//' | tr -d ' ' || true)
                if [ -n "$DIR_NAME" ]; then
                    log_error "「${DIR_NAME}」に参考元が記載されていません（← 既存: xxx を参考）"
                fi
            done <<< "$NEW_DIRS"
        fi

        if ! echo "$DIR_SECTION" | grep -qE '├──|└──'; then
            log_error "ディレクトリ構成がツリー形式で記載されていません"
        fi

        # Check test files are included (TDD requirement)
        if ! echo "$DIR_SECTION" | grep -qE 'api/tests/|tests/unit/|tests/integration/'; then
            log_error "ディレクトリ構成にテストファイル（api/tests/）の記載がありません（TDD必須）"
        fi
    fi

    # Sequence diagram in flow section
    FLOW_SECTION=$(echo "$CONTENT" | sed -n '/^## 3\. 処理フロー/,/^## [0-9]/p' | sed '$d')

    if [ -n "$FLOW_SECTION" ]; then
        if ! echo "$FLOW_SECTION" | grep -q 'sequenceDiagram'; then
            log_error "処理フローセクションにシーケンス図がありません"
        fi
    fi

    # Check backend section has package requirements and authentication/authorization
    BACKEND_SECTION=$(echo "$CONTENT" | sed -n '/^## 5\. バックエンド設計/,/^## [0-9]/p' | sed '$d')

    if [ -n "$BACKEND_SECTION" ]; then
        if ! echo "$BACKEND_SECTION" | grep -qE '修正なし'; then
            if ! echo "$BACKEND_SECTION" | grep -qE 'パッケージ要件|パッケージ'; then
                log_warn "バックエンド設計にパッケージ要件の記載がありません"
            fi
            # Check authentication/authorization (security critical)
            if ! echo "$BACKEND_SECTION" | grep -qE '認証・認可|認証|認可|修正なし|既存.*同様'; then
                log_error "バックエンド設計に認証・認可の記載がありません（セキュリティ必須項目）"
            fi
        fi
    fi

    # Check frontend section has package requirements, screen design, and authentication/authorization
    FRONTEND_SECTION=$(echo "$CONTENT" | sed -n '/^## 6\. フロントエンド設計/,$p')

    if [ -n "$FRONTEND_SECTION" ]; then
        if ! echo "$FRONTEND_SECTION" | grep -qE '修正なし'; then
            # Check screen design (6.1)
            if ! echo "$FRONTEND_SECTION" | grep -qE '画面デザイン|ボタン配置|レイアウト'; then
                log_error "フロントエンド設計に画面デザイン（6.1）の記載がありません"
            fi
            # Check package requirements (6.2)
            if ! echo "$FRONTEND_SECTION" | grep -qE 'パッケージ要件|パッケージ'; then
                log_warn "フロントエンド設計にパッケージ要件の記載がありません"
            fi
            # Check authentication/authorization (security critical)
            if ! echo "$FRONTEND_SECTION" | grep -qE '認証・認可|認証|認可|修正なし|既存.*同様'; then
                log_error "フロントエンド設計に認証・認可の記載がありません（セキュリティ必須項目）"
            fi
        fi
    fi
fi

# Implementation plan specific checks
# Note: EARS is NOT required in implementation plans (already in design doc)
if [ "$IS_IMPLEMENTATION_PLAN" = true ]; then
    # Check branch details have checklists
    BRANCH_SECTION=$(echo "$CONTENT" | sed -n '/実装ブランチ詳細/,$p')
    if [ -n "$BRANCH_SECTION" ]; then
        if ! echo "$BRANCH_SECTION" | grep -qE 'チェックリスト|\\- \\[ \\]'; then
            log_warn "実装ブランチにチェックリストがありません"
        fi
        if ! echo "$BRANCH_SECTION" | grep -qE '変更ファイル|ファイル一覧'; then
            log_warn "実装ブランチに変更ファイル一覧がありません"
        fi
    fi
fi

# Mermaid syntax validation (requires Docker)
check_mermaid() {
    if ! command -v docker &> /dev/null; then
        log_warn "Dockerが利用不可のためMermaid構文チェックをスキップ"
        return
    fi

    local project_root
    local temp_dir
    project_root="$(cd "$SCRIPT_DIR/../../.." && pwd)"
    temp_dir="$project_root/.tmp-mermaid-check"
    mkdir -p "$temp_dir"

    local block_num=0
    local in_mermaid=false
    local current_block=""

    while IFS= read -r line; do
        if [[ "$line" == '```mermaid' ]]; then
            in_mermaid=true
            current_block=""
        elif [[ "$line" == '```' ]] && [ "$in_mermaid" = true ]; then
            in_mermaid=false
            if [ -n "$current_block" ]; then
                echo "$current_block" > "$temp_dir/block_$block_num.mmd"
                block_num=$((block_num + 1))
            fi
        elif [ "$in_mermaid" = true ]; then
            current_block="${current_block}${line}"$'\n'
        fi
    done < "$FILE_PATH"

    if [ "$block_num" -eq 0 ]; then
        rm -rf "$temp_dir"
        return
    fi

    echo -e "${CYAN}🔍 Mermaid構文チェック: ${block_num}ブロック${NC}"

    for ((i=0; i<block_num; i++)); do
        local error_output
        error_output=$(docker run --rm -v "$temp_dir:/data" minlag/mermaid-cli \
            -i "/data/block_$i.mmd" -o "/data/out_$i.svg" 2>&1) || true

        if echo "$error_output" | grep -qE "^Error:|Parse error"; then
            local error_msg
            error_msg=$(echo "$error_output" | grep -E "^Error:|Parse error" | head -1)
            log_error "Mermaid構文エラー (ブロック $((i+1))): $error_msg"
        fi
    done

    rm -rf "$temp_dir"
}

check_mermaid

print_result_summary
exit $?
