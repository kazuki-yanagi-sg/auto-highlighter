#!/usr/bin/env bash
# Worktree env / port 計算ライブラリ。
#
# 役割:
#   - branch slug の SHA-256 hash から worktree 専用ポートを deterministic 採番
#   - main の 3 つの .env (root / api / client) をベースに worktree 専用 .env を生成
#   - worktree 専用の docker stack project 名を算出
#   - main の docker Postgres から worktree DB へデータをコピー
#
# 採番設計 (既存クローン並列が 1/2/4 万番台を使うため 6 万番台に固定):
#   NEXT_PORT          60000-60999
#   UVICORN_PORT       61000-61999
#   POSTGRES_PORT      62000-62999
#   MAILPIT_SMTP_PORT  63000-63999
#   MAILPIT_WEB_PORT   64000-64999
#
#   いずれも TCP 上限 65535 未満。pgAdmin は worktree では起動しないため採番しない。
#
# 設計方針:
#   - 関数で失敗を返す場合は `return 1` を使い、source 元シェルを壊さない
#   - エラーメッセージはすべて stderr。stdout は値のみに保つ (eval / capture 用)
#   - docker compose 実行時は critical var を shell export してから呼び、
#     compose の .env 補間機構 (include ごとに自ディレクトリ .env を読む) の曖昧さを排除する

set -uo pipefail

# ─────────────────────────────────────────
# slug / port / project 名計算
# ─────────────────────────────────────────

# branch 名から DB / file 名に安全な slug を作る
# ex: "feature/foo-bar.baz" → "feature_foo_bar_baz"
slugify_branch() {
  local input="${1:-}"
  if [[ -z "$input" ]]; then
    echo "setup-worktree/lib: slugify_branch: 第 1 引数 branch が必須" >&2
    return 1
  fi
  printf '%s' "$input" \
    | tr '[:upper:]' '[:lower:]' \
    | sed 's/[^a-z0-9]/_/g' \
    | sed 's/__*/_/g' \
    | sed 's/^_//;s/_$//'
}

# SHA-256 hash の先頭 7 hex を取り、base + (hash mod 1000) を port として返す。
# salt で port 種別を分離する (同一 slug でも種別ごとに別 port になる)。
compute_port() {
  local slug="${1:-}"
  local base="${2:-}"
  local salt="${3:-}"
  if [[ -z "$slug" || -z "$base" || -z "$salt" ]]; then
    echo "setup-worktree/lib: compute_port: slug / base / salt が必須" >&2
    return 1
  fi
  local hex
  hex=$(printf '%s:%s' "$slug" "$salt" | shasum -a 256 | cut -c1-7)
  local n=$((0x${hex} % 1000))
  echo $((base + n))
}

# slug から worktree の docker project 名 (PROJECT_NAME / COMPOSE_PROJECT_NAME 共用) を返す。
# compose の project 名は [a-z0-9_-] のみ許容。slug は既に小文字 + _ なので prefix を付けるだけ。
compute_project_name() {
  local slug="${1:-}"
  if [[ -z "$slug" ]]; then
    echo "setup-worktree/lib: compute_project_name: 第 1 引数 slug が必須" >&2
    return 1
  fi
  echo "senri-wt-${slug}"
}

# ─────────────────────────────────────────
# main_repo_root
# ─────────────────────────────────────────
# worktree path から main worktree (リポジトリ root) の絶対 path を解決する。
# `git worktree list` の先頭エントリが常に main worktree であることを利用。
main_repo_root() {
  local worktree_path="${1:-}"
  if [[ -z "$worktree_path" ]]; then
    echo "setup-worktree/lib: main_repo_root: 第 1 引数 worktree_path が必須" >&2
    return 1
  fi
  local root
  root=$(git -C "$worktree_path" worktree list 2>/dev/null | head -n 1 | awk '{print $1}')
  if [[ -z "$root" || ! -d "$root" ]]; then
    echo "setup-worktree/lib: main_repo_root: 解決失敗 (root='$root')" >&2
    return 1
  fi
  echo "$root"
}

# ─────────────────────────────────────────
# .env 生成
# ─────────────────────────────────────────
# senri は root / api / client の 3 つの独立した .env を持つ。
# worktree では gitignore されたこれらを「ポート行のみ書き換えコピー」で再生成する。
# URL 派生値 (DATABASE_URL / CORS_ORIGINS / NEXT_PUBLIC_API_ORIGIN_URL 等) は
# 基本 ${VAR} 参照なので port 行を変えれば自動追従する。例外 (client の DATABASE_URL の
# host port 直書き) のみ個別に書き換える。

# 1 行を「KEY= の値だけ差し替え」て echo する補助 (行末コメントは保持しない)。
_rewrite_line() {
  local line="$1" key="$2" value="$3"
  case "$line" in
    "${key}="*) echo "${key}=${value}" ;;
    *) echo "$line" ;;
  esac
}

