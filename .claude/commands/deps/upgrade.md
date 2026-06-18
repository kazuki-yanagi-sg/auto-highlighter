---
allowed-tools: [Bash, Read, Grep, Edit, MultiEdit, TaskCreate, TaskUpdate]
description: Dependabotプルリクエストの処理と必要な修正を実施
---

# Dependabot PR処理

Dependabotが作成したPRを処理し、必要な修正を実施。

## 引数の処理

引数: $ARGUMENTS

- `/deps:upgrade` - オープンなDependabot PRから選択
- `/deps:upgrade 123` - 特定のPR番号を処理

⚠️ **重要**: 複数のPRが存在する場合、1つのPRのみ処理して終了

## 実行フロー

1. **PR特定**: `gh pr list --author "app/dependabot"`でPR確認
   - 1つのPRを選択
   - `gh pr checkout <PR番号>`でローカルにチェックアウト

2. **最新developの取り込み**:
   - `git fetch origin develop`
   - `git merge origin/develop`でdevelopの最新をマージ
   - コンフリクトがあれば解決
   - **マージ後の依存関係のインストール**：
     - Frontend:
       - ローカル: `(cd client && bun install)`
       - Docker: Dockerは開発時未使用のため不要
     - Backend（両方必須）:
       - ローカル: `(cd api && uv sync --locked)`
       - Docker: `docker compose exec api uv sync --locked`
       - **重要**: ローカルとDocker両方で同期すること（テストはDocker内で実行するため）

3. **変更分析・調査**:
   - 更新パッケージと使用箇所を特定
   - 公式ドキュメントの最新情報を調査（WebSearch/WebFetch活用）
   - マイグレーション手順や破壊的変更を確認
   - 対処すべき内容を一通り洗い出し

4. **必要な修正**:
   - 3で取得した情報を1つずつ丁寧に対応
   - 設定ファイル調整、インポート文更新等
   - **Backend（API）の重要注意事項**:
     - Dependabotは`api/uv.lock`のみを更新することが多い
     - **⚠️ pyproject.tomlの最小バージョン要件も必ず更新する**:
       - `api/pyproject.toml`の該当パッケージの最小バージョンを新バージョンに合わせる
       - 例: `"pillow>=11.1.0"` → `"pillow>=12.0.0"`
       - **理由**: 古いバージョン指定が残ると、uv.lockとの不整合が発生し、将来的に問題を引き起こす
     - **pyproject.toml更新後、`uv lock`で`uv.lock`を再生成**
     - **ローカルとDocker両方で依存関係をインストール**:
       - ローカル: `(cd api && uv sync --locked)`
       - Docker: `docker compose exec api uv sync --locked`
   - **Frontend（Client）の重要注意事項**:
     - Dependabotは`client/package.json`と`client/bun.lock`を更新
     - **⚠️ 最小バージョン要件が古くなっていないか確認**:
       - `client/package.json`の該当パッケージのバージョン指定を確認
       - 必要に応じて更新（例: `"react": "^18.2.0"` → `"react": "^19.0.0"`）

5. **Lint・Test実行（必須）**:
   - **Lint実行**:
     - Frontend更新: `./project_check.sh --client-lint`
     - Backend更新: `./project_check.sh --api-lint`
     - エラー・Warningがあれば修正して再実行
   - **Test実行**:
     - Frontend更新: `bun run test`
     - Backend更新: `docker compose exec api uv run pytest`（Docker内で実行）
       - asdfの干渉を避けるためDocker内でテストを実行する
     - エラー・Warningがあれば修正して再実行
   - **全てPASS・Warning無しになるまで繰り返す**（これを怠るとPRがマージできない）

6. **CI/CD設定のチェック（重要）**:
   - ⚠️ **依存関係更新時はCI/CD設定も同期更新が必要**
   - **チェック対象**: `.github/workflows/*.yml`、`Dockerfile`、`docker-compose.yml`、`package.json`（engines）、`pyproject.toml`（requires-python）
   - **例**: TypeScript/Pythonのメジャー更新時は、CI内のNode.js/Pythonバージョン、Dockerfileも要確認・更新
   - **確認**: 公式ドキュメントで要求バージョン確認 → CI/CD設定ファイル検索 → 必要に応じて更新
   - **⚠️ 型定義パッケージ（@types/*）の同期更新**:
     - 本体パッケージのメジャーバージョン更新時、対応する`@types/*`も同時に更新すること
     - 主な対象:
       - `@types/node` ← Node.js（`engines.node`）のメジャーバージョンと同期（Dependabot無視設定済み）
       - `@types/react` ← `react`のメジャーバージョンと同期
       - `@types/react-dom` ← `react-dom`のメジャーバージョンと同期
     - 更新箇所: `client/package.json`の該当`@types/*`を本体バージョンに合わせる

7. **PR更新**:
   - 依存関係のインストール内容（lock file等）と修正内容をcommit
   - `git push`でcheckoutしたPRブランチにpush
   - `gh pr view --web`でブラウザを開いて確認

## 使用方法

- `/deps:upgrade` - オープンなDependabot PRから選択
- `/deps:upgrade 456` - 特定のPRを処理

## カスタムコマンド共通仕様

@.claude/lib/common.md
