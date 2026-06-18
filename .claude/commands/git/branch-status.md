---
category: git
description: 現在のブランチの状況を包括的に把握する
created: 2025-11-15
author: claude
version: 1.0.0
---

# git:branch-status

## 概要

現在のブランチのPR情報と親ブランチとの差分を詳細に分析し、ブランチの目的と全体像を把握します。

## 目的

- 現在のブランチに紐づくPRを特定
- 親ブランチとの差分を徹底的に確認（修正が多くても手抜きなし）
- ブランチの目的と変更内容の全体像を整理して説明

## 使用方法

```bash
/git:branch-status
```

## 実行フロー

### 1. 現在のブランチ確認

```bash
# 現在のブランチ名を取得
git branch --show-current
```

**出力例**:
```
feature/add-authentication
```

### 2. PR情報の取得

```bash
# 現在のブランチに紐づくPRを検索
gh pr list --head <current-branch> --json number,title,state,baseRefName,headRefName
```

**確認内容**:
- PR番号
- PRタイトル
- PR状態（OPEN/CLOSED/MERGED）
- ベースブランチ（親ブランチ）
- ヘッドブランチ（現在のブランチ）

**PRが見つからない場合**:
```
⚠️ このブランチに紐づくPRが見つかりません

【考えられる原因】
- PRがまだ作成されていない
- ブランチ名が一致していない
- リモートにpushされていない

【対処法】
1. `gh pr create` でPRを作成
2. `git push -u origin <branch>` でリモートにpush
3. ブランチ名を確認
```

**PRが見つかった場合**:
```
✅ PR情報

PR番号: #123
タイトル: Add user authentication feature
状態: OPEN
親ブランチ: develop
```

### 3. 親ブランチの最新を取得

```bash
# 親ブランチの最新を取得
git fetch origin <base-branch>
```

### 4. 差分の統計情報

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

### 5. コミット履歴の確認

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

### 6. 変更ファイルの詳細分析

**重要**: 修正が多い場合でも手抜きせず、すべてのファイルを確認します。

```bash
# 変更されたファイルの一覧を取得
git diff origin/<base-branch>...HEAD --name-status
```

**ファイルステータスの意味**:
- `M`: Modified（変更）
- `A`: Added（追加）
- `D`: Deleted（削除）
- `R`: Renamed（名前変更）
- `C`: Copied（コピー）

**分析手順**:

1. **カテゴリ別に分類**:
   ```
   フロントエンド（client/）:
   - M client/src/components/Auth/LoginForm.tsx
   - A client/src/components/Auth/AuthProvider.tsx
   - M client/src/hooks/useAuth.ts

   バックエンド（api/）:
   - M api/src/routes/auth.py
   - A api/src/middleware/auth_middleware.py
   - M api/src/models/user.py

   テスト:
   - A tests/unit/test_auth.py
   - M tests/integration/test_login.py

   設定・その他:
   - M .env.sample
   - M CLAUDE.md
   ```

2. **各ファイルの変更内容を確認**:
   ```bash
   # 重要なファイルの差分を確認（ファイルごとに実行）
   git diff origin/<base-branch>...HEAD -- <file-path>
   ```

3. **変更の性質を分類**:
   - 新機能追加（feat）
   - バグ修正（fix）
   - リファクタリング（refactor）
   - テスト追加（test）
   - ドキュメント（docs）
   - 設定変更（chore）

### 7. 変更内容の整理と説明

すべての情報を収集した後、以下の形式で簡潔に整理して報告します。

**報告フォーマット**:

```markdown
# ブランチ状況レポート

## 基本情報
- ブランチ名: feature/add-authentication
- PR #123: Add user authentication feature (OPEN)
- 親ブランチ: develop

## 変更統計
- 23ファイル変更、12コミット
- +1,234行 / -456行

## ブランチの目的
ユーザー認証機能の新規追加（JWT認証、ログイン/ログアウト、認証ミドルウェア）

## 主な変更
- フロントエンド: LoginForm、AuthProvider、useAuth等の認証関連コンポーネント実装
- バックエンド: 認証API、JWTミドルウェア、Userモデル拡張
- テスト: 認証関連の単体・統合テスト追加
- 設定: .env.sampleにJWT関連の環境変数追加
```

## エラーハンドリング

### PRが存在しない場合

```
⚠️ PRが見つかりません

【対処法】
1. PRを作成する: `gh pr create`
2. リモートにpush: `git push -u origin <branch>`
3. ブランチ名を確認: `git branch --show-current`
```

### 親ブランチが見つからない場合

```
⚠️ 親ブランチが特定できません

【対処法】
1. PRが作成されているか確認
2. デフォルトでdevelopブランチとの差分を表示
3. 手動で親ブランチを指定
```

### 差分が大きすぎる場合

```
⚠️ 変更が非常に多いです（100ファイル以上）

【推奨対応】
1. ファイルをカテゴリ別に分けて段階的に確認
2. 特に重要なファイル（スキーマ、API、環境変数）を優先
3. 必要に応じてブランチの分割を検討
```

## 使用例

### 例1: 通常のfeatureブランチ

```bash
/git:branch-status
```

**実行結果**:
```
✅ PR情報を取得しました

PR #123: Add user authentication feature
親ブランチ: develop
状態: OPEN

📊 変更統計を分析中...
変更ファイル数: 23ファイル
コミット数: 12個

📝 詳細を確認中...
（すべてのファイルの差分を確認）

✅ 分析完了

【ブランチの目的】
ユーザー認証機能の新規追加

【主な変更】
1. JWT認証の実装
2. ログイン/ログアウトAPI
3. 認証ミドルウェア
4. テスト追加
```

### 例2: 大規模な変更

```bash
/git:branch-status
```

**実行結果**:
```
✅ PR情報を取得しました

PR #456: Refactor entire authentication system
親ブランチ: develop
状態: OPEN

⚠️ 大規模な変更が検出されました
変更ファイル数: 127ファイル
コミット数: 45個

📝 カテゴリ別に詳細を確認中...

フロントエンド: 78ファイル
バックエンド: 35ファイル
テスト: 12ファイル
設定: 2ファイル

（各カテゴリの詳細を段階的に確認）

✅ 分析完了

【ブランチの目的】
認証システム全体のリファクタリング

（詳細な変更内容を整理して表示）
```

## 注意事項

### 実行前の確認

- [ ] リモートリポジトリにアクセス可能
- [ ] ghコマンドがインストール済み
- [ ] ブランチがリモートにpush済み

### 確認の徹底

- **手抜きは厳禁**: 修正が多くても全ファイルを確認
- **細部に注目**: 型定義、環境変数、スキーマ変更を見逃さない
- **コンテキストを理解**: 単なるファイル一覧ではなく、変更の意図を把握

### 報告の品質

- **具体的**: 「認証機能を追加」ではなく「JWT認証、ログイン/ログアウトAPIを実装」
- **網羅的**: すべての重要な変更を漏れなく記載
- **構造化**: カテゴリ別、優先度順に整理

## ベストプラクティス

### 定期的な確認

- PRレビュー前に実行
- 大きな変更をマージする前に実行
- チームメンバーとの共有前に実行

### 他のコマンドとの組み合わせ

```bash
# ブランチ状況確認 → developマージ
/git:branch-status
/git:merge-develop
```

## 関連コマンド

- `/git:merge-develop` - developの最新をマージ
- `/git:clean-branches` - マージ済みブランチの削除
- `/dev:check-diff-structure` - 差分ファイルの配置確認

## カスタムコマンド共通仕様

@.claude/lib/common.md