# root .env を生成する。
write_root_env() {
  local worktree_path="$1" parent_path="$2" project_name="$3" next_port="$4" uvicorn_port="$5"
  local src="$parent_path/.env" dst="$worktree_path/.env"
  if [[ ! -f "$src" ]]; then
    echo "setup-worktree/lib: parent root .env が無い: $src" >&2
    return 1
  fi
  [[ -e "$dst" ]] && rm -f "$dst"

  local has_compose_name=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      NEXT_PORT=*) echo "NEXT_PORT=$next_port" ;;
      UVICORN_PORT=*) echo "UVICORN_PORT=$uvicorn_port" ;;
      PROJECT_NAME=*) echo "PROJECT_NAME=\"$project_name\"" ;;
      COMPOSE_PROJECT_NAME=*) echo "COMPOSE_PROJECT_NAME=$project_name"; has_compose_name=1 ;;
      *) echo "$line" ;;
    esac
  done < "$src" > "$dst"

  if [[ "$has_compose_name" -eq 0 ]]; then
    echo "COMPOSE_PROJECT_NAME=$project_name" >> "$dst"
  fi
  echo "setup-worktree/lib: wrote $dst (NEXT_PORT=$next_port UVICORN_PORT=$uvicorn_port PROJECT_NAME=$project_name)" >&2
}

# api/.env を生成する。port 行のみ書き換え (URL 類は ${VAR} 参照で自動追従)。
write_api_env() {
  local worktree_path="$1" parent_path="$2" uvicorn_port="$3" postgres_port="$4" mailpit_smtp_port="$5" mailpit_web_port="$6"
  local src="$parent_path/api/.env" dst="$worktree_path/api/.env"
  if [[ ! -f "$src" ]]; then
    echo "setup-worktree/lib: parent api/.env が無い: $src" >&2
    return 1
  fi
  mkdir -p "$worktree_path/api"
  [[ -e "$dst" ]] && rm -f "$dst"

  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      UVICORN_PORT=*) echo "UVICORN_PORT=$uvicorn_port" ;;
      POSTGRES_PORT=*) echo "POSTGRES_PORT=$postgres_port" ;;
      MAILPIT_SMTP_PORT=*) echo "MAILPIT_SMTP_PORT=$mailpit_smtp_port" ;;
      MAILPIT_WEB_PORT=*) echo "MAILPIT_WEB_PORT=$mailpit_web_port" ;;
      *) echo "$line" ;;
    esac
  done < "$src" > "$dst"
  echo "setup-worktree/lib: wrote $dst (UVICORN_PORT=$uvicorn_port POSTGRES_PORT=$postgres_port)" >&2
}

# client/.env を生成する。port 行 + DATABASE_URL の host port 直書きを書き換える。
write_client_env() {
  local worktree_path="$1" parent_path="$2" uvicorn_port="$3" postgres_port="$4"
  local src="$parent_path/client/.env" dst="$worktree_path/client/.env"
  if [[ ! -f "$src" ]]; then
    echo "setup-worktree/lib: parent client/.env が無い: $src" >&2
    return 1
  fi
  mkdir -p "$worktree_path/client"
  [[ -e "$dst" ]] && rm -f "$dst"

  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      UVICORN_PORT=*) echo "UVICORN_PORT=$uvicorn_port" ;;
      POSTGRES_PORT=*) echo "POSTGRES_PORT=$postgres_port" ;;
      DATABASE_URL=*)
        # Prisma 用。host は local 実行なので localhost:<port> 形式の直書き port を差し替える。
        echo "$line" | sed -E "s#(@localhost:)[0-9]+(/)#\1${postgres_port}\2#"
        ;;
      *) echo "$line" ;;
    esac
  done < "$src" > "$dst"
  echo "setup-worktree/lib: wrote $dst (UVICORN_PORT=$uvicorn_port POSTGRES_PORT=$postgres_port)" >&2
}

# 3 つの .env を一括生成する。
write_worktree_envs() {
  local worktree_path="$1" parent_path="$2" project_name="$3"
  local next_port="$4" uvicorn_port="$5" postgres_port="$6" mailpit_smtp_port="$7" mailpit_web_port="$8"
  write_root_env "$worktree_path" "$parent_path" "$project_name" "$next_port" "$uvicorn_port" || return 1
  write_api_env "$worktree_path" "$parent_path" "$uvicorn_port" "$postgres_port" "$mailpit_smtp_port" "$mailpit_web_port" || return 1
  write_client_env "$worktree_path" "$parent_path" "$uvicorn_port" "$postgres_port" || return 1
}

# ─────────────────────────────────────────
# .env 値の読み取り
# ─────────────────────────────────────────
# KEY= 行の値 (行末コメント・引用符を除去) を返す。
read_env_value() {
  local env_file="${1:-}" key="${2:-}"
  if [[ -z "$env_file" || -z "$key" ]]; then
    echo "setup-worktree/lib: read_env_value: env_file / key が必須" >&2
    return 1
  fi
  grep -E "^${key}=" "$env_file" 2>/dev/null | tail -n 1 \
    | sed -E "s/^${key}=//; s/[[:space:]]+#.*$//; s/^\"(.*)\"$/\1/; s/^'(.*)'$/\1/"
}

