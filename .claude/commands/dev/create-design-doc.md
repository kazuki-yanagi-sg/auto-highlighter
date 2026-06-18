---
category: dev
description: 指定された画面の設計書を作成し、アカウント権限一覧を更新
created: 2025-01-14
---

# 設計書作成コマンド

指定された画面の設計書を作成します。フロントエンドとバックエンドの実装を徹底的に確認し、正確な設計書を生成します。

## 引数の処理

- **必須引数**: 設計書を作成する画面のパス（例: `/master/warehouses`, `/wm/shipment-requests/edit`）
- 引数が未指定の場合はエラーを返す

## 実行フロー

### 1. 事前準備（Taskツール必須）

以下のタスクリストを作成：

```
1. ブランチの作成と切り替え
2. 設計ガイドラインの理解（セクション3参照）
3. 既存設計書2つの確認（参考用）
4. フロントエンド実装の詳細調査
5. バックエンドAPI実装の詳細調査
6. 設計書ドラフトの作成
7. フロントエンド実装との照合（1周目）
8. フロントエンド実装との照合（2周目）
9. フロントエンド実装との照合（3周目）
10. バックエンド実装との照合（1周目）
11. バックエンド実装との照合（2周目）
12. バックエンド実装との照合（3周目）
13. アカウント権限一覧への設計書URL追加
14. Client lintチェック実行
15. Commit + Push + PR作成
```

### 2. ブランチ作成

```bash
# 現在のブランチがdevelopの場合のみ新しいブランチを作成
# それ以外の場合は現在のブランチで作業継続
git checkout -b docs/add-design-[feature-name]
```

### 3. 設計書作成のガイドライン

設計書を作成する際は、以下のガイドラインに厳密に従ってください。

#### 3.1 基本方針

- 仕様書画面のアクセス権限は画面ごとに設定（詳細は `/feature-design/account-permission` を参照）
- 抽象度の高い内容で、エンジニアではない人でも理解できる表現を使用
- 詳細な設計ではなく、データ通信とAPI操作の概要を記載

#### 3.2 設計書の構成

設計書は以下の順序で構成してください：

**1. 画面概要**
- 箇条書きで簡潔に記載
- 重複した表現は避ける
- 例：「倉庫情報の管理画面（登録・参照・更新・削除・検索）」

**2. 機能一覧**
- フロントエンドとバックエンドの機能を明確に分けて記載
- グリッドレイアウトで左右に配置（md:grid-cols-2）
- それぞれを独立したCardコンポーネントとして表示

**3. アカウントタイプ別権限**
- 表形式で記載し、機能一覧の直後に配置
- アカウントタイプ（Admin、Manager、User）ごとに使用可能な機能を○印で示す
- 機能ごとにどのアカウントタイプが使用できるかを明確にする
- 機能の並び順: 一覧表示→検索→詳細表示→登録→更新→削除

**4. 個別機能セクション**
- 各機能をCardコンポーネントで記載
- 機能の並び順: 一覧→参照→登録→更新→削除
- 一覧機能と検索機能は1つのセクションにまとめる（「一覧表示・検索機能」）
- 各セクション内でグリッドレイアウトを使用し、左側にフロントエンド、右側にバックエンドの動きを配置
- フロントエンドとバックエンドの間に縦線を表示（`md:border-r`を使用）

**5. 補足情報**
- 特殊な機能や注意事項のみ記載
- 一般的なエラーハンドリングに関する記述は不要
- ビジネスロジックに関わる特殊な制約やエラーは記載可

#### 3.3 記載内容のルール

**不要な表現**

以下の表現は原則として記載しない：

- **一般的なフォームバリデーション**: 「必須チェック」「入力値チェック」などの一般的なバリデーション
  - ただし、ビジネスルールに関わる特定のバリデーション（「数量 > 0」など）は記載可
- **一般的なエラーハンドリング**: 「エラーメッセージを表示」などの一般的なエラー処理
  - ただし、ビジネスロジックに関わるエラー（「請求済みの場合はエラー（422）」など）は記載可
- **権限チェック**: 「権限チェック」という表現（権限表で示すため）
- **アカウントタイプの括弧書き**: 「（管理者のみ）」などの括弧書き（権限表で示すため）

**許容される表現**

以下の表現は記載して問題ない：

- **具体的なバリデーション**: ビジネスルールに関わる場合（例：「バリデーション：数量 > 0、出荷日必須」）
- **具体的なエラー**: ビジネスロジックに関わる場合（例：「変更がない場合はエラー（422）」）

**必要な表現**

- 機能の具体的な動作内容
- データの流れや処理内容
- 重複チェックや依存関係チェックなど、ビジネスロジックに関わる処理
- APIエンドポイントとHTTPメソッド
- データベース操作の概要

**用語の一貫性**

- 「登録」を使用（「新規登録」は使用しない）
- 機能名の並び順: 一覧→参照→登録→更新→削除
- アカウントタイプに関する括弧書き（例：「（管理者のみ）」）は記載しない（権限表で明示するため）

