---
allowed-tools: [Bash, mcp__serena__search_for_pattern, mcp__serena__find_symbol, mcp__serena__list_dir, Read, TaskCreate, TaskUpdate]
description: developとの差分ファイルが適切な場所に配置されているかをチェックし、修正提案をbefore/afterで表示
---

# 差分ファイル配置チェックと修正提案

現在のブランチでdevelopから変更されたファイルを抽出し、既存の類似ファイルと比較して適切なディレクトリに配置されているかをチェック・修正提案をbefore/afterで表示します。

## 引数の処理

引数: $ARGUMENTS

- 引数なし: 現在のブランチのdevelopとの差分を全てチェック

## 実行フロー

### 1. 現在のブランチとdevelopとの差分を確認

**ブランチ確認:**

```bash
# 現在のブランチを確認
CURRENT_BRANCH=$(git branch --show-current)
echo "現在のブランチ: $CURRENT_BRANCH"

# developブランチでない場合のみ実行
if [ "$CURRENT_BRANCH" = "develop" ]; then
  echo "エラー: developブランチでは実行できません"
  exit 1
fi
```

**差分ファイルを抽出:**

```bash
# developとの差分ファイル一覧を取得（削除ファイルを除外）
git diff develop...HEAD --name-only --diff-filter=ACMR
```

### 2. 差分ファイルをBackend/Frontendに分類

**分類ルール:**
- Backend: `api/src/` または `api/tests/` 配下
- Frontend: `client/src/` 配下
- その他: チェック対象外

**出力例:**

```text
📋 差分ファイル一覧

Backend (3件):
  - api/src/routers/member/new_feature.py
  - api/src/models/new_model.py
  - api/tests/unit/routers/member/test_new_feature.py

Frontend (2件):
  - client/src/components/organisms/new-component.tsx
  - client/src/lib/api-client/new-endpoint.ts
```

### 3. 各差分ファイルの類似ファイルを探索

**重要:** 各差分ファイルについて、以下の手順で類似ファイルを探す。

#### ステップA: ファイル名から類似性を推測

```bash
# 例: new_ticket_router.py
# → "ticket" というキーワードを抽出
# → Serenaの search_for_pattern で "ticket" を含むファイルを検索

mcp__serena__search_for_pattern(
  substring_pattern="ticket",
  relative_path="api/src/routers",
  restrict_search_to_code_files=true
)
```

#### ステップB: ファイル内容を読んで用途を分析

```bash
# Serenaの find_symbol でファイルの主要な関数/クラスを取得
mcp__serena__find_symbol(
  name_path="/",  # トップレベルシンボル
  relative_path="api/src/routers/member/new_feature.py",
  include_body=true,
  depth=1
)

# 分析内容:
# - FastAPIのルーターか？ → routers/ 配下が正しい
# - Pydanticモデルか？ → models/ 配下が正しい
# - ユーティリティ関数か？ → utils/ 配下が正しい
# - admin/member/sharedのどの権限か？ → 関心の分離を確認
```

#### ステップC: 類似ファイルの配置場所を特定

**既存の類似ファイルが見つかった場合:**

```text
類似ファイル: api/src/routers/admin/ticket.py
→ このファイルのディレクトリ: api/src/routers/admin/
→ 差分ファイルもここに配置すべき可能性が高い
```

**複数の類似ファイルが見つかった場合:**

```text
類似ファイル候補:
1. api/src/routers/admin/ticket.py
2. api/src/routers/member/ticket.py

→ ファイル内容を分析して権限（admin/member）を判定
→ 最も適切な配置場所を決定
```

### 4. CLAUDE.mdルールとの照合

**Backend:**

@.claude/rules/backend/architecture.md の以下のセクション:
- **関心の分離（最重要）** - 権限別ディレクトリ（admin/member/shared/guest）の分離

**チェック内容:**
- admin権限のコードが member/ に配置されていないか
- member権限のコードが admin/ に配置されていないか
- 認証不要のコードが shared/ に配置されているか

**Frontend:**

@.claude/rules/frontend/architecture.md の以下のセクション:
- **階層ルール** - Import規則、階層構造
- **Organismsコンポーネント命名規則**
- **Substancesコンポーネント命名規則**

**チェック内容:**
- atoms/molecules/organisms/substances の階層が正しいか
- 命名規則（`OrganismsXxxYyy`、`SubstancesXxxYyy`）に従っているか

※ import 方向は ESLint `layer-arch/layer-imports` で自動検出

### 5. 配置の妥当性を判定

**判定基準:**

**✅ 配置OK:**
- 類似ファイルと同じディレクトリに配置されている
- CLAUDE.mdのルールに準拠している
- ファイル名の命名規則が正しい

**⚠️ 配置が疑わしい:**
- 類似ファイルとは異なるディレクトリに配置されている
- ファイル内容とディレクトリ名が一致しない
- 例: admin用のコードが member/ に配置

**❌ 配置が間違っている:**
- CLAUDE.mdのルール違反（関心の分離、階層ルール）
- 命名規則違反
- テストファイルの配置が実装と対応していない

### 6. 修正提案の作成

**修正が必要な場合:**

#### 6-1. Before/After比較の作成

**問題のあるファイルごとに以下の形式で提案:**

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 修正提案 #1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【問題】
api/src/routers/member/admin_report.py
→ admin権限のコードが member/ に配置されている

【類似ファイル】
api/src/routers/admin/user_report.py (admin権限)
api/src/routers/admin/ticket.py (admin権限)

【修正内容】
権限の分離ルールに基づき、admin/ に移動すべき

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Before (現在の配置)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

api/src/routers/member/
├── ticket.py
├── task.py
├── admin_report.py  ← ❌ ここに配置（member権限ディレクトリ）
└── profile.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ After (修正後の配置)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

api/src/routers/admin/
├── user.py
├── ticket.py
└── report.py  ← ✅ ここに移動（admin権限ディレクトリ）
```

#### 6-2. 修正不要の場合

```text
✅ 全ての差分ファイルが適切に配置されています

チェック対象: 5件
- Backend: 3件 → 全て配置OK
- Frontend: 2件 → 全て配置OK

修正不要です。
```

### 7. 結果レポート出力

**問題がある場合:**

```text
🔍 差分ファイル配置チェック結果

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 修正提案: 2件
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

詳細な修正提案（Before/After）は上記セクション6を参照してください。
```

**問題がない場合:**

```text
🔍 差分ファイル配置チェック結果

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 全ての差分ファイルが適切に配置されています
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

修正不要です。
```

## エラーハンドリング

**類似ファイルが見つからない場合:**
- ファイル内容のみでCLAUDE.mdルールに基づいて判定
- 判定根拠を明示してユーザーに提案

**判定が困難な場合:**
- 複数の配置候補を提示
- それぞれのメリット・デメリットを説明
- ユーザーに最終判断を委ねる

## 使用方法

- `/dev:check-diff-structure` - 現在のブランチのdevelopとの差分をチェックし、修正提案を表示

## カスタムコマンド共通仕様

@.claude/lib/common.md
