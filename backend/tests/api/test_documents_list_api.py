"""P5: 一覧(ページネーション/検索/カテゴリ)API と categories API のテスト。"""

import pytest

from app.domain.models import Document, Segment
from app.repositories.sqlalchemy_repo import SqlAlchemyDocumentRepository


@pytest.fixture()
def seeded(app_db):
    repo = SqlAlchemyDocumentRepository(app_db.session())
    repo.add(Document(url="https://a.com/python", title="Python入門", category="技術",
                      segments=[Segment(order=0, text="x。")]))
    repo.add(Document(url="https://b.com/economy", title="経済の話", category="ビジネス",
                      segments=[Segment(order=0, text="y。")]))
    repo.add(Document(url="https://c.com/python-web", title="Web開発", category="技術",
                      segments=[Segment(order=0, text="z。")]))
    return app_db


def test_list_paginated(client, seeded):
    res = client.get("/documents", params={"page": 1, "size": 2})
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["size"] == 2
    assert len(body["items"]) == 2
    # 新しい順 + サマリは category を持つ/segmentsは持たない
    assert body["items"][0]["title"] == "Web開発"
    assert body["items"][0]["category"] == "技術"
    assert "segments" not in body["items"][0]


def test_list_search_query(client, seeded):
    res = client.get("/documents", params={"q": "python"})
    titles = {i["title"] for i in res.json()["items"]}
    assert titles == {"Python入門", "Web開発"}


def test_list_category_filter(client, seeded):
    res = client.get("/documents", params={"category": "ビジネス"})
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "経済の話"


def test_categories_endpoint(client, seeded):
    res = client.get("/categories")
    assert res.status_code == 200
    assert sorted(res.json()) == ["ビジネス", "技術"]


def test_delete_document_removes_it_and_notes(client):
    body = client.post("/documents", json={"url": "https://example.com/a"}).json()
    doc_id = body["document"]["id"]
    seg_id = body["document"]["segments"][0]["id"]
    client.post(
        f"/documents/{doc_id}/notes", json={"segment_id": seg_id, "body": "メモ"}
    )

    assert client.delete(f"/documents/{doc_id}").status_code == 204
    assert client.get(f"/documents/{doc_id}").status_code == 404
    assert client.get(f"/documents/{doc_id}/notes").json() == []


def test_delete_unknown_document_is_idempotent(client):
    assert client.delete("/documents/999").status_code == 204


def test_delete_reduces_list_total(client, seeded):
    before = client.get("/documents").json()["total"]
    first_id = client.get("/documents").json()["items"][0]["id"]
    client.delete(f"/documents/{first_id}")
    assert client.get("/documents").json()["total"] == before - 1


def test_create_document_now_has_category(client):
    # conftest の FakeCategorizer は "技術"。カテゴリは背景処理(同期実行済み)で付く。
    res = client.post("/documents", json={"url": "https://example.com/a"})
    assert res.status_code == 202
    doc_id = res.json()["document"]["id"]
    got = client.get(f"/documents/{doc_id}")
    assert got.json()["category"] == "技術"
