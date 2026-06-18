---
allowed-tools: [Bash, LS, Read, Glob, Grep, Edit, MultiEdit, Write, TaskCreate, TaskUpdate, WebSearch]
description: Frontend/Backendコーディング規約の更新（既存コードパターンから自動検出）
---

# コーディング規約の更新

既存コードのパターンを分析し、規約ファイルを更新します。

## 規約ファイルの場所

- **Frontend**: `.claude/rules/frontend/architecture.md`
- **Backend**: `.claude/rules/backend/architecture.md`

## 実行フロー

### 1. 既存コードの分析

以下のディレクトリを分析し、実際のパターンを抽出:

**Frontend**:
- `client/src/components/` - コンポーネント構成
- `client/src/lib/` - ユーティリティ・APIクライアント
- `client/src/hooks/` - カスタムフック
- `client/src/test/` - テストパターン

**Backend**:
- `api/src/routers/` - ルーター構成
- `api/src/models/` - モデル設計
- `api/src/services/` - サービス層
- `api/tests/` - テストパターン

### 2. 規約との比較

- 既存コードのパターンと現在の規約を比較
- 差異を検出

### 3. 規約の更新

- 差異がある場合のみ規約を更新
- 更新不要な場合は「更新不要」と報告

## 観点（最重要）

### 1. ディレクトリ構成の担保

既存のディレクトリ構成を絶対に尊重する

### 2. 一貫性の重視

- 既存コードの書き方を必ず踏襲
- イレギュラーを排除
- レビューしやすいコード構成

### 3. シンプルな構成の追求

- 不要な抽象化を排除
- 明確な責務分離
- 理解しやすい構造

## 注意事項

- **既存コードのパターンが規約より優先される**
- 更新がなければ何もしない（無駄な変更禁止）
- 変更内容は明確に報告

## カスタムコマンド共通仕様

@.claude/lib/common.md
