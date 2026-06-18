---
paths:
  - "client/**/*.{ts,tsx,jsx,js}"
---

# Frontend アーキテクチャ

## 階層ルール

### 階層構造（上から下へ）

1. **lib/api** （最上位、API クライアント）
2. **servers** （サーバーサイド処理）
3. **substances** （hooks, 状態管理）
4. **organisms** （デザイン・レイアウト）
5. **molecules** （小機能 UI）
6. **atoms** （最小単位 UI）

### 階層外ディレクトリ

- **components/shadcn/**: shadcn/ui 自動生成（編集禁止）
- **providers/**: Context Provider 群
- **generated/**: 自動生成（編集禁止）

### Import 規則

- ✅ 上位層 → 下位層
- ✅ 同階層内 OK
- ❌ 下位層 → 上位層
- ESLint `layer-arch/layer-imports` で自動検出

## 責務

| 層 | 責務 | 型依存 |
|---|---|---|
| lib/api | API クライアント | OpenAPI 型 |
| servers | サーバーサイド処理 | Prisma / OpenAPI 型 |
| substances | hooks, 状態 | OpenAPI 型 |
| organisms | デザイン・レイアウト | Prisma 型 |
| molecules | 小機能 UI | - |
| atoms | 最小単位 UI | - |

## 型原則

`as` cast / `any` 禁止は `prohibitions.md` に集約。ここでは型設計だけ書く。

- 親は子に従う（型変換は親で実施）
- `ComponentProps<typeof Component>` で型を Pick
- spread 構文は `...props` で統一
- Props 型名: `{ComponentName}Props`（`type Props =` 禁止）

## コンポーネント命名

ESLint `custom/component-naming` で自動検出（フォルダ階層を PascalCase 結合した名前と一致を強制）。

### Organisms

パターン: `Organisms{UIPattern}{Model}{Role}`

例:
- `OrganismsDataTableTicketAdmin`
- `OrganismsFormEntryTicket`
- `OrganismsLayoutHeader`

### Substances

パターン: `Substances{Role}{UIPattern}{Model}{Item}`

例:
- `SubstancesManagerDataTableTicket`
- `SubstancesMemberDialogNewTicket`
- `SubstancesAccountCardLogin`

## ディレクトリ構成

### Substances

```text
components/substances/
├── account/      # アカウント関連（ログイン後の自分の情報）
├── admin/        # 管理者権限
├── guest/        # 認証不要（ログイン画面等）
├── manager/      # マネージャ権限
├── member/       # メンバー権限
└── {feature}/    # 機能別（例: shipment-requests-picking）
```

UI パターン別サブディレクトリ: `data-table/`, `dialog/`, `form/`, `layout/`, `component/`, `chat/`, `combobox/`, `card/`, `grid-card/`

### Servers

```text
components/servers/
├── admin/
├── manager/
└── member/
```

ロール別に分割。サーバーサイド処理は role 配下に置く。

## テスト

- 必須: `lib/`, `hooks/`
- 不要: UI 層, `components/shadcn/`
- AAA パターン

## UI パターン

- React Hook Form + Zod
- Lucide React アイコン
- レスポンシブ: `md:` / `lg:` 使用、`sm:` 原則不使用
