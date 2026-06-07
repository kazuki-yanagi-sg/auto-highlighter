"""F1: JobStore のテスト。"""

from app.services.jobs import JobStore


def test_create_and_get():
    store = JobStore()
    jid = store.create(document_id=7)
    job = store.get(jid)
    assert job is not None
    assert job.document_id == 7
    assert job.status == "processing"
    assert job.done == 0


def test_update_merges_fields():
    store = JobStore()
    jid = store.create(document_id=1)
    store.update(jid, done=2, total=5, markers={0: "red"})
    store.update(jid, status="done")
    job = store.get(jid)
    assert job.done == 2
    assert job.total == 5
    assert job.markers == {0: "red"}
    assert job.status == "done"


def test_get_unknown_returns_none():
    assert JobStore().get("nope") is None
