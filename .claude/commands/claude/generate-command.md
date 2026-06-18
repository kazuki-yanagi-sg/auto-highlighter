---
allowed-tools: [Read, Write, Grep, Glob, LS, WebSearch, TaskCreate, TaskUpdate, Bash, Edit, MultiEdit]
description: ユーザーの要望を分析してベストプラクティスに従ったカスタムコマンドを生成
---

# カスタムコマンド生成

ユーザーの要望を分析し、2025年のベストプラクティスに従ったカスタムコマンドを自動生成します。

## 引数の処理

引数: $ARGUMENTS

- 引数指定時: その要望でコマンド生成
- 引数未指定時: 会話履歴から要望抽出

## 実行フロー

1. **要望分析**
   - ユーザー要望の理解
   - 必要機能の特定
   - カテゴリ選択（ci, deps, dev, git, help, issue, test）
   - コマンド名決定（category:action形式）

2. **既存確認**
   - 類似コマンドの検索
   - registry.jsonで重複チェック

3. **コマンド生成**
   - YAMLフロントマター作成
   - 引数処理セクション
   - 実行内容の構造化
   - 使用例の追加

4. **品質チェック**
   - namespace形式の確認
   - 必要ツールの妥当性
   - MECE原則の適用

5. **保存と登録**
   - ファイル保存（.claude/commands/category/action.md）
   - registry.json更新
   - 統計情報の更新
   - .claude/docs/COMMANDS.md更新（新規コマンドの説明追加）

## 使用方法

- `/claude:generate-command "要望内容"` - 指定要望でコマンド生成
- `/claude:generate-command` - 会話履歴から要望抽出して生成

## カスタムコマンド共通仕様

@.claude/lib/common.md
