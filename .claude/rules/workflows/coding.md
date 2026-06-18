# コーディングワークフロー

実装・リファクタの原則は `principles.md`、階層・命名は `frontend/architecture.md` / `backend/architecture.md`、環境変数・Python 直接実行などの禁止事項は `prohibitions.md` を参照。ここでは「ワークフロー固有の手順」だけ書く。

## エラー対応

### 根本原因の特定

1. エラーメッセージを正確に読む
2. 表面修正を繰り返さない
3. 段階的デバッグ

### 対応手順

1. 現状確認
2. 仮説設定（複数）
3. 実証テスト
4. 反証テスト
5. 根拠と共に結論

### 無限ループ・矛盾する指示

- チェックのチェックなど無限ループに陥ったら即座に相談
- 相反する要求（例: 「変更するな」と「更新しろ」）は解決案を提示

## ロール別 endpoints の追加（Backend）

新しい endpoint を作る時:

1. 対象ロール（`admin / manager / member / common`）を先に決める
2. `api/src/<domain>/endpoints/<role>/` に追加
3. ロールガード（`get_admin` / `get_manager` / `get_member`）を必ず付ける
4. 異なるロールを同一ファイルに混ぜない
5. URL prefix（`/api/v1/<role>/...`）を守る
