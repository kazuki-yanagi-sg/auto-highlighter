---
allowed-tools: [Bash]
description: Stacked PR構成のブランチに、developの最新変更を順次マージ・pushする（自動解析・CLOSED PR除外）
---

# Stacked Branches同期コマンド

Stacked PR（積み重ねPR）構成で、指定されたブランチから親子関係を自動解析し、developブランチの最新変更を順次マージ・pushします。

## このコマンドがやること

1. **developを最新化** - `git fetch origin develop:develop`
2. **ブランチの親子関係を自動検出** - 指定ブランチからdevelopまで遡る
3. **順次マージ・push** - 各ブランチで「マージ → 即push」を実行
4. **コンフリクト時は停止** - pushせずに手動解決を促す
5. **CLOSED PRのブランチはスキップ** - 処理対象外として自動除外

## 引数

- **引数1（任意）**: 対象ブランチ名（例: `feature/final-feature`）
- 引数なしの場合: 現在のブランチを使用

## 実行内容

### 1. develop最新化

```bash
git fetch origin develop:develop
```

### 2. ブランチ親子関係の自動解析

指定されたブランチから遡って、developまでの親子関係を自動検出。

**検出例**:

```text
入力: feature/integration-tests

検出される経路:
develop → feature/base-implementation → feature/ui-components → feature/integration-tests
```

### 3. 順次マージ・push処理

検出された経路に従って、各ブランチで**マージ→即push**を実行:

1. **最初のブランチ（develop直下）**:

   ```bash
   git checkout feature/base-implementation
   git merge develop --no-ff -m "chore: sync with latest develop"
   git push origin feature/base-implementation  # 即座にpush
   ```

2. **2番目以降のブランチ**:

   ```bash
   git checkout feature/ui-components
   git merge feature/base-implementation --no-ff -m "chore: sync with parent branch"
   git push origin feature/ui-components  # 即座にpush
   ```

3. **各ステップで**:
   - マージ前に`git status`で状態確認
   - マージ成功後、**即座にpushを実行**
   - push成功を確認してから次のブランチへ進む
   - コンフリクト発生時は即座に停止
   - ユーザーに状況を報告
   - 解決方法を提案（手動解決 or `git merge --abort`）

### 4. 結果サマリー

全ブランチの処理完了後:

- ✅ 成功したブランチ一覧
- ⚠️ コンフリクト等で停止したブランチ（あれば）

## エラーハンドリング

| エラー種別 | 動作 |
| ---------- | ---- |
| コンフリクト発生 | 即停止、pushせず手動解決を促す |
| push失敗 | 該当ブランチで停止、状況報告 |
| 親ブランチ検出失敗 | エラー表示、処理中断 |
| CLOSED PRブランチ | 警告表示してスキップ、処理継続 |

## 使用例

### 基本的な使用

```bash
/git:sync-stacked-branches feature/integration-tests
```

実行すると:

1. developを最新化
2. `feature/integration-tests`から親子関係を自動検出
   - 検出結果: `develop → feature/base → feature/ui → feature/integration-tests`
3. 順次マージ・push実行:
   - `feature/base` をマージ → push
   - `feature/ui` をマージ → push
   - `feature/integration-tests` をマージ → push
4. 結果サマリー表示

### 現在のブランチで実行

```bash
/git:sync-stacked-branches
```

引数なしの場合、現在のブランチを対象に実行。

### 想定される構成例

```text
develop
├── feature/base-implementation
    ├── feature/ui-components
        └── feature/integration-tests
```

この構成で`feature/integration-tests`を指定すると:

1. 親子関係を自動検出
2. `develop → base → ui → integration-tests` の順でマージ・push
3. 各ブランチにdevelopの最新変更が反映される

### CLOSED PRのブランチがある場合

```text
develop
├── feature/plan (PR: CLOSED)
    ├── feature/db-schema (PR: OPEN)
        ├── feature/api (PR: OPEN)
            └── feature/ui (PR: OPEN)
```

この構成で`feature/ui`を指定すると:

```bash
/git:sync-stacked-branches feature/ui
```

実行結果:

```text
⚠️  Skipping CLOSED PR branch: feature/plan
✅ 検出された経路:
   develop → feature/db-schema → feature/api → feature/ui

処理対象ブランチ: 3個
  - feature/db-schema
  - feature/api
  - feature/ui
```

**重要**: `feature/plan`はCLOSED状態のため自動的にスキップされ、その親の`develop`から直接マージが開始されます。

## 注意事項

- **コンフリクトは手動解決**: 自動解決は行わない（安全性優先）
- **--no-ffでマージ**: マージコミットを明示的に作成（履歴追跡のため）
- **処理完了後**: 元いたブランチに戻る

## 制限事項

- ブランチ名に`feature/`プレフィックスが必要
- 複数の親を持つブランチ（複雑なマージ履歴）は未対応

## カスタムコマンド共通仕様

@.claude/lib/common.md
