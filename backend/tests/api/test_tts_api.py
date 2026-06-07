"""ステップ7/P1: TTS(VOICEVOX) API のテスト。GETでストリーミング再生する。

VOICEVOXは conftest の FakeTts(有効なtiny WAVを返す)に差し替え済み。
"""

from app.api import deps
from app.services.tts import TtsService


def _document(client) -> dict:
    # markers: seg0=red, seg2=green (conftest の FakeAnnotator による・背景処理は同期実行済み)
    body = client.post("/documents", json={"url": "https://example.com/a"}).json()
    return client.get(f"/documents/{body['document']['id']}").json()


def test_synthesize_red_streams_wav(client):
    doc = _document(client)
    res = client.get(f"/documents/{doc['id']}/tts", params={"color": "red"})
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"
    # ストリーミングWAVの先頭は RIFF....WAVE ヘッダ
    assert res.content[:4] == b"RIFF"
    assert res.content[8:12] == b"WAVE"


def test_synthesize_returns_422_when_color_has_no_segments(client):
    doc = _document(client)
    res = client.get(f"/documents/{doc['id']}/tts", params={"color": "blue"})
    assert res.status_code == 422


def test_synthesize_invalid_color_returns_422(client):
    doc = _document(client)
    res = client.get(f"/documents/{doc['id']}/tts", params={"color": "purple"})
    assert res.status_code == 422


def test_synthesize_missing_document_returns_404(client):
    res = client.get("/documents/999/tts", params={"color": "red"})
    assert res.status_code == 404


def test_synthesize_propagates_color_specific_text(client):
    """red と green で別の文が選ばれる(色フィルタが効いている)ことを確認。"""

    captured: list[str] = []

    class RecordingTts(TtsService):
        def synthesize(self, text: str) -> bytes:
            captured.append(text)
            from tests.api.conftest import _tiny_wav

            return _tiny_wav()

    client.app.dependency_overrides[deps.get_tts] = lambda: RecordingTts()
    doc = _document(client)
    client.get(f"/documents/{doc['id']}/tts", params={"color": "green"})
    assert any("例えば" in t for t in captured)


def test_synthesize_strips_latex_so_no_backslash_reaches_tts(client, app_db):
    """数式入り記事の音声テキストにバックスラッシュ等のTeX記号が残らない。"""
    from app.domain.models import Color, Document, Segment
    from app.repositories.sqlalchemy_repo import SqlAlchemyDocumentRepository

    repo = SqlAlchemyDocumentRepository(app_db.session())
    doc = repo.add(
        Document(
            url="https://x.com/math",
            title="数式",
            segments=[
                Segment(order=0, text=r"質量は $E = mc^2$ である。", marker=Color.RED),
                Segment(order=1, text=r"{\displaystyle \frac{a}{b}}", marker=Color.RED),
            ],
        )
    )

    captured: list[str] = []

    class RecordingTts(TtsService):
        def synthesize(self, text: str) -> bytes:
            captured.append(text)
            from tests.api.conftest import _tiny_wav

            return _tiny_wav()

    client.app.dependency_overrides[deps.get_tts] = lambda: RecordingTts()
    res = client.get(f"/documents/{doc.id}/tts", params={"color": "red"})
    assert res.status_code == 200
    joined = "".join(captured)
    for bad in ["\\", "$", "{", "}"]:
        assert bad not in joined
    assert "2乗" in joined  # 数式が読みに変換されている
