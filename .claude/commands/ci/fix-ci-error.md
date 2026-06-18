---
allowed-tools: [Bash, Read, Glob, Grep, Edit, MultiEdit, Write, TaskCreate, TaskUpdate, WebFetch]
description: PRのCIエラーを分析して自動修正
---

# CI エラー自動修正

PRのCIエラーを分析し、自動修正します。

## 引数の処理

引数: $ARGUMENTS

- 引数指定時: 特定のPR番号またはワークフローに限定
- 引数未指定時: 現在のブランチのPRのCIエラーを修正

## 実行フロー

1. **PR情報取得**: `gh pr status`でPR番号・CIステータス確認
2. **エラー分析**: ワークフローログから エラーパターン特定
3. **自動修正**: `./project_check.sh`でエラー再現・修正
4. **検証**: 修正後の全体チェック・動作確認
5. **commit & push**: 修正をコミット・プッシュ
6. **CI監視**: 以下のフローでCIが通るまで監視
   - ワークフロー実行開始を待機（最大5分）
   - CIステータスを30秒ごとにチェック
   - 成功: 完了報告
   - 失敗: ログ分析→修正→再push（最大3回まで試行）
   - タイムアウト: 手動確認を促す

## 使用方法

- `/ci:fix-ci-error` - 現在のブランチのPRのCIエラーを修正
- `/ci:fix-ci-error 123` - PR #123のCIエラーを修正
- `/ci:fix-ci-error client-test` - 特定ワークフローのエラーを修正

## カスタムコマンド共通仕様

@.claude/lib/common.md
