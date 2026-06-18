---
category: git
description: PRのレビュー内容を分析して見解をまとめる
created: 2025-11-15
author: claude
version: 1.0.0
---

# git:review-analysis

## 概要

現在のブランチのPRを特定し、レビューコメントを全て確認・分析して、対応方針の見解をまとめます。

## 目的

- PRのレビューコメントを網羅的に把握
- コメントの分類と優先度付け
- 対応状況の確認
- 対応方針の提案と見解報告

## 使用方法

```bash
/git:review-analysis
```

## 実行フロー

### 1. ブランチとPRの特定

```bash
# 現在のブランチ名を取得
git branch --show-current

# PRを検索
gh pr list --head <current-branch> --json number,title,state,baseRefName
```

### 2. レビュー情報の取得

```bash
# PRのレビュー全体を取得
gh pr view <pr-number> --json reviews,reviewRequests,comments

# レビューコメントの詳細を取得
gh api repos/{owner}/{repo}/pulls/{pr}/reviews

# レビューコメント（コード上のコメント）を取得
gh api repos/{owner}/{repo}/pulls/{pr}/comments
```

**取得する情報**:
- レビューステータス（APPROVED/CHANGES_REQUESTED/COMMENTED）
- レビュアー
- レビューコメント内容
- コード上の具体的なコメント
- コメントの投稿日時

### 3. 差分の統計情報

```bash
# 変更ファイルの統計
git diff origin/<base-branch>...HEAD --stat

# 変更ファイル数のカウント
git diff origin/<base-branch>...HEAD --name-only | wc -l

# 追加・削除行数の集計
git diff origin/<base-branch>...HEAD --numstat
```

**出力例**:
```
📊 変更統計

変更ファイル数: 23ファイル
追加行数: 1,234行
削除行数: 456行

主な変更領域:
- client/src/components/: 15ファイル
- api/src/routes/: 5ファイル
- tests/: 3ファイル
```

### 4. コミット履歴の確認

```bash
# コミット一覧を表示
git log origin/<base-branch>..HEAD --oneline --decorate

# コミット数をカウント
git log origin/<base-branch>..HEAD --oneline | wc -l
```

**出力例**:
```
📝 コミット履歴（12個のコミット）

80d36f7 feat: change consignee address max length from 50 to 60 chars
faec0e4 chore: update command statistics
ab28719 chore: update command statistics
de9466282 fix: update test expectations for new error handling spec
1841cccdc feat: add error CSV download for consignee upload validation
...
```

### 5. レビューコメントの分類

**分類軸**:

1. **種類**:
   - 必須対応（CHANGES_REQUESTED）
   - 提案・改善案（COMMENTED）
   - 承認済み（APPROVED）

2. **カテゴリ**:
   - セキュリティ
   - パフォーマンス
   - コード品質
   - テスト
   - ドキュメント
   - 設計・アーキテクチャ
   - その他

3. **優先度**（推測）:
   - 高：セキュリティ、重大なバグ、設計の根本的な問題
   - 中：パフォーマンス、コード品質、テスト不足
   - 低：ドキュメント、軽微な改善提案

### 6. 対応状況の確認

各コメントについて、以下を確認：
- 対応済みか未対応か
- 対応が必要か不要か（議論中含む）
- 対応する場合の方針

**確認方法**:
```bash
# 最新のコミット以降の変更を確認
git log --since="<レビュー投稿日時>" --oneline

# レビューコメントで指摘されたファイルの現状確認
git diff origin/<base-branch>...HEAD -- <指摘されたファイル>
```

### 7. 見解のまとめと報告

すべての情報を分析した後、以下の形式で簡潔に報告します。

**報告フォーマット**:

