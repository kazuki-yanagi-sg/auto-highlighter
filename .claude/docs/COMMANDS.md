# カスタムコマンド一覧

このドキュメントは、プロジェクトで利用可能なすべてのカスタムコマンドの一覧です。

**総コマンド数**: 28

| カテゴリー | コマンド | 説明 |
|-----------|---------|------|
| Help | `/help` | ヘルプとコマンド一覧の表示 |
| CI | `/ci:fix-ci-error` | CI環境のエラーを自動修正 |
| Claude | `/claude:generate-command` | ベストプラクティスに従ったコマンド生成 |
| Claude | `/claude:refactor-rules` | CLAUDE.md自体のリファクタリング |
| Claude | `/claude:remove-command` | 不要なカスタムコマンドを安全に削除 |
| Claude | `/claude:validate-claude-config` | .claude/設定がClaude Codeの最新ベストプラクティスに準拠しているか検証 |
| Claude | `/claude:sync-commands` | 別プロジェクトのcustom commandと比較し、新規追加・更新されたものを同期 |
| Claude | `/claude:sync-skills` | 別プロジェクトのスキルと比較し、新規追加・更新されたものを同期 |
| Claude | `/claude:show-command-stats` | カスタムコマンドの使用統計を表示する |
| Deps | `/deps:grouping` | Dependabotグルーピング設定の自動生成 |
| Deps | `/deps:upgrade` | DependabotのPR処理と修正 |
| Dev | `/dev:check-diff-structure` | developとの差分ファイルが適切な場所に配置されているかをチェックし、類似ファイルとの比較で修正 |
| Dev | `/dev:check-rules` | CLAUDE.mdルール違反の検出と修正 |
| Dev | `/dev:create-design-doc` | 指定された画面の設計書を作成し、アカウント権限一覧を更新 |
| Dev | `/dev:refactor-safe` | 仕様を壊さない安全なリファクタリング |
| Dev | `/dev:refactor-thorough` | 徹底的な根本的リファクタリング（妥協なし） |
| Dev | `/dev:remove-excessive-comments` | 対応中ブランチで新規追加された過剰なdocstring/コメントを削除（必要最小限のみ残す） |
| Dev | `/dev:structure-check` | ドキュメント記載構造と実際のディレクトリ構造の整合性をチェックし、不整合を修正 |
| Dev | `/dev:coding-conventions` | Frontend/Backendコーディング規約の更新（既存コードパターンから自動検出） |
| Git | `/git:branch-status` | 現在のブランチの状況を包括的に把握する |
| Git | `/git:clean-branches` | マージ済みブランチの自動削除 |
| Git | `/git:merge-develop` | developの最新をcurrent branchにmerge |
| Git | `/git:review-analysis` | PRのレビュー内容を分析して見解をまとめる |
| Git | `/git:squash-commits` | ブランチのコミットを論理的にまとめてレビューしやすくする |
| Git | `/git:sync-stacked-branches` | Stacked PR構成のブランチに、developの最新変更を順次マージ・pushする |
| Issue | `/issue:create-claude-task` | claude-todosルールに基づいてタスクを体系的に管理 |
| Test | `/test:validate-quality` | テストの価値を評価し品質改善を実施（Google Testing Philosophy準拠） |
