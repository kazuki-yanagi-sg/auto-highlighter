---
paths:
  - "CLAUDE.md"
  - "CLAUDE.local.md"
  - ".claude/CLAUDE.md"
  - ".claude/rules/**/*.md"
---

# Claude への指示ファイルの書き方

## 仕組みの違い

| 種類 | いつロード | 何を書く |
|---|---|---|
| CLAUDE.md | 毎セッション全文 | 常時効く普遍原則 |
| .claude/rules/*.md（paths なし） | 毎セッション全文 | CLAUDE.md の延長分割 |
| .claude/rules/*.md（paths あり） | 該当ファイルを触る時だけ | 領域固有の規約 |
| @xxx.md（CLAUDE.md からの import） | 毎セッション全文展開 | 整理のみ／サイズ削減効果なし |

## サイズ目安

| 対象 | 目安 | 出典 |
|---|---|---|
| CLAUDE.md | 200 行未満 | 公式明示 |
| .claude/rules/*.md（1 ファイル） | 200 行以内 | 公式明示なし／同原理から推論 |
| 同時ロード合計 | 〜600 行 | 経験則 |

- 公式が「200 行未満」と明示するのは CLAUDE.md のみ
- rules ファイル個別のサイズ推奨は公式に存在しない
- ただし「paths なし rules は CLAUDE.md と同等扱い」と公式に記載されているため、同じ目安で運用する

## どこに何を書くか

| 内容 | 置き場所 |
|---|---|
| 常時効く普遍原則（後方互換ポリシー、PR 方針、判断軸） | CLAUDE.md |
| 領域固有の規約（API 設計、React 規約、テスト方針） | .claude/rules/<topic>.md + paths |
| 作業手順・ワークフロー（リリース手順、特定の段取り） | .claude/skills/<name>/SKILL.md |
| 自動化できる規約（インデント、命名、import 順） | lint / formatter / 型 / テスト |

## path-scoped rules の書き方

```markdown
---
paths:
  - "src/frontend/**/*.tsx"
---

# フロントエンドのルール

- 関数コンポーネントで書く
- ...
```

- ファイル先頭に `---` で囲った YAML frontmatter を置く
- `paths` に glob パターンを並べる
- 該当パスのファイルを触った時だけロードされる
- 同時に複数 rules が発動するケースがあるため、合計サイズも意識する

## 設計の順番

```
1. CLAUDE.md に普遍原則だけ書く（〜200 行）
        ↓ 領域固有のものがある
2. .claude/rules/<topic>.md + paths で分割
        ↓ 単一領域で 200 行超える
3. 規約そのものを縮める
   - lint / formatter / 型 / テストに移す
   - rules には「判断軸」だけ残す
        ↓ 作業手順なら
4. .claude/skills/ に移す
```

## やってはいけない

- `@xxx.md` import でサイズ削減を狙う（毎回全文ロードされるため効果なし）
- 自動化できる規約をテキストで書く（lint / 型 / テストに移す）
- 経緯・歴史を残す（今の状態だけ書く）
- 1 ファイルを 200 行超で書く

## 出典

- https://code.claude.com/docs/en/memory