#### 3.4 機能の記載例

**フロントエンド機能の記載例：**

```
- 〇〇一覧の表示
- 〇〇名・〇〇コードによる検索
- 〇〇詳細の表示
- 〇〇の登録
- 〇〇の更新
- 〇〇の削除
```

**バックエンド機能の記載例：**

```
- 〇〇データの検索と取得
- 〇〇の登録と重複チェック
- 〇〇の更新と重複チェック
- 〇〇の削除と依存関係チェック
```

#### 3.5 データ構造の記載方法（DesignDefinitionTable）

データ構造（API仕様、フォーム項目、バリデーションなど）は**必ずDesignDefinitionTableコンポーネント**を使用してテーブル形式で記載します。

**重要原則：**

1. **実際の変数名を使用**: OpenAPI型定義（`client/src/openapi/types.gen.ts`）から正確な変数名を取得
2. **憶測で変数名を書かない**: 必ずコードを確認
3. **2列形式**: 物理名と説明のペア（field/description、parameter/description など）

- URLパラメータ: `parameter` + `description`
- 送信データ・レスポンスデータ: `field` + `description`（型名を括弧内に記載）
- ソート条件: `field` + `order`
- 重複チェック・存在確認: `field` + `condition`

詳細は既存設計書（`/feature-design/master/warehouses`、`/feature-design/wm/shipment-requests/edit`）を参照してください。

#### 3.6 API記載方法

**基本ルール：**

1. API URLは箇条書き（`<li>`）で記載
2. URLパラメータ、送信データ、レスポンスデータは**必ずDesignDefinitionTableでテーブル化**
3. 型名を括弧内に記載（例: `送信データ（WarehouseCreateSchema）`）

詳細は既存設計書（`/feature-design/master/warehouses`、`/feature-design/wm/shipment-requests/edit`）を参照してください。

#### 3.7 バリデーション記載方針

**固有のビジネスロジックがある場合のみ**記載します。一般的なバリデーション（必須チェック、型チェックなど）は記載不要です。

**記載すべきバリデーション：**
- 重複チェック（DesignDefinitionTableで `field` + `condition` 形式）
- 依存関係チェック（DesignDefinitionTableで `field` + `condition` 形式）
- ビジネスルール固有の制約（例: 出荷日は入庫日以降）

### 4. 既存設計書の確認（参考用）

以下の2つの設計書を読み込み、構造とスタイルを理解：

1. `client/src/app/[locale]/(member-layout)/feature-design/master/warehouses/page.tsx`
2. `client/src/app/[locale]/(member-layout)/feature-design/wm/shipment-requests/edit/page.tsx`

### 5. フロントエンド実装の詳細調査

指定された画面パス（`client/src/app/[locale]/(member-layout)/[指定パス]/page.tsx`）とその関連コンポーネント（organisms/molecules/substances）を確認し、以下を把握：

- 使用しているAPI（エンドポイント、パラメータ、送信データ、レスポンス）
- フォームフィールド（名称、型）
- 表示データ（一覧項目、詳細項目）
- ユーザー操作（ボタンクリック、フォーム送信の処理フロー）

### 6. バックエンドAPI実装の詳細調査

フロントエンドで呼び出されているAPIエンドポイントを特定し、各APIについて以下を確認：

- ルーター・サービス層（`api/src/[module]/endpoints/[role]/routers.py`、`services.py`）
- スキーマ（`schemas.py`）から、リクエスト・レスポンスの型定義
- ビジネスロジック（重複チェック、依存関係チェック、計算処理）
- データベース操作（検索条件、ソート、登録・更新・削除の処理）

### 7. 設計書ドラフトの作成

#### 7.1 設計書のパス構成

設計書のパスは、本番画面のパスに `/feature-design/` プレフィックスを追加し、動的セグメント（`[id]` など）を除いた形で構成します。

**パス構成例：**

| 本番画面のパス | 設計書のパス |
|--------------|-------------|
| `/master/warehouses` | `/feature-design/master/warehouses` |
| `/wm/shipment-requests/[shipmentRequestId]/edit` | `/feature-design/wm/shipment-requests/edit` |

**その他の例：**
- アカウント権限一覧: `/feature-design/account-permission`
- 管理者専用画面の場合も同様のルールを適用

#### 7.2 設計書テンプレート

以下の構成で設計書を作成：

