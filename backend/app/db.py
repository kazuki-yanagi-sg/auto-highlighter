"""DB接続のセットアップ。URLに応じてエンジンを構築する。

SQLite in-memory はテストで使うため StaticPool で1コネクションを共有する。
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.repositories.orm import Base


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

    def session(self) -> Session:
        return self._session_factory()