```markdown
# レビュー分析レポート

## 基本情報
- PR #123: Add user authentication feature
- レビュアー: @reviewer1, @reviewer2
- レビューステータス: CHANGES_REQUESTED

## 変更統計
- 23ファイル変更、12コミット
- +1,234行 / -456行

## レビュー概要
- 総コメント数: 15件
- 必須対応: 5件
- 提案・改善案: 8件
- 承認済み: 2件

## 必須対応事項（優先度順）

### 高優先度（3件）
1. **セキュリティ**: JWT_SECRET_KEYのハードコーディング → 環境変数化が必要
2. **設計**: 認証ミドルウェアのエラーハンドリング不足 → try-catch追加
3. **バグ**: トークンリフレッシュのロジックエラー → 修正必要

### 中優先度（2件）
1. **テスト**: 異常系のテストケース不足 → テスト追加
2. **パフォーマンス**: N+1クエリの発生 → クエリ最適化

## 提案・改善案（対応検討）

### 対応推奨（3件）
1. **コード品質**: マジックナンバーの定数化 → constants.tsに移動
2. **可読性**: 長い関数の分割 → リファクタリング推奨
3. **ドキュメント**: API仕様のコメント追加 → 追加推奨

### 対応任意（5件）
1. 変数名の改善提案（user → currentUser）
2. importの順序整理
3. コメントの追加提案
4. ファイル構成の見直し提案
5. 型定義の改善提案

## 対応方針

### 即座に対応すべき
- セキュリティ、設計、バグの3件を最優先で修正
- 修正後、レビュアーに再レビュー依頼

### 次のステップで対応
- テスト追加、パフォーマンス改善は修正完了後に対応
- 対応推奨の改善案も可能な範囲で実施

### 議論が必要
- 設計の見直し提案については、レビュアーと議論してから判断
```

## エラーハンドリング

### PRが見つからない場合

```
⚠️ PRが見つかりません

【対処法】
1. PRを作成: `gh pr create`
2. リモートにpush: `git push -u origin <branch>`
3. ブランチ名を確認: `git branch --show-current`
```

### レビューが存在しない場合

```
⚠️ このPRにはまだレビューがありません

【状況】
- レビューリクエストは送信済み
- レビュー待ちの状態

【次のアクション】
- レビュアーにリマインド
- または、セルフレビューを実施
```

### レビューコメントが大量の場合

```
⚠️ レビューコメントが非常に多いです（50件以上）

【対応】
1. 優先度の高いコメントから順に分析
2. カテゴリ別に整理して段階的に対応
3. レビュアーと対応方針を相談することを推奨
```

## 使用例

### 例1: 通常のレビュー分析

```bash
/git:review-analysis
```

**実行結果**:
```
✅ PR情報を取得しました

PR #123: Add user authentication feature
レビュアー: @reviewer1, @reviewer2

📊 レビューコメントを取得中...
総コメント数: 15件

📝 コメントを分析中...
必須対応: 5件
提案・改善案: 8件
承認済み: 2件

✅ 分析完了

【優先対応が必要】
高優先度: セキュリティ、設計、バグで3件
中優先度: テスト、パフォーマンスで2件

【推奨対応】
コード品質改善で3件

【対応方針】
まず高優先度の3件を修正し、再レビュー依頼を推奨
```

### 例2: APPROVED状態のPR

```bash
/git:review-analysis
```

**実行結果**:
```
✅ PR情報を取得しました

PR #456: Fix login bug
レビュアー: @reviewer1

📊 レビューステータス: APPROVED

【レビュー結果】
- 承認済み
- コメント数: 2件（軽微な改善提案のみ）

【対応方針】
改善提案は任意対応。マージ可能な状態です。
```

## 注意事項

### 実行前の確認

- [ ] PRが作成済み
- [ ] レビューリクエストが送信済み
- [ ] ghコマンドがインストール済み

### 分析の精度

- **優先度判断は推測**: 実際の優先度はレビュアーに確認すること
- **対応状況の判断**: コミット履歴から推測するため、完全ではない
- **議論中のコメント**: スレッドの全文を確認して判断する

### 報告の活用

- レビュー対応の計画立案に活用
- レビュアーとのコミュニケーションの補助
- 対応漏れの防止

## ベストプラクティス

### 定期的な確認

- レビューコメントが追加されたら実行
- 対応完了後、再度実行して確認
- 再レビュー前に実行して対応漏れチェック

### 他のコマンドとの組み合わせ

```bash
# ブランチ状況確認 → レビュー分析 → 修正 → 再レビュー
/git:branch-status
/git:review-analysis
# 修正作業
/git:review-analysis  # 再確認
```

### レビュアーとのコミュニケーション

- 優先度や対応方針について不明な点は、レビュアーに質問
- 大規模な修正が必要な場合は、事前に方針を相談
- 議論が必要なコメントは、PR上で返信して議論

## 関連コマンド

- `/git:branch-status` - ブランチ状況の把握
- `/git:merge-develop` - developの最新をマージ

## カスタムコマンド共通仕様

@.claude/lib/common.md