# ─────────────────────────────────────────
# docker stack helper
# ─────────────────────────────────────────
# worktree の docker compose を「critical var を shell export してから」実行する。
# 第 1 引数 = worktree_path、以降 = docker compose に渡す引数。
worktree_compose() {
  local worktree_path="${1:-}"; shift || true
  if [[ -z "$worktree_path" ]]; then
    echo "setup-worktree/lib: worktree_compose: 第 1 引数 worktree_path が必須" >&2
    return 1
  fi
  local root_env="$worktree_path/.env" api_env="$worktree_path/api/.env"

  local project_name next_port uvicorn_port postgres_version
  local postgres_port mailpit_smtp_port mailpit_web_port pgadmin_port
  project_name=$(read_env_value "$root_env" PROJECT_NAME)
  next_port=$(read_env_value "$root_env" NEXT_PORT)
  uvicorn_port=$(read_env_value "$api_env" UVICORN_PORT)
  postgres_port=$(read_env_value "$api_env" POSTGRES_PORT)
  postgres_version=$(read_env_value "$api_env" POSTGRES_VERSION)
  mailpit_smtp_port=$(read_env_value "$api_env" MAILPIT_SMTP_PORT)
  mailpit_web_port=$(read_env_value "$api_env" MAILPIT_WEB_PORT)
  pgadmin_port=$(read_env_value "$api_env" PGADMIN_PORT)

  PROJECT_NAME="$project_name" \
  COMPOSE_PROJECT_NAME="$project_name" \
  NEXT_PORT="$next_port" \
  UVICORN_PORT="$uvicorn_port" \
  POSTGRES_VERSION="$postgres_version" \
  POSTGRES_PORT="$postgres_port" \
  MAILPIT_SMTP_PORT="$mailpit_smtp_port" \
  MAILPIT_WEB_PORT="$mailpit_web_port" \
  PGADMIN_PORT="$pgadmin_port" \
    docker compose --project-directory "$worktree_path" -p "$project_name" "$@"
}

# ─────────────────────────────────────────
# DB コピー (main → worktree)
# ─────────────────────────────────────────
# main の Postgres コンテナから pg_dump し、worktree の Postgres コンテナへ流し込む。
# DB / USER / PASSWORD は同一前提 (port のみ異なる)。
# main コンテナ名は ${main PROJECT_NAME}-db (api/docker-compose.yml の container_name)。
copy_main_db_to_worktree() {
  local worktree_path="${1:-}" parent_path="${2:-}"
  if [[ -z "$worktree_path" || -z "$parent_path" ]]; then
    echo "setup-worktree/lib: copy_main_db_to_worktree: worktree_path / parent_path が必須" >&2
    return 1
  fi

  local main_db main_user main_pass main_pgport main_project
  main_db=$(read_env_value "$parent_path/api/.env" POSTGRES_DB)
  main_user=$(read_env_value "$parent_path/api/.env" POSTGRES_USER)
  main_pass=$(read_env_value "$parent_path/api/.env" POSTGRES_PASSWORD)
  main_pgport=$(read_env_value "$parent_path/api/.env" POSTGRES_PORT)
  main_project=$(read_env_value "$parent_path/.env" PROJECT_NAME)
  local main_container="${main_project}-db"

  local wt_project wt_pgport
  wt_project=$(read_env_value "$worktree_path/.env" PROJECT_NAME)
  wt_pgport=$(read_env_value "$worktree_path/api/.env" POSTGRES_PORT)
  local wt_container="${wt_project}-db"

  if ! docker ps --format '{{.Names}}' | grep -qx "$main_container"; then
    echo "setup-worktree/lib: main DB コンテナ '$main_container' が起動していない。main で docker compose up しろ" >&2
    return 1
  fi
  if ! docker ps --format '{{.Names}}' | grep -qx "$wt_container"; then
    echo "setup-worktree/lib: worktree DB コンテナ '$wt_container' が起動していない" >&2
    return 1
  fi

  echo "setup-worktree/lib: DB copy $main_container:$main_pgport → $wt_container:$wt_pgport ($main_db)" >&2
  if docker exec -e PGPASSWORD="$main_pass" "$main_container" \
       pg_dump -U "$main_user" -p "$main_pgport" -d "$main_db" --no-owner --no-privileges \
     | docker exec -i -e PGPASSWORD="$main_pass" "$wt_container" \
       psql -U "$main_user" -p "$wt_pgport" -d "$main_db" -v ON_ERROR_STOP=0 >/dev/null; then
    echo "setup-worktree/lib: DB copy 完了" >&2
  else
    echo "setup-worktree/lib: DB copy 失敗" >&2
    return 1
  fi
}
