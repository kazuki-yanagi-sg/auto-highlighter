---
allowed-tools: [Bash, TaskCreate, TaskUpdate]
description: オリジンに存在しないローカルブランチ・CLOSEDなPRのブランチを自動識別・削除
---

# ブランチクリーンアップ

不要なローカルブランチを安全に削除します。

## 引数の処理

引数: $ARGUMENTS

- 全ての不要ブランチを自動削除（引数は無視）

## 削除対象

1. **`[gone]`ブランチ**: リモートで削除済み（`git branch -vv`で`[gone]`マーク付き）
2. **CLOSED PRブランチ**: PRが未マージで閉じられたブランチ（`gh pr list --state closed`で確認）

## 実行フロー

1. **リモート同期**: `git fetch --prune`でリモート情報を更新
2. **ブランチ状況確認**: `git branch -vv`で追跡状況確認
3. **`[gone]`ブランチ特定**: リモートが削除されたブランチを収集
4. **CLOSED PRブランチ特定**: develop以外の各ローカルブランチについて`gh pr list --head {branch} --state all`でPR状態を確認し、PRが全てCLOSED（未マージ）のブランチを収集
5. **削除対象の報告**: 削除対象ブランチ一覧とその理由（gone/CLOSED PR）を表示
6. **安全削除**: `git branch -D`で削除実行

## 使用方法

- `/git:clean-branches` - 不要な全ローカルブランチを削除

## カスタムコマンド共通仕様

@.claude/lib/common.md

## ⚠️ 重要な注意事項

**このコマンドは統計ファイルの更新を行いません（例外コマンド）**

### 理由

- このコマンドはブランチがクリーンな状態でのみ使用するコマンド
- 統計ファイル更新のためだけにPR作成が必要になることを避けるため
- ブランチクリーンアップという性質上、他の変更と混在させるべきではない

そのため、`git add .claude/command-stats.json`およびcommit・pushは**一切行いません**。
