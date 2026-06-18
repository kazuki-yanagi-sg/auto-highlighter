# Git・PR ルール

`--no-verify` / worktree 等の禁止は `prohibitions.md` に集約。ここでは「形式」だけ書く。

## ブランチ

- 命名: `feature/` / `fix/` / `refactor/` / `chore/`（英語）
- **develop から分岐**（`main` 禁止）
- lefthook の `check-branch-name` で機械検証

## コミット

Conventional Commits（英語本文）。

```bash
git commit -m "feat: add feature"
git commit -m "fix(client): handle null case"
git commit -m "refactor(api): extract helper"
```

| type | 用途 |
|---|---|
| feat | 新機能 |
| fix | バグ修正 |
| refactor | リファクタ |
| docs | ドキュメント |
| test | テスト |
| chore | ツール / 設定 |

## PR

- **タイトル**: Conventional Commits（`type(scope): subject`）+ 日本語必須
  - 例: `feat(client): 配送費実績管理に検索日付rangeを追加`
  - GitHub Actions（`PR Title Check`）で機械検証（Dependabot / Renovate は除外）
- **本文**: 日本語
- **ベース: `develop`**（`main` 禁止）
- 作成後は `gh pr view --web` でブラウザに開く
