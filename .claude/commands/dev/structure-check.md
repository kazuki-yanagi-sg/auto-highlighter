---
allowed-tools: [mcp__serena__list_dir, mcp__serena__search_for_pattern, Read, Bash, Edit, TaskCreate, TaskUpdate]
description: ドキュメント記載構造と実際のディレクトリ構造の整合性をチェックし、不整合を修正
---

# 構造整合性チェックと自動修正

`docs/structure/backend.md`と`docs/structure/frontend.md`の記載内容と実際のディレクトリ構造を比較し、不整合を検出・修正します。

## 引数の処理

引数: $ARGUMENTS

- 引数なし: プロジェクト全体をチェック・修正
- ディレクトリパス指定: 指定されたディレクトリ配下を全てチェック・修正
  - `api` → `api/` 配下全体（`api/src`, `api/tests` など）
  - `api/src` → `api/src/` 配下のみ
  - `client` → `client/` 配下全体
  - `client/src/components` → `client/src/components/` 配下のみ
  - 複数指定可能: `api/src api/tests`

## 実行フロー

### 1. ドキュメント確認

**Backend構造ドキュメント:**
- `docs/structure/backend.md` を読み込み
- 記載されている構造を解析

**Frontend構造ドキュメント:**
- `docs/structure/frontend.md` を読み込み
- 記載されている階層構造と命名規則を確認

### 2. 実際の構造確認

**Serenaのlist_dirを使用:**

```bash
# Backend
mcp__serena__list_dir(relative_path="api/src", recursive=true)

# Frontend
mcp__serena__list_dir(relative_path="client/src/components", recursive=true)
```

### 3. 実際のtree構造と設計書の構造比較

**重要:** 設計書に記載されているtree構造と実際のディレクトリ構造を詳細に比較する。

#### 比較手順

1. **tree構造の抽出**
   - 設計書から````text```ブロック内のtree構造を抽出
   - 実際のディレクトリからtree構造を生成

2. **構造の正規化**
   - コメント（`# ✅`、`# ❌`等）を除去
   - インデントを統一
   - 自動生成ファイル（`__pycache__`、`.next`等）を除外

3. **差分検出**
   - ディレクトリの存在チェック
   - ファイルの存在チェック
   - 階層構造の整合性確認

#### 差分パターン

**パターンA: 設計書にあるが実際に存在しない**

```text
docs/structure/backend.md には記載あり
→ api/src/routers/admin/reports/ が存在しない
```

**パターンB: 実際に存在するが設計書に記載がない**

```text
api/src/routers/admin/analytics/ が存在
→ docs/structure/backend.md に記載なし
```

**パターンC: 階層が異なる**

```text
設計書: api/src/routers/member/tickets/
実際:   api/src/routers/member/ticket/
```

### 4. 設計書の自動修正

**差分検出後の対応:**

#### 修正対象の判定

**自動修正する（設計書を実際に合わせる）:**
- 実際に存在するが設計書に記載がないディレクトリ/ファイル
- 階層構造の不一致（実際の構造を正とする）
- ファイル名の表記揺れ

**手動確認が必要:**
- 設計書にあるが実際に存在しないもの（削除されたのか、未実装なのか）

#### 設計書更新手順

1. **tree構造の再生成**

   ```bash
   # Backend
   tree -I '__pycache__|*.pyc|.pytest_cache' api/src

   # Frontend
   tree -I 'node_modules|.next|dist|.turbo' client/src/components
   ```

2. **設計書の該当セクションを更新**
   - EditツールでMarkdownの````text```ブロックを書き換え
   - 3分割構造（Core/Business/Supporting）を維持

3. **更新内容のレビュー**
   - 差分を明示的に出力
   - ユーザーに確認を促す

### 5. テストコードの構造親和性チェック

**目的:** テストコードのディレクトリ構造が実際のソースコードと対応しているかを検証。

#### Backend テスト構造チェック

- `src/` の階層構造と `tests/` の階層構造が対応しているか

#### Frontend テスト構造チェック

- ソースコードと同じディレクトリにテストファイルが配置されているか

#### 親和性チェック結果の出力

```text
📊 テストコード構造親和性チェック結果

Backend:
  ✅ テスト構造の対応: 95% (19/20)
  ⚠️  テスト未作成: 1件
    - api/src/routers/admin/reports/routers.py
      → tests/unit/routers/admin/reports/test_routers.py を作成してください

Frontend:
  ✅ テスト構造の対応: 92% (46/50)
  ⚠️  テスト未作成: 4件
    - client/src/lib/new-feature/index.ts
      → client/src/lib/new-feature/index.test.ts を作成してください
