---
paths:
  - "api/tests/**/*.py"
  - "api/**/test_*.py"
  - "api/**/conftest.py"
  - "api/src/**/factories.py"
---

# Backend テストコード規約

## ディレクトリ構成

```text
api/tests/
├── conftest.py              # 横断 fixture（DB、認証、HTTP client 等）
├── helpers/                 # 横断ヘルパー、共通アサーション
│   ├── common.py            # create_and_persist_*, create_auth_headers
│   └── assertions.py
├── mocks/                   # モック・スタブ
├── unit/                    # モック使用、高速
│   └── <domain>/            # 例: unit/consignors/, unit/auth/
└── integration/             # 実 DB（testcontainers）使用
    └── <domain>/
```

- `testpaths = ["tests"]`（`api/pyproject.toml`）
- Factory は `api/src/<domain>/factories.py` に配置（本体 dir 直下、本番 seed/migration からも使用）

## pytest マーカー

| マーカー | サイズ | 対象 |
|---|---|---|
| `@pytest.mark.small` | <100ms | ビジネスロジック、バリデーション、純粋データ変換 |
| `@pytest.mark.medium` | 100ms〜1s | API エンドポイント、DB 操作、認証・認可、WebSocket |
| `@pytest.mark.large` | >1s | E2E。極力使わない |

Small は **モック使用**、Medium は **testcontainers で実 DB**。

`pytest-asyncio` は `asyncio_mode = "auto"`（`api/pyproject.toml`）。`@pytest.mark.asyncio` の明示は不要。

```python
@pytest.mark.medium
class TestMemberItemsCRUD:
    async def test_create_item_success(
        self, async_client: AsyncClient, db_session: Session
    ) -> None:
        # Arrange
        user = create_and_persist_user(db_session, AccountType.MEMBER)
        headers = create_auth_headers(user)
        create_data = {"title": "新規"}

        # Act
        response = await async_client.post("/api/v1/member/items", json=create_data, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["title"] == "新規"
```

## 命名規則

### テストメソッド

```python
def test_<対象>_<状況/条件>_<期待結果>(self) -> None:
```

- メソッド名は英語で書け。日本語を使うな

例:
- `test_create_item_success`
- `test_authentication_required`
- `test_admin_privilege_enforcement_integration`

### テストクラス

```python
@pytest.mark.small  # または @pytest.mark.medium
class TestItemPolicy:
    """ItemPolicy のテスト（目的の説明）"""

    def test_admin_can_delete(self) -> None:
        """admin は自分でない item も削除できる"""
        # Arrange / Act / Assert
```

## Factory パターン

`api/src/<domain>/factories.py` に配置。

| メソッド | 用途 | DB アクセス |
|---|---|---|
| `Factory.build()` | Unit Test 用、DB 永続化なし | なし |
| `Factory()` | Integration Test 用、DB 永続化 | あり |
| `Factory.build_dict()` | API リクエスト用 dict 生成 | なし |

`_exclude_fields` で DB 自動生成（`id`, `created_at`, `updated_at`）と親モデル ID を除外する。

```python
class ItemFactory(BaseFactory[Item]):
    _exclude_fields = {
        "id", "created_at", "updated_at",
        "consignor_id",
    }
    class Meta:
        model = Item

    title: str = Faker("sentence", nb_words=4)
```

## 共通ヘルパー

Integration Test では `api/tests/helpers/common.py` の共通ヘルパーを使う。**テストファイル内にローカルヘルパーを定義しない**。

- 命名規則: `create_and_persist_<model名>`
- 必須パラメータ: `db_session: Session`

```python
user = create_and_persist_user(db_session, AccountType.MEMBER)
item = create_and_persist_item(db_session, user.id, title="テスト")
headers = create_auth_headers(user)
```

## モック

| 使う | 使うな |
|---|---|
| 外部サービス | DB（testcontainers で実 DB） |
| 非決定的処理（時刻・乱数） | 検証対象のビジネスロジック |
| I/O、エラー条件 | - |

```python
# 同期: MagicMock(spec=Session)
# 非同期: AsyncMock を patch に渡す
with patch("src.websocket.events.handlers.emit_event", new=AsyncMock()) as mock_emit:
    await some_async_function()
    mock_emit.assert_called_once()
```

## アサーション

`api/tests/helpers/assertions.py` のヘルパーを使う。

- `assert_api_response(response, expected_status=200)` → JSON 自動パース・診断情報付き
- `assert_error_response(response, expected_status=422)`
- 命名規則: `assert_<検証対象>`、診断情報必須

```python
with pytest.raises(HTTPException) as exc_info:
    await bulk_update(request, mock_session, user)
assert exc_info.value.status_code == 404
```
