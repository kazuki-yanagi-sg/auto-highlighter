"""ステップ5/F9: Documents API のテスト(即保存202＋裏で注釈→progress)。

TestClient では BackgroundTasks がレスポンス後に同期実行されるため、POST から戻った時点で
注釈は完了している(progress は done)。
"""

from app.api import deps
from app.services.scraper import ScrapeError, Scraper


def _create(client, url="https://example.com/a"):
    res = client.post("/documents", json={"url": url})
    assert res.status_code == 202
    return res.json()


def test_create_returns_document_and_job_id(client):
    body = _create(client)
    assert "job_id" in body
    doc = body["document"]
    assert doc["id"] is not None
    assert [s["text"] for s in doc["segments"]] == [
        "重要な主張。",
        "ただの説明。",
        "例えば〜。",
    ]


def test_annotation_applied_after_background(client):
    # 背景処理(同期実行済み)後、保存済みドキュメントにマーカーが付いている
    body = _create(client)
    res = client.get(f"/documents/{body['document']['id']}")
    assert res.status_code == 200
    markers = [s["marker"] for s in res.json()["segments"]]
    assert markers == ["red", None, "green"]


def test_progress_reports_done_with_markers(client):
    body = _create(client)
    res = client.get(f"/documents/progress/{body['job_id']}")
    assert res.status_code == 200
    prog = res.json()
    assert prog["status"] == "done"
    assert prog["total"] >= 1
    # markers は order->color。FakeAnnotator は 0=red, 2=green
    assert prog["markers"]["0"] == "red"
    assert prog["markers"]["2"] == "green"
    assert prog["category"] == "技術"


def test_progress_unknown_job_404(client):
    assert client.get("/documents/progress/nope").status_code == 404


def test_get_missing_document_returns_404(client):
    assert client.get("/documents/999").status_code == 404


def test_scrape_failure_returns_502(client):
    class BrokenScraper(Scraper):
        def fetch(self, url):
            raise ScrapeError("失敗")

    client.app.dependency_overrides[deps.get_scraper] = lambda: BrokenScraper()
    res = client.post("/documents", json={"url": "https://example.com/x"})
    assert res.status_code == 502


def test_ai_error_sets_job_status_error(client):
    from app.services.annotator import AiError, Annotator

    class FailingAnnotator(Annotator):
        def _suggest(self, segments):
            raise AiError("quota")

    client.app.dependency_overrides[deps.get_annotator] = lambda: FailingAnnotator()
    body = _create(client)  # POST自体は202(本文は保存済み)
    prog = client.get(f"/documents/progress/{body['job_id']}").json()
    assert prog["status"] == "error"
    assert prog["detail"]