```

### 6. コード構造の不整合検出（従来機能）

#### Backend不整合パターン

以下のルールに準拠しているかをチェック:

@.claude/rules/backend/architecture.md の以下のセクション:
- **関心の分離（最重要）** - 権限別ディレクトリ（admin/member/shared/guest）の分離

#### Frontend不整合パターン

以下のルールに準拠しているかをチェック:

@.claude/rules/frontend/architecture.md の以下のセクション:
- **階層ルール** - Import規則、階層構造
- **Organismsコンポーネント命名規則**
- **Substancesコンポーネント命名規則**

### 7. コード修正処理（従来機能）

#### 不整合の優先度

**High（即座に修正）:**
- 命名規則違反
- 一貫性の欠如

**Medium（確認後修正）:**
- ドキュメント未記載の実装

**Low（記録のみ）:**
- 自動生成ファイル（`__pycache__`, `.next`等）

#### 修正手順

**ファイル移動が必要な場合:**

1. **移動先ディレクトリ作成:**

   ```bash
   mkdir -p client/src/components/organisms/badge/ticket-status
   ```

2. **ファイル移動:**

   ```bash
   git mv \
     client/src/components/organisms/badge/ticket-status.tsx \
     client/src/components/organisms/badge/ticket-status/index.tsx
   ```

3. **Import文の一括更新:**

   ```bash
   # 全ファイルのimport文を更新
   find client/src -type f -name "*.tsx" -o -name "*.ts" | \
     xargs sed -i '' 's|@/components/organisms/badge/ticket-status|@/components/organisms/badge/ticket-status/index|g'
   ```

**重要:** git mvを使用してGit履歴を保持

### 8. ドキュメント更新（従来機能）

修正後、該当ドキュメントを更新:

```markdown
# 修正前
organisms/
├── badge/
│   ├── ticket-status.tsx          # ❌
│   └── connection-status/

# 修正後
organisms/
├── badge/
│   ├── ticket-status/
│   │   └── index.tsx              # ✅
│   └── connection-status/
```

### 9. 検証

**TypeCheckで確認:**

```bash
bun run typecheck --cwd client
```

**テスト実行:**

```bash
bun run test --cwd client
```

## 出力フォーマット

### 1. 構造比較結果

```text
🔍 構造整合性チェック結果

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 ステップ1: 設計書とディレクトリ構造の比較
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Backend (docs/structure/backend.md vs api/src):
  ⚠️  差分を検出: 2件

  [設計書に記載なし] 実際に存在するディレクトリ
  - api/src/routers/admin/analytics/
  - api/src/models/notifications/

  → 設計書を更新します

Frontend (docs/structure/frontend.md vs client/src):
  ✅ 設計書と実際の構造が一致しています

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 ステップ2: テストコード構造親和性チェック
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Backend:
  ✅ テスト構造の対応: 95% (19/20)
  ⚠️  テスト未作成: 1件
    - api/src/routers/admin/analytics/routers.py
      → tests/unit/routers/admin/analytics/test_routers.py を作成推奨

Frontend:
  ✅ テスト構造の対応: 100% (50/50)
  🎉 全ての必須テストが存在します

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 ステップ3: コード構造の不整合検出
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Backend (api/src):
  ✅ ディレクトリ構造: 整合性あり
  ✅ ファイル配置: 問題なし

Frontend (client/src/components):
  ⚠️  不整合を検出: 1件

  [High] 命名規則違反
  - organisms/badge/ticket-status.tsx
    → あるべき姿: organisms/badge/ticket-status/index.tsx
    影響範囲: 7ファイル

→ 自動修正を実行します
```

### 2. 設計書修正結果

```text
📝 設計書を更新しました

修正内容:
  ✅ docs/structure/backend.md を更新
    - api/src/routers/admin/analytics/ を追加
    - api/src/models/notifications/ を追加

変更差分:
  + ├── routers/
  + │   ├── admin/
  + │   │   ├── analytics/          # ← 追加
  + │   │   │   └── routers.py
```

### 3. コード修正結果

```text
🔧 構造整合性の修正完了

修正内容:
  ✅ ファイル移動: organisms/badge/ticket-status.tsx → organisms/badge/ticket-status/index.tsx
  ✅ Import更新: 7ファイル
  ✅ ドキュメント更新: docs/structure/frontend.md

検証結果:
  ✅ TypeCheck: PASS
  ✅ Tests: PASS
```

## エラーハンドリング

**Import更新失敗時:**
- 手動での修正が必要なファイルをリストアップ
- 具体的な修正方法を提示

**テスト失敗時:**
- 変更をrollback
- 問題箇所を特定して報告

## 使用方法

- `/dev:structure-check` - プロジェクト全体をチェック・修正
- `/dev:structure-check api` - api配下全体（api/src, api/tests 等）をチェック・修正
- `/dev:structure-check api/src` - api/src のみチェック・修正
- `/dev:structure-check client` - client配下全体をチェック・修正
- `/dev:structure-check client/src/components` - client/src/components のみチェック・修正
- `/dev:structure-check "api/src api/tests"` - 複数ディレクトリを指定

## カスタムコマンド共通仕様

@.claude/lib/common.md
