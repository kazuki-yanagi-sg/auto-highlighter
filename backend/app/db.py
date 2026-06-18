"""DB接続のセットアップ。URLに応じてエンジンを構築する。

SQLite in-memory はテストで使うため StaticPool で1コネクションを共有する。
"""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.repositories.orm import Base

# create_all は既存テーブルに列を足さないため、後付け列を冪等に追加する軽量マイグレーション。
# (name, ddl) の ddl は ALTER TABLE ... ADD COLUMN の本体。SQLite/Postgres 両対応。
_ADDED_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "segments": [
        ("block", "block INTEGER NOT NULL DEFAULT 0"),
        ("kind", "kind VARCHAR(16) NOT NULL DEFAULT 'text'"),
    ],
}


def _make_engine(url: str):
    if url in ("sqlite://", "sqlite:///:memory:"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    # pool_pre_ping: DB再起動などで切れた接続を使う前に検査し、自動で張り直す
    # (db コンテナが落ちても backend が500を出し続けない)。
    return create_engine(url, pool_pre_ping=True)


class Database:
    def __init__(self, url: str):
        self.engine = _make_engine(url)
        self._session_factory = sessionmaker(
            bind=self.engine, autoflush=False, expire_on_commit=False
        )

    def create_all(self) -> None:
        Base.metadata.create_all(self.engine)
        self._add_missing_columns()

    def _add_missing_columns(self) -> None:
        """既存テーブルに後付け列を冪等に追加する(create_all は列追加しないため)。"""
        inspector = inspect(self.engine)
        tables = set(inspector.get_table_names())
        for table, columns in _ADDED_COLUMNS.items():
            if table not in tables:
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            missing = [(n, ddl) for n, ddl in columns if n not in existing]
            if not missing:
                continue
            with self.engine.begin() as conn:
                for _, ddl in missing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))

    def session(self) -> Session:
        return self._session_factory()
