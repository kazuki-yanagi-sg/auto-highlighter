---
name: aws-environment-investigation
description: AWS環境（development / preview / production）の状態・データを読み取り専用で調査する。AWS CLI（プロファイル senri-core-system）と ECS Exec 経由のDBクエリを使う。「本番調査」「AWS確認」「ECS exec」「DB状態確認」「データ確認」「環境調査」「production調査」「preview確認」などのキーワードで使用。
---

# AWS環境調査スキル

AWS の3環境（development / preview / production）の状態・データを調査するためのスキル。

## プロジェクト固有の情報

- **AWS CLIプロファイル**: `senri-core-system`（`--profile senri-core-system` を指定）

  ```bash
  aws --profile senri-core-system sts get-caller-identity
  ```
- **環境**: `development` / `preview` / `production`
- **ECS Exec スクリプト**: `./api/scripts/ecs/exec.sh -e <environment>` で環境切替（詳細は `api/scripts/ecs/README.md`）
- **DB接続方法**: ECS Exec で API コンテナに入り、`python`（PATH=/workdir/.venv/bin:$PATH が通っているので venv の python が直接呼ばれる）から SQLAlchemy で `os.environ['DATABASE_URL']` に接続してクエリを投げる。本番 image には uv が含まれない設計のため `uv run` は使わない。

  ```bash
  ./api/scripts/ecs/exec.sh -e <environment> -m "python -c \"from sqlalchemy import create_engine, text; import os; e = create_engine(os.environ['DATABASE_URL']); c = e.connect(); r = c.execute(text('SELECT id, name, system_code FROM consignors LIMIT 10')); print([dict(row._mapping) for row in r]); c.close()\""
  ```

## スコープ

- このスキルの責務は **調査・確認まで**
- 修正対応はユーザーから別途依頼があった時のみ着手する
- 結果は **事実と仮説を分けて** 報告する

## やってはいけないこと（明示依頼がない限り絶対実行しない）

- DBへの変更系操作
- マイグレーション・シード投入
- AWS リソース・設定の変更（ECS / IAM / Secrets / Parameter Store / S3 等）
- ECSタスクの停止・再起動・強制再デプロイ
- 調査スコープを超えた修正

## やるべきこと

- AWS CLI 実行時は `--profile senri-core-system` を指定
- 対象環境を `-e` フラグで明示
- 読み取り専用のクエリ・コマンドのみ使用
- 変更系の操作が必要だと判断した場合は、**実行前にユーザー承認を得る**
