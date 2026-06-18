#!/usr/bin/env bash
# Worktree を hash port + 専用 docker stack + main DB コピーで main から分離する。
#
# 引数:
#   $1 = worktree_path  (worktree の絶対 path、例 <main>/.claude/worktrees/<name>)
#   $2 = parent_path?   (省略時は git worktree list 先頭 = main repo root)
#   $3 = branch?        (省略時は worktree の HEAD ブランチ)
#
# 動作:
#   1. branch slug → 6 万番台ポート / project 名を deterministic 採番
#   2. root / api / client の 3 つの .env を port 書き換えコピーで生成
#   3. client deps (bun install + prisma generate)
#   4. worktree 専用 docker stack を起動 (db → DB copy → api/mailpit、pgAdmin は起動しない)
#   5. main DB を worktree DB へコピー → alembic upgrade heads でブランチ分を上乗せ
#   6. ポート早見表を banner 出力

set -uo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
source "$script_dir/lib.sh"

worktree_path="${1:-}"
if [[ -z "$worktree_path" ]]; then
  echo "usage: $0 <worktree_path> [parent_path] [branch]" >&2
  exit 1
fi
worktree_path="$(cd "$worktree_path" && pwd)" || { echo "setup-worktree: worktree_path が存在しない: $1" >&2; exit 1; }

parent_path="${2:-}"
if [[ -z "$parent_path" ]]; then
  parent_path="$(main_repo_root "$worktree_path")" || exit 1
fi
parent_path="$(cd "$parent_path" && pwd)"

branch="${3:-}"
if [[ -z "$branch" ]]; then
  branch="$(git -C "$worktree_path" branch --show-current 2>/dev/null)"
fi
if [[ -z "$branch" || "$branch" == "develop" || "$branch" == "main" ]]; then
  echo "setup-worktree: branch が空 / develop / main。feature ブランチで worktree を作れ (branch='$branch')" >&2
  exit 1
fi

if [[ "$worktree_path" == "$parent_path" ]]; then
  echo "setup-worktree: worktree_path と parent_path が同一。main repo では実行禁止" >&2
  exit 1
fi

# Step 1: 採番
slug="$(slugify_branch "$branch")" || exit 1
project_name="$(compute_project_name "$slug")" || exit 1
next_port="$(compute_port "$slug" 60000 next)"
uvicorn_port="$(compute_port "$slug" 61000 uvicorn)"
postgres_port="$(compute_port "$slug" 62000 postgres)"
mailpit_smtp_port="$(compute_port "$slug" 63000 mailpit_smtp)"
mailpit_web_port="$(compute_port "$slug" 64000 mailpit_web)"

echo "setup-worktree: branch=$branch slug=$slug project=$project_name" >&2
echo "setup-worktree: ports NEXT=$next_port UVICORN=$uvicorn_port POSTGRES=$postgres_port MAILPIT_SMTP=$mailpit_smtp_port MAILPIT_WEB=$mailpit_web_port" >&2

# Step 2: .env 生成
write_worktree_envs "$worktree_path" "$parent_path" "$project_name" \
  "$next_port" "$uvicorn_port" "$postgres_port" "$mailpit_smtp_port" "$mailpit_web_port" || exit 1

# Step 3: client deps
if [[ -d "$worktree_path/client" ]]; then
  echo "setup-worktree: client deps install (bun install + prisma generate)" >&2
  ( cd "$worktree_path/client" && bun install --frozen-lockfile && bun run generate-prisma ) \
    || echo "setup-worktree: ⚠️ client deps install に失敗。手動で 'cd client && bun install && bun run generate-prisma' を流せ" >&2
fi

# Step 3.5: Microsoft 公式 @playwright/cli skill を worktree に install (verify-screen が delegate)
echo "setup-worktree: playwright-cli skill install (npx @playwright/cli)" >&2
( cd "$worktree_path" && npx -y @playwright/cli@latest install --skills >&2 ) \
  || echo "setup-worktree: ⚠️ playwright-cli skill install に失敗。verify-screen 前に手動 install しろ" >&2
# bare `playwright-cli` コマンドが PATH に無いと公式 skill の手順が動かないため global 導入を保証
if ! command -v playwright-cli >/dev/null 2>&1; then
  echo "setup-worktree: playwright-cli を global install (npm i -g @playwright/cli)" >&2
  npm install -g @playwright/cli >&2 \
    || echo "setup-worktree: ⚠️ playwright-cli global install に失敗。'npm i -g @playwright/cli' を手動実行しろ" >&2
fi

# Step 4: docker stack (db を先に起動)
echo "setup-worktree: docker stack up (db)" >&2
worktree_compose "$worktree_path" up -d db || { echo "setup-worktree: db 起動失敗" >&2; exit 1; }

# db healthy 待ち
wt_db_container="${project_name}-db"
echo "setup-worktree: waiting for $wt_db_container healthy" >&2
db_ready=0
for _ in $(seq 1 60); do
  if docker exec -e PGPASSWORD="$(read_env_value "$worktree_path/api/.env" POSTGRES_PASSWORD)" "$wt_db_container" \
       pg_isready -U "$(read_env_value "$worktree_path/api/.env" POSTGRES_USER)" -p "$postgres_port" >/dev/null 2>&1; then
    db_ready=1
    break
  fi
  sleep 1
done
[[ "$db_ready" -eq 1 ]] || { echo "setup-worktree: db が healthy にならない" >&2; exit 1; }

# Step 5: main DB を copy → alembic upgrade heads
copy_main_db_to_worktree "$worktree_path" "$parent_path" \
  || echo "setup-worktree: ⚠️ DB copy 失敗。空 DB で続行する (alembic で schema は作られる)" >&2

echo "setup-worktree: alembic upgrade heads (ブランチ分の migration を上乗せ)" >&2
worktree_compose "$worktree_path" run --rm api alembic upgrade heads \
  || echo "setup-worktree: ⚠️ alembic upgrade に失敗。'.../setup.sh' 再実行か手動 upgrade を検討しろ" >&2

# api / mailpit 起動
echo "setup-worktree: docker stack up (api mailpit)" >&2
worktree_compose "$worktree_path" up -d api mailpit || { echo "setup-worktree: api/mailpit 起動失敗" >&2; exit 1; }

# Step 6: banner
echo "setup-worktree: ============================================" >&2
echo "  ✅ worktree ready: $worktree_path" >&2
echo "     branch  : $branch" >&2
echo "     project : $project_name" >&2
echo "     API     : http://localhost:$uvicorn_port  (docker)" >&2
echo "     CLIENT  : http://localhost:$next_port      (bun run dev で起動)" >&2
echo "     POSTGRES: localhost:$postgres_port" >&2
echo "     MAILPIT : http://localhost:$mailpit_web_port" >&2
echo "  ℹ️  dev起動 : bash .claude/skills/worktree-dev-up/up.sh \"$worktree_path\"" >&2
echo "  ℹ️  後始末  : bash .claude/skills/setup-worktree/teardown.sh \"$worktree_path\"" >&2
echo "setup-worktree: ============================================" >&2

# stdout には 1 行で port を出す (呼び出し側 parse 用)
echo "PROJECT_NAME=$project_name NEXT_PORT=$next_port UVICORN_PORT=$uvicorn_port POSTGRES_PORT=$postgres_port"
