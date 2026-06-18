#!/usr/bin/env bash
# setup-worktree/lib.sh の自己テスト (docker / git に依存しない純粋関数のみ)。
# 使い方: bash .claude/skills/setup-worktree/test_lib.sh

set -uo pipefail
cd "$(dirname "$0")"
source ./lib.sh

pass=0
fail=0
check() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    echo "  ok: $label"
    pass=$((pass + 1))
  else
    echo "  NG: $label (expected='$expected' actual='$actual')"
    fail=$((fail + 1))
  fi
}

echo "== slugify_branch =="
check "feature/foo-bar.baz" "feature_foo_bar_baz" "$(slugify_branch 'feature/foo-bar.baz')"
check "UPPER/Case" "upper_case" "$(slugify_branch 'UPPER/Case')"
check "1025-x" "1025_x" "$(slugify_branch '1025-x')"

echo "== compute_port (deterministic & range) =="
p1=$(compute_port "feature_x" 60000 next)
p2=$(compute_port "feature_x" 60000 next)
check "deterministic" "$p1" "$p2"
salt_diff=$([[ "$(compute_port feature_x 60000 next)" != "$(compute_port feature_x 60000 uvicorn)" ]] && echo diff || echo same)
check "salt 分離" "diff" "$salt_diff"
in_range=$([[ "$p1" -ge 60000 && "$p1" -le 60999 ]] && echo yes || echo no)
check "範囲内 60000-60999" "yes" "$in_range"

echo "== compute_project_name =="
check "prefix" "senri-wt-feature_x" "$(compute_project_name 'feature_x')"

echo "== read_env_value (行末コメント / 引用符除去) =="
tmp=$(mktemp)
cat > "$tmp" <<'EOF'
NEXT_PORT=13100
POSTGRES_PORT=15532 # コメント付き
PROJECT_NAME="senri-core-system-2"
EOF
check "plain" "13100" "$(read_env_value "$tmp" NEXT_PORT)"
check "trailing comment 除去" "15532" "$(read_env_value "$tmp" POSTGRES_PORT)"
check "quote 除去" "senri-core-system-2" "$(read_env_value "$tmp" PROJECT_NAME)"
rm -f "$tmp"

echo "== write_root_env / write_client_env (port 書換) =="
work=$(mktemp -d)
parent=$(mktemp -d)
mkdir -p "$parent/client"
cat > "$parent/.env" <<'EOF'
PROJECT_NAME="senri-core-system-2"
NEXT_PORT=13100
UVICORN_PORT=18100
OTELCOL_ARGS=
EOF
cat > "$parent/client/.env" <<'EOF'
UVICORN_PORT=18100
POSTGRES_PORT=15532
NEXT_PUBLIC_API_ORIGIN_URL=http://localhost:${UVICORN_PORT}
DATABASE_URL=postgresql://myuser:mypassword@localhost:15532/mydatabase
EOF
write_root_env "$work" "$parent" "senri-wt-feature_x" 60123 61123 2>/dev/null
check "root NEXT_PORT" "60123" "$(read_env_value "$work/.env" NEXT_PORT)"
check "root PROJECT_NAME" "senri-wt-feature_x" "$(read_env_value "$work/.env" PROJECT_NAME)"
check "root COMPOSE_PROJECT_NAME 追記" "senri-wt-feature_x" "$(read_env_value "$work/.env" COMPOSE_PROJECT_NAME)"
write_client_env "$work" "$parent" 61123 62123 2>/dev/null
check "client POSTGRES_PORT" "62123" "$(read_env_value "$work/client/.env" POSTGRES_PORT)"
check "client DATABASE_URL host port 書換" "postgresql://myuser:mypassword@localhost:62123/mydatabase" "$(read_env_value "$work/client/.env" DATABASE_URL)"
check 'client API origin は ${UVICORN_PORT} 参照のまま' 'http://localhost:${UVICORN_PORT}' "$(read_env_value "$work/client/.env" NEXT_PUBLIC_API_ORIGIN_URL)"
rm -rf "$work" "$parent"

echo ""
echo "結果: pass=$pass fail=$fail"
[[ "$fail" -eq 0 ]]
