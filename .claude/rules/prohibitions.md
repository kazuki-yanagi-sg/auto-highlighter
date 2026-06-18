# 絶対にやってはいけないこと（最重要）

本プロジェクトで絶対に違反してはならない項目。違反は重大な問題を引き起こす。

## 1. develop / main への直接 push

- 必ず feature ブランチ経由で PR 作成
- 直接 push は本番環境への影響リスク大

## 2. `cp` での `.env` 生成

```bash
# ❌ 絶対にやってはいけない
cp .env.sample .env

# ✅ 必ずこれを使用
sh project_check.sh -e
```

## 3. 認証情報の値変更

- `CLIENT_ID` / `CLIENT_SECRET` / `JWT_SECRET_KEY` 等の値を変更するな
- `.env` は環境ごとに値が違う。sample にある値で勝手に上書きするな
- ローカル開発用デフォルト（`admin0@example.com` / `member1@example.com` / `Password1@`）も勝手に変えるな

## 4. ユーザーの指示を鵜呑みにして確認せずに答える

- ユーザーも間違える可能性がある
- 必ず実際のコード・ファイル・状況を確認
- 「その通りです」などの安易な同意は厳禁
- 事実に基づいた確認結果のみを報告

## 5. 対症療法による問題の隠蔽

- 必ず根本解決を行う
- エラーを無視・回避するのではなく、根本原因を特定・解決
- セキュリティチェックのスキップは禁止
- 一時的な回避策の場合は、必ず根本解決への道筋を示す

## コード編集関連

- 保護ディレクトリ（自動生成物: `client/src/api/`, `client/src/generated/`, `client/src/components/shadcn/` 等）の編集禁止
- `api/alembic/versions/` の手動編集禁止（必ず autogenerate）
- **コメントは TODO と運用ルールのみ許可**（コードで明らかなことは書くな）
  - 運用ルール = コードからは読み取れない業務・運用上の判断（なぜこの仕様にしたか）
  - 運用ルールを記載する場合のみコメントを許可しろ
- ポート番号のハードコーディング禁止（`.env` の `NEXT_PORT` / `UVICORN_PORT` 等を使う）

## Git 関連

- `git commit --no-verify` での hook 回避禁止
- `project_check.sh` でエラーが出たら必ず修正
- lint / 型 / テストエラーを無視するな
- worktree は `.claude/worktrees/` 配下に作り `setup-worktree` skill で環境分離する（`CLAUDE.local.md` 参照）

## Python 実行関連

- **Python ツールの直接実行禁止**（`mypy`, `pytest`, `ruff`, `black` 等）
  - ❌ `mypy .` → ✅ `uv run mypy .`
  - ❌ `pytest` → ✅ `uv run pytest`
  - ❌ `ruff check` → ✅ `uv run ruff check`
- 理由: asdf シムの問題を回避し、正しい仮想環境を確実に使用

## TypeScript 関連（IMPORTANT）

- **`as` cast 禁止** → 型安全に書け（`as const` は許可）
- **`any` 型禁止**
- ESLint で自動検出

## プロジェクト管理関連

- `CLAUDE.md` / `.claude/rules/` は依頼がない限り編集・コミットするな

## 違反時の対処

1. 即座に作業を停止
2. 違反内容を認識・報告
3. 正しい方法で再実装
4. 根本原因を分析して再発防止
