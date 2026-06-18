#!/bin/bash

# データベースモデル検証スクリプト
# Usage: ./validate-model.sh <model_name>
# Example: ./validate-model.sh tickets

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../shared/scripts/common.sh disable=SC1091
source "$SCRIPT_DIR/../../shared/scripts/common.sh"

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <model_name>"
    echo ""
    echo "Example:"
    echo "  $0 tickets"
    echo "  $0 threads"
    echo "  $0 file_uploads"
    exit 1
fi

MODEL_NAME="$1"
KEBAB_NAME=$(echo "$MODEL_NAME" | tr '_' '-')

# スネークケースからパスカルケース（単数形）に変換
to_pascal_case() {
    local input="$1"
    local result=""
    local capitalize_next=1
    for (( i=0; i<${#input}; i++ )); do
        char="${input:$i:1}"
        if [ "$char" = "_" ]; then
            capitalize_next=1
        elif [ $capitalize_next -eq 1 ]; then
            result+="$(echo "$char" | tr '[:lower:]' '[:upper:]')"
            capitalize_next=0
        else
            result+="$char"
        fi
    done
    if [[ "$result" =~ s$ ]] && [[ ! "$result" =~ ss$ ]]; then
        result="${result%s}"
    fi
    echo "$result"
}
PASCAL_NAME=$(to_pascal_case "$MODEL_NAME")

echo -e "${CYAN}📋 データベースモデル検証: $MODEL_NAME${NC}"
print_separator

# 1. SQLModel ファイルチェック
echo -e "\n${CYAN}[1/7] SQLModel ファイルチェック${NC}"

SQLMODEL_PATH="api/src/models/${MODEL_NAME}/models.py"
if [ -f "$SQLMODEL_PATH" ]; then
    log_pass "SQLModel ファイル存在: $SQLMODEL_PATH"

    if grep -q "@dataclass(frozen=True)" "$SQLMODEL_PATH"; then
        log_pass "Constraints dataclass 定義あり"
    else
        log_warn "Constraints dataclass が定義されていません"
    fi

    if grep -q "BaseModel, table=True" "$SQLMODEL_PATH"; then
        log_pass "BaseModel を継承"
    else
        log_error "BaseModel を継承していません"
    fi

    if grep -q "back_populates=" "$SQLMODEL_PATH"; then
        log_pass "back_populates リレーション定義あり"
    else
        log_warn "back_populates が定義されていません（リレーションなしの場合は無視）"
    fi

    if grep -q "Relationship(" "$SQLMODEL_PATH"; then
        if grep -q "cascade_delete=True" "$SQLMODEL_PATH"; then
            log_pass "cascade_delete 設定あり"
        else
            log_warn "cascade_delete が設定されていません（親リレーションのみの場合は無視）"
        fi
    fi
else
    log_error "SQLModel ファイルが存在しません: $SQLMODEL_PATH"
fi

# 2. Prisma スキーマチェック
echo -e "\n${CYAN}[2/7] Prisma スキーマチェック${NC}"

PRISMA_PATH="client/prisma/schema.prisma"
if [ -f "$PRISMA_PATH" ]; then
    if grep -q "^model ${PASCAL_NAME}" "$PRISMA_PATH"; then
        log_pass "Prisma モデル定義あり: ${PASCAL_NAME}"

        if grep -A 50 "^model ${PASCAL_NAME}" "$PRISMA_PATH" | grep -q "@@map(\"${MODEL_NAME}\")" 2>/dev/null; then
            log_pass "@@map テーブルマッピングあり"
        else
            log_warn "@@map(\"${MODEL_NAME}\") が定義されていません"
        fi
    else
        log_error "Prisma モデルが定義されていません: ${PASCAL_NAME}"
    fi
else
    log_error "Prisma スキーマが存在しません: $PRISMA_PATH"
fi

# 3. Factory ファイルチェック
echo -e "\n${CYAN}[3/7] Factory ファイルチェック${NC}"

FACTORY_PATH="api/src/models/${MODEL_NAME}/factories.py"
if [ -f "$FACTORY_PATH" ]; then
    log_pass "Factory ファイル存在: $FACTORY_PATH"

    if grep -q "BaseFactory\[" "$FACTORY_PATH"; then
        log_pass "BaseFactory を継承"
    else
        log_error "BaseFactory を継承していません"
    fi

    if grep -q "_exclude_fields" "$FACTORY_PATH"; then
        log_pass "_exclude_fields 定義あり"
    else
        log_warn "_exclude_fields が定義されていません"
    fi
else
    log_error "Factory ファイルが存在しません: $FACTORY_PATH"
fi

# 4. Frontend Mock ファイルチェック
echo -e "\n${CYAN}[4/7] Frontend Mock ファイルチェック${NC}"

MOCK_PATH="client/src/test/models/${KEBAB_NAME}.ts"
if [ -f "$MOCK_PATH" ]; then
    log_pass "Mock ファイル存在: $MOCK_PATH"

    if grep -q "export const createMock" "$MOCK_PATH"; then
        log_pass "createMock 関数あり"
    else
        log_error "createMock 関数が定義されていません"
    fi

    if grep -qE "export const mock[A-Z].*: .*= createMock" "$MOCK_PATH"; then
        log_pass "mock 単一インスタンスあり"
    else
        log_warn "mock 単一インスタンスが定義されていません"
    fi

    if grep -qE "export const mock.*\[\]" "$MOCK_PATH"; then
        log_pass "mock 配列あり"
    else
        log_warn "mock 配列が定義されていません"
    fi

    if grep -q "@prisma/client" "$MOCK_PATH"; then
        log_pass "Prisma 型をインポート"
    else
        log_error "Prisma 型がインポートされていません"
    fi
else
    log_error "Mock ファイルが存在しません: $MOCK_PATH"
fi

# 5. models/__init__.py チェック
echo -e "\n${CYAN}[5/7] models/__init__.py チェック${NC}"

INIT_PATH="api/src/models/__init__.py"
if [ -f "$INIT_PATH" ]; then
    if grep -q "from src.models.${MODEL_NAME}.models import" "$INIT_PATH"; then
        log_pass "__init__.py にインポートあり"
    else
        log_error "__init__.py にインポートがありません"
    fi

    if grep -q "${PASCAL_NAME}" "$INIT_PATH"; then
        log_pass "__all__ にエクスポートあり"
    else
        log_warn "__all__ にエクスポートがありません"
    fi
else
    log_error "models/__init__.py が存在しません"
fi

# 6. リレーション整合性チェック
echo -e "\n${CYAN}[6/7] リレーション整合性チェック${NC}"

if [ -f "$SQLMODEL_PATH" ] && [ -f "$PRISMA_PATH" ]; then
    SQLMODEL_FK_COUNT=$(grep -c "foreign_key=" "$SQLMODEL_PATH" 2>/dev/null || echo "0")
    SQLMODEL_FK_COUNT=$(echo "$SQLMODEL_FK_COUNT" | tr -d '[:space:]')

    PRISMA_REL_COUNT=$(grep -A 50 "^model ${PASCAL_NAME}" "$PRISMA_PATH" 2>/dev/null | grep -c "@relation" 2>/dev/null || echo "0")
    PRISMA_REL_COUNT=$(echo "$PRISMA_REL_COUNT" | tr -d '[:space:]')

    if [ "$SQLMODEL_FK_COUNT" = "$PRISMA_REL_COUNT" ]; then
        log_pass "リレーション数一致: SQLModel($SQLMODEL_FK_COUNT) = Prisma($PRISMA_REL_COUNT)"
    else
        log_warn "リレーション数不一致: SQLModel($SQLMODEL_FK_COUNT) != Prisma($PRISMA_REL_COUNT)"
    fi
else
    log_warn "リレーション整合性チェックをスキップ（ファイル不足）"
fi

# 7. Seed データチェック（任意）
echo -e "\n${CYAN}[7/7] Seed データチェック${NC}"

SEED_PATH="api/src/database/seed.py"
if [ -f "$SEED_PATH" ]; then
    if grep -q "from src.models.${MODEL_NAME}" "$SEED_PATH"; then
        log_pass "Seed ファイルにインポートあり"
    else
        log_warn "Seed ファイルにインポートがありません（新規モデルの場合は追加推奨）"
    fi
else
    log_warn "Seed ファイルが存在しません"
fi

print_result_summary ".claude/skills/database-operations/SKILL.md"
exit $?
