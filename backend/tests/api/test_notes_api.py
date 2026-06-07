"""ステップ6: Notes(付箋) API のテスト。"""


def _create_document(client) -> dict:
    return client.post("/documents", json={"url": "https://example.com/a"}).json()[
        "document"
    ]


def test_create_and_list_note(client):
    doc = _create_document(client)
    seg_id = doc["segments"][0]["id"]

    res = client.post(
        f"/documents/{doc['id']}/notes",
        json={"segment_id": seg_id, "body": "ここ疑問", "x": 10, "y": 20},
    )
    assert res.status_code == 201
    note = res.json()
    assert note["body"] == "ここ疑問"
    assert note["segment_id"] == seg_id
    assert note["id"] is not None

    listed = client.get(f"/documents/{doc['id']}/notes").json()
    assert [n["body"] for n in listed] == ["ここ疑問"]


def test_update_note_body(client):
    doc = _create_document(client)
    seg_id = doc["segments"][0]["id"]
    note = client.post(
        f"/documents/{doc['id']}/notes",
        json={"segment_id": seg_id, "body": "初版"},
    ).json()

    res = client.patch(f"/notes/{note['id']}", json={"body": "改訂版"})
    assert res.status_code == 200
    assert res.json()["body"] == "改訂版"

    listed = client.get(f"/documents/{doc['id']}/notes").json()
    assert listed[0]["body"] == "改訂版"


def test_delete_note(client):
    doc = _create_document(client)
    seg_id = doc["segments"][0]["id"]
    note = client.post(
        f"/documents/{doc['id']}/notes",
        json={"segment_id": seg_id, "body": "消す"},
    ).json()

    assert client.delete(f"/notes/{note['id']}").status_code == 204
    assert client.get(f"/documents/{doc['id']}/notes").json() == []


def test_create_note_without_segment_at_position(client):
    doc = _create_document(client)
    res = client.post(
        f"/documents/{doc['id']}/notes",
        json={"body": "ここにメモ", "x": 120.5, "y": 240.0},
    )
    assert res.status_code == 201
    note = res.json()
    assert note["segment_id"] is None
    assert note["x"] == 120.5
    assert note["y"] == 240.0


def test_create_note_has_default_size(client):
    doc = _create_document(client)
    note = client.post(
        f"/documents/{doc['id']}/notes", json={"body": "メモ", "x": 10, "y": 10}
    ).json()
    assert note["w"] > 0
    assert note["h"] > 0


def test_update_note_resizes(client):
    doc = _create_document(client)
    note = client.post(
        f"/documents/{doc['id']}/notes", json={"body": "メモ", "x": 0, "y": 0}
    ).json()
    res = client.patch(f"/notes/{note['id']}", json={"w": 260, "h": 200})
    assert res.status_code == 200
    assert res.json()["w"] == 260
    assert res.json()["h"] == 200
    assert res.json()["body"] == "メモ"


def test_update_note_moves_position(client):
    doc = _create_document(client)
    note = client.post(
        f"/documents/{doc['id']}/notes", json={"body": "メモ", "x": 0, "y": 0}
    ).json()

    res = client.patch(f"/notes/{note['id']}", json={"x": 300, "y": 150})
    assert res.status_code == 200
    assert res.json()["x"] == 300
    assert res.json()["y"] == 150
    assert res.json()["body"] == "メモ"  # body は維持


def test_create_note_on_missing_document_returns_404(client):
    res = client.post(
        "/documents/999/notes", json={"segment_id": 1, "body": "x"}
    )
    assert res.status_code == 404


def test_update_missing_note_returns_404(client):
    assert client.patch("/notes/999", json={"body": "x"}).status_code == 404
