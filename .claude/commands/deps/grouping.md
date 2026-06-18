---
allowed-tools: [Read, Edit, MultiEdit, Write, Grep, Bash, WebSearch, TaskCreate, TaskUpdate]
description: Dependabotのグルーピング設定を自動生成・最適化
---

# Dependabotグルーピング設定

Dependabotのグルーピング機能で複数の依存関係更新を効率的に管理。

## 引数の処理

引数: $ARGUMENTS

- `/deps:grouping` - 全エコシステムのグルーピング設定
- `/deps:grouping frontend` - Frontend（npm）のみ
- `/deps:grouping patch-grouping` - patch更新のグループ化

## 実行フロー

1. **現状分析**: 既存dependabot.yml確認、プロジェクト構造把握
2. **戦略設計**: エコシステム別・更新レベル別・用途別グループ化
3. **設定生成**: マルチエコシステムグルーピング設定作成
4. **検証**: YAML構文チェック、段階的適用テスト

## グルーピング戦略

**Frontend**: React/TypeScript/UI/テストツール
**Backend**: FastAPI/DB/認証/テストツール
**共通**: 開発ツール/セキュリティ更新

## 使用方法

- `/deps:grouping` - 全エコシステムのグルーピング
- `/deps:grouping frontend` - Frontend特化設定
- `/deps:grouping multi-ecosystem` - マルチエコシステム統合

## カスタムコマンド共通仕様

@.claude/lib/common.md