```tsx
'use client'

import { MoleculesPageTitle } from '@/components/molecules/page-title'
import { DesignSectionWithList } from '@/components/feature-design/section-with-list'
import { DesignPermissionsTable } from '@/components/feature-design/permissions-table'
import { DesignFeaturesList } from '@/components/feature-design/features-list'
import { DesignFeatureSection } from '@/components/feature-design/feature-section'
import { DesignDefinitionTable } from '@/components/feature-design/definition-table'

export default function [FeatureName]DesignPage() {
  // 1. 画面概要
  const overview = ['...']

  // 2. アカウントタイプ別権限
  const permissions = [
    { feature: '一覧表示', admin: true, manager: true, user: true },
    // ...
  ]

  // 3. 機能一覧
  const frontendFeatures = [
    { text: '〇〇一覧の表示・検索', anchor: 'list-search' },
    { text: '〇〇詳細の表示', anchor: 'detail' },
    { text: '〇〇の登録', anchor: 'create' },
    // ...
  ]
  
  const backendFeatures = [
    { text: '〇〇データの検索と取得', anchor: 'list-search' },
    { text: '〇〇詳細の取得', anchor: 'detail' },
    { text: '〇〇の登録と重複チェック', anchor: 'create' },
    // ...
  ]

  return (
    <div className='container mx-auto space-y-6 p-6'>
      <MoleculesPageTitle title='[画面名] 設計書' />

      <DesignSectionWithList title='画面概要' items={overview} />

      <DesignPermissionsTable permissions={permissions} />

      <DesignFeaturesList
        frontendFeatures={frontendFeatures}
        backendFeatures={backendFeatures}
      />

      {/* 個別機能セクション */}
      <DesignFeatureSection
        id='list-search'
        title='1. 一覧表示・検索機能'
        frontendItems={
          <ul className='list-disc space-y-2 pl-6'>
            <li>
              GET /api/v1/member/xxx
              <ul className='mt-1 ml-4 list-[circle]'>
                <li>page: ページ番号</li>
                <li>per: 1ページあたりの件数</li>
                <li>xxx_name: 〇〇名</li>
              </ul>
            </li>
            <li>検索フォームで〇〇名または〇〇コードを入力してURLパラメータを更新</li>
            <DesignDefinitionTable
              title='表示項目'
              items={[
                { field: 'xxxCode', description: '〇〇コード' },
                { field: 'xxxName', description: '〇〇名' },
                { field: 'createdAt', description: '作成日時' },
              ]}
            />
          </ul>
        }
        backendItems={
          <ul className='list-disc space-y-2 pl-6'>
            <li>〇〇名は部分一致、〇〇コードは部分一致でデータベースを検索</li>
            <DesignDefinitionTable
              title='レスポンスデータ'
              items={[
                { field: 'xxxList', description: '〇〇一覧（配列）' },
                { field: 'total', description: '総件数' },
                { field: 'page', description: '現在ページ' },
              ]}
            />
          </ul>
        }
      />

      {/* その他の機能セクション */}
    </div>
  )
}
```

ファイル保存先: `client/src/app/[locale]/(member-layout)/feature-design/[指定パス]/page.tsx`

### 8. フロントエンド実装との照合（3周レビュー）

設計書の内容が実装と一致しているかを確認：

1. **1周目**: 機能の網羅性、API、フォームフィールド名
2. **2周目**: 画面遷移、検索ロジック、データの流れ
3. **3周目**: ビジネスロジック、ガイドライン準拠

### 9. バックエンド実装との照合（3周レビュー）

設計書の内容が実装と一致しているかを確認：

1. **1周目**: APIエンドポイント、パラメータ、レスポンス構造、データベース操作
2. **2周目**: バリデーションルール、ビジネスロジック（重複チェック、依存関係チェック）
3. **3周目**: 設計書の表現と実装の一致、適切な抽象度

### 10. アカウント権限一覧への設計書URL追加

`client/src/app/[locale]/(member-layout)/feature-design/account-permission/page.tsx` を開き、該当する画面のオブジェクトに `designDocUrl` を追加：

```typescript
{
  name: '[画面名]',
  url: '[画面URL]',
  category: '[カテゴリ]',
  admin: true,
  manager: true,
  member: true,
  note: '[備考]',
  designDocUrl: '/feature-design/[指定パス]',  // 追加
},
```

**重要**: 同じ設計書を参照すべき画面が複数ある場合（例: 一覧・詳細・登録・編集・削除）、すべてのページに同じURLを設定する。

### 11. Client lintチェック実行

```bash
sh project_check.sh -cl
```

エラーがあれば修正して再実行。

### 12. Commit + Push + PR作成

変更をステージング、コミット、プッシュし、PRを作成します。

## 重要な注意事項

1. **完全性の重視**: 設計書は実装と完全に一致させる。3周レビューを徹底
2. **確認範囲**: フロントエンドはsubstances/organisms/molecules、バックエンドはrouters/services/schemasまで確認
3. **表現の正確性**: ビジネスロジックは記載、一般的な機能（エラーハンドリングなど）は記載不要

## 使用例

```bash
# 倉庫マスタの設計書を作成
/dev:create-design-doc /master/warehouses

# 出荷リクエスト編集の設計書を作成
/dev:create-design-doc /wm/shipment-requests/edit

# 入庫実績登録の設計書を作成
/dev:create-design-doc /wm/receiving-records/new
```

## カスタムコマンド共通仕様

@.claude/lib/common.md
