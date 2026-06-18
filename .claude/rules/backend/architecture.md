---
paths:
  - "api/**/*.py"
---

# Backend アーキテクチャ

## 大原則

- 1 ドメイン = `api/src/<domain>/` ディレクトリ（複数形・スネークケース。例: `consignors/`, `delivery_records/`）
- ロール別認可は `endpoints/{admin,manager,member,common}/` でディレクトリ分割
- 異なるロールを同一ファイルに混在禁止
- 各ロールは `get_admin` / `get_manager` / `get_member` 等で保護
- URL は ロール prefix を持つ: `/api/v1/admin/...` `/api/v1/manager/...` `/api/v1/member/...`

## ディレクトリ構造

```text
api/src/
├── auth/                       # 認証基盤
│   ├── endpoints/
│   │   ├── confirmable/
│   │   ├── database_authenticatable/
│   │   ├── lockable/
│   │   └── self/
│   └── mixins/
├── <domain>/                   # 例: consignors, items, delivery_records
│   ├── models.py               # SQLModel + Enum + Constraints
│   ├── factories.py            # test fixture
│   ├── schemas.py              # request / response
│   ├── services.py             # ビジネスロジック
│   ├── cud.py                  # 必要時のみ（Create/Update/Delete 集約）
│   └── endpoints/
│       ├── admin/              # 管理者権限（get_admin で保護）
│       ├── manager/            # マネージャ権限（get_manager で保護）
│       ├── member/             # メンバー権限（get_member で保護）
│       └── common/             # ロール非依存
├── shared/                     # 横断ユーティリティ
├── database/                   # session / engine
├── modules/                    # 横断モジュール
├── services/                   # 横断サービス
├── middlewares.py
└── main.py
```

## URL ルール

- ロール prefix を必ず付ける: `/api/v1/admin/...` `/api/v1/manager/...` `/api/v1/member/...`
- URL segment は kebab-case
- model 名を省略しない（`/columns` ではなく `/data-columns`）

## モデル定義

- ファイル名は `models.py`（複数形）
- 継承: `BaseModel, table=True`
- ForeignKey: `sa_column=Column(..., ForeignKey("...", ondelete=...), nullable=..., index=True)` で `ondelete` 必須
- リレーション双方向: `back_populates` + `cascade_delete=True`
- 循環 import 回避: `if TYPE_CHECKING:`

```python
if TYPE_CHECKING:
    from src.consignors.models import Consignor

consignor: "Consignor" = Relationship(back_populates="items")
```

### Constraints

```python
@dataclass(frozen=True)
class ItemConstraints:
    NAME_MAX_LENGTH: int = 100
```

### Enum

```python
class ItemStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
```

## Cascade Delete

- アプリレベル: `cascade_delete=True`（親削除時に子削除）
- DB レベル `ondelete="CASCADE"` も併用可

## マイグレーション

- **`api/alembic/versions/` の手動編集禁止**（必ず autogenerate）
- ドリフト検査: `sh project_check.sh -acheck`

```bash
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
```

## Factory

```python
class ItemFactory(BaseFactory[Item]):
    title = Faker("sentence")
    _exclude_fields = {"id", "created_at", "updated_at", "consignor_id"}
```

`_exclude_fields` で DB 自動生成・親モデル ID を除外する。

## 環境設定

```python
# ❌ デフォルト値禁止
DATABASE_URL = os.getenv("DATABASE_URL", "default")
# ✅
DATABASE_URL = os.environ["DATABASE_URL"]
```

## Python 環境

- Python 3.13（`pyproject.toml` と整合）
- 仮想環境: `uv venv` 作成、`uv sync --dev` で依存解決
- 全 Python コマンドは `uv run` 経由（asdf シム回避）
