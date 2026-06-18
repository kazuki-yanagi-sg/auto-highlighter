---
allowed-tools: [Bash, mcp__serena__find_symbol, mcp__serena__replace_symbol_body, mcp__serena__think_about_collected_information]
description: 対応中ブランチで新規追加された過剰なdocstring/コメントを削除（必要最小限のみ残す）
---

# dev:remove-excessive-comments

対応中ブランチで新規追加されたdocstring/コメントを分析し、過剰なものを削除します。

## 目的

- ✅ コーディングワークフロー準拠（コメントは最小限）
- ✅ 自明なコメントの削除
- ✅ 冗長なdocstringの簡潔化
- ❌ 既存コメントは保持（差分追加のみ対象）

## 削除対象

### Frontend (TypeScript/React)

- 自明な型・引数の説明
- 実装を繰り返すだけのコメント
- JSDocの過剰な説明
- console.log残骸

### Backend (Python)

- 自明な引数・戻り値のdocstring
- 実装を繰り返すだけのコメント
- 型ヒントで自明な説明
- print文残骸

## 保持対象

- ビジネスロジックの「なぜ」
- 非自明なアルゴリズムの説明
- TODOコメント（根拠付き）
- 型システムで表現できない制約

## 実行手順

### 1. 差分追加コメント抽出

```bash
# developとの差分で追加されたコメント行を特定
git diff develop...HEAD --unified=0 | grep -E "^\+.*(/\*|\*/|//|#|\"\"\")" | head -50
```

### 2. ファイル別に分析

追加されたコメントを含む各ファイルについて：

- `mcp__serena__find_symbol` でシンボル特定
- コメント削除基準を適用
- `mcp__serena__replace_symbol_body` で修正

### 3. 削除基準の適用

#### Frontend判定基準

```typescript
// ❌ 削除対象
/** ユーザーIDを返す */
function getUserId() { ... }

// ✅ 保持
/** レート制限: 5秒以内に3回以上の呼び出しでエラー */
function fetchData() { ... }
```

#### Backend判定基準

```python
# ❌ 削除対象
def get_user_id() -> int:
    """ユーザーIDを取得する

    Returns:
        int: ユーザーID
    """
    return user.id

# ✅ 保持
def calculate_priority() -> int:
    """優先度計算（Eisenhower Matrix準拠）

    重要度と緊急度から1-4の優先度を算出。
    アルゴリズム: important * 2 + urgent
    """
    return importance * 2 + urgency
```

### 4. 思考フェーズ

`mcp__serena__think_about_collected_information` で以下を確認：

- 削除したコメントは本当に不要か？
- 残したコメントは必要最小限か？
- ビジネスロジックの説明が失われていないか？

### 5. 検証

```bash
# 修正後の差分確認
git diff

# lintエラーがないか確認
./project_check.sh --client-lint  # Frontend
./project_check.sh --api-lint     # Backend
```

## 使用例

```bash
# 基本実行
/dev:remove-excessive-comments

# 特定ファイルのみ（引数拡張可能）
/dev:remove-excessive-comments client/src/components/organisms/form/ticket.tsx
```

## 注意事項

- **既存コメントは絶対に削除しない**（git diffで追加分のみ対象）
- **推測での削除は禁止**（確信が持てない場合は保持）
- **ビジネスロジックの「なぜ」は保持必須**
- **削除理由を明確に説明できない場合は保持**

## 期待される成果

- 可読性向上（コード自体が語る設計）
- 保守性向上（嘘をつかないコメント）
- レビュー効率化（本質的な差分に集中）

## カスタムコマンド共通仕様

@.claude/lib/common.md
