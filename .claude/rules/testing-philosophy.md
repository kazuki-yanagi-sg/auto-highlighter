---
paths:
  - "api/tests/**/*.py"
  - "api/**/test_*.py"
  - "api/**/conftest.py"
  - "client/**/*.{test,spec}.{ts,tsx,jsx,js}"
---

# テスト思想（テストは仕様の定義書）

## Google Testing Philosophy

本プロジェクトでは Google Testing Philosophy に準拠する。

**核心思想**:

- **状態のテスト**: 相互作用ではなく、最終的な状態を検証
- **パブリックAPIを通じたテスト**: 実装の詳細に依存しない
- **Beyoncé Rule**: 壊れたくないものは必ずテストする

## テストの価値基準

1. **バグの早期発見**: 本番に到達する前に検出
2. **リグレッション防止**: 既存機能の破壊を防ぐ
3. **ドキュメント**: コードの意図を伝える生きた仕様書
4. **リファクタリングの安全網**: 改善を恐れずに行える基盤

## テストすべきこと / すべきでないこと

**テストすべき**:

- ビジネスロジック
- バリデーション
- エラーハンドリング
- 認証・認可
- データの整合性

**テスト不要**:

- フレームワーク自体の機能（FastAPI / SQLModel / React の挙動）
- 単純な getter/setter
- ログ出力の詳細
- サードパーティライブラリの内部動作

## テストサイズ分類（共通）

| サイズ | 目安 | 特徴 |
|---|---|---|
| Small | <100ms | モック使用、外部依存なし、決定的 |
| Medium | 100ms〜1s | 実インフラ使用、トランザクションで隔離 |
| Large | >1s | E2E。最小限に抑える（目標: 0%） |

## SMURF フレームワーク

Test Pyramid を補完する多次元評価モデル（Google Testing Blog 由来）。

| 次元 | 説明 | Unit | E2E |
|---|---|:---:|:---:|
| **S**peed | 実行速度 | ⭐⭐⭐ | ⭐ |
| **M**aintainability | 保守性 | ⭐⭐⭐ | ⭐ |
| **U**tilization | リソース効率 | ⭐⭐⭐ | ⭐ |
| **R**eliability | 安定性（Flaky 回避） | ⭐⭐⭐ | ⭐ |
| **F**idelity | 運用環境との近似度 | ⭐ | ⭐⭐⭐ |

### 判断原則

1. 複数の次元を損なわずに 1 つ以上を改善できるなら実施する
2. トレードオフが避けられない場合はプロジェクトの優先事項で判断する

### 本プロジェクトの方針

- ビジネスロジック → Unit Test（高 Speed / Maintainability）
- DB/API 連携 → Integration Test（高 Fidelity）
- E2E → 最小限（Frontend の Playwright に委譲）

## AAA パターン（共通フォーマット）

全テストは Arrange / Act / Assert の 3 段で書く。コメントは英語で。

```text
# Arrange: 準備（テストデータ、前提条件）
# Act:     実行（テスト対象の操作を 1 つだけ）
# Assert:  検証（期待結果の確認）
```

## 禁止事項（共通）

- **モックの過剰使用**: 検証対象自体をモックしない。外部依存のみモック
- **実装の詳細への依存**: パブリック API を通じて検証する
- **テストの書き換え**: 失敗時は実装を直す。テストを通すための書き換えは禁止

## 参考

- [Google Testing Blog - SMURF: Beyond the Test Pyramid](https://testing.googleblog.com/2024/10/smurf-beyond-test-pyramid.html)
