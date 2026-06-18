# 3 ブロック記入例

session-summary スキルの記入例。状況に近い方を参考にしろ。

---

## サンプル 1: 単一作業ケース

元の状況: 1 PR の修正作業のみ。follow-up なし。

チャット提示:

```markdown
## ✅ 直近終わったこと

`refactor-one-pr` スキルの観点 A〜F 説明を箇条書き化して読みやすくした。

## ⚠️ follow-up

該当なし
```

（複数行動なしのため 📋 サマリーブロックは省略）

---

## サンプル 2: 複数行動ケース

元の状況: 認証周りの小タスクを 3 件並列で消化。1 件は設計検討で follow-up issue 化。

チャット提示:

```markdown
## ✅ 直近終わったこと

ログイン周りの細かい改善 3 件を消化。パスワードリセットの設計検討は follow-up に切り出した。

## 📋 サマリー

| # | PR | 状態 | 概要 | やったこと |
|---|---|---|---|---|
| A | [#101](https://github.com/sky-grid-inc/senri-core-system/pull/101) | MERGED | feat(auth): セッション期限切れ時のリダイレクト先を保持 | 期限切れリダイレクトに `from` を載せた |
| B | [#102](https://github.com/sky-grid-inc/senri-core-system/pull/102) | MERGED | refactor(auth): ログインフォーム validation を zod に統一 | yup → zod 移行で 1 重複削除 |
| C | [#103](https://github.com/sky-grid-inc/senri-core-system/pull/103) | OPEN | fix(auth): メアド大文字混入時のログイン失敗を修正 | normalize を `lower` に統一 |

## ⚠️ follow-up

| # | 項目 | 何がまずいか | 補足 |
|---|---|---|---|
| 1 | follow-up #110 | パスワードリセットの 2 段階認証要否が未確定 | メール 1 段階のままで良いか、SMS 追加するかをプロダクト判断待ち |
```

---

## サンプル 3: 情報不足ケース

元の状況: PR は merge 済みだが follow-up が会話履歴から拾えない。

チャット提示:

```markdown
## ✅ 直近終わったこと

PR #200 を merge。flake8 plugin に新しい AST ルールを 1 件追加した。

## ⚠️ follow-up

情報なし
```

（follow-up があるかどうか会話履歴から判断できない時は捏造せず「情報なし」と書け）
