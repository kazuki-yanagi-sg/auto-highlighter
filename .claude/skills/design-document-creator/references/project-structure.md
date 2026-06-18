# プロジェクト構造リファレンス

設計書のディレクトリ構成セクションで参照用（senri-core-system 実態）。

## Backend (api/)

```text
api/
├── src/
│   ├── <domain>/                # 例: consignors, items, delivery_records
│   │   ├── models.py            # SQLModel + Enum + Constraints
│   │   ├── factories.py         # test fixture
│   │   ├── schemas.py           # request / response
│   │   ├── services.py          # ビジネスロジック
│   │   ├── cud.py               # 必要時のみ
│   │   └── endpoints/           # ロール別ディレクトリ
│   │       ├── admin/           # 管理者権限（get_admin で保護）
│   │       ├── manager/         # マネージャ権限（get_manager で保護）
│   │       ├── member/          # メンバー権限（get_member で保護）
│   │       └── common/          # ロール非依存
│   ├── auth/                    # 認証基盤
│   │   └── endpoints/
│   │       ├── confirmable/
│   │       ├── database_authenticatable/
│   │       ├── lockable/
│   │       └── self/
│   ├── shared/                  # 横断ユーティリティ
│   ├── database/                # DB 接続
│   ├── modules/                 # 横断モジュール
│   ├── services/                # 横断サービス
│   ├── middlewares.py
│   └── main.py
│
└── tests/
    ├── conftest.py              # 横断 fixture
    ├── helpers/                 # 共通アサーション / ヘルパー
    ├── mocks/                   # モック・スタブ
    ├── unit/                    # モック使用、高速
    │   └── <domain>/
    └── integration/             # 実 DB（testcontainers）
        └── <domain>/
```

## Frontend (client/src/)

```text
client/src/
├── components/
│   ├── atoms/               # 最小単位 UI
│   ├── molecules/           # 小機能 UI
│   ├── organisms/           # デザイン・レイアウト（UI パターン別）
│   ├── substances/          # hooks, 状態
│   │   ├── account/         # アカウント関連
│   │   ├── admin/
│   │   ├── guest/           # 認証不要
│   │   ├── manager/
│   │   ├── member/
│   │   └── {feature}/       # 機能別（例: shipment-requests-picking）
│   ├── servers/             # サーバーサイド処理
│   │   ├── admin/
│   │   ├── manager/
│   │   └── member/
│   ├── shadcn/              # shadcn/ui 自動生成（編集禁止）
│   └── feature-design/
├── lib/
│   ├── api/                 # API クライアント
│   ├── cookies/
│   ├── csv/
│   ├── file-download/
│   ├── file-upload/
│   ├── label-print/
│   ├── print/
│   ├── shadcn/
│   ├── zip-cloud/
│   └── zod-i18n/
├── api/                     # ロール別 API ラッパー
│   ├── admin/
│   ├── common/
│   ├── guest/
│   ├── manager/
│   └── member/
├── hooks/                   # 共通 hooks
├── app/[locale]/            # ルーティング
├── generated/prisma/        # Prisma 型（編集禁止）
├── i18n/
├── middleware/
└── test/                    # テストヘルパー
    └── models/              # Prisma モデルのモック（1 ファイル 1 モデル）
```
