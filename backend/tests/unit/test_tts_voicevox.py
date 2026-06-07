"""VoicevoxTts と音声ストリーミングのテスト。

巨大テキストを1回で送るとVOICEVOXがOOMで落ち、かつ返りも遅い。そこで
- synthesize は「1チャンク=1往復=1WAV」のプリミティブ
- stream_wav が、チャンクを順に合成して「先頭ヘッダ＋各チャンクPCM」を逐次 yield
する設計を検証する。VOICEVOX本体は MockTransport で差し替える。
"""

import io
import wave

import httpx
import pytest

from app.services.tts import (
    TtsError,
    VoicevoxTts,
    _chunk_text,
    stream_wav,
)


def _tiny_wav(nframes: int = 100) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(b"\x00\x00" * nframes)
    return buf.getvalue()


def _client(counter: dict, synthesis_status: int = 200) -> httpx.Client:
    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path.endswith("/audio_query"):
            return httpx.Response(200, json={"dummy": True})
        if req.url.path.endswith("/synthesis"):
            counter["synthesis"] = counter.get("synthesis", 0) + 1
            return httpx.Response(synthesis_status, content=_tiny_wav())
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


# --- チャンク分割 ---
def test_chunk_text_splits_long_text_within_limit():
    chunks = _chunk_text("あいうえお。かきくけこ。さしすせそ。", max_chars=8)
    assert chunks
    assert all(len(c) <= 8 for c in chunks)


def test_chunk_text_keeps_short_text_as_one():
    assert _chunk_text("短い文。", max_chars=200) == ["短い文。"]


# --- synthesize は1往復で1WAV ---
def test_synthesize_one_chunk_single_roundtrip():
    counter: dict = {}
    tts = VoicevoxTts("http://vv:50021", client=_client(counter))
    wav = tts.synthesize("短い文。")
    assert counter["synthesis"] == 1
    with wave.open(io.BytesIO(wav)) as w:
        assert w.getframerate() == 24000


def test_synthesize_raises_ttserror_on_http_failure():
    counter: dict = {}
    tts = VoicevoxTts("http://vv:50021", client=_client(counter, synthesis_status=500))
    with pytest.raises(TtsError):
        tts.synthesize("短い文。")


# --- stream_wav: 先頭ヘッダ＋各チャンクPCM ---
def test_stream_wav_yields_header_then_pcm_per_chunk():
    counter: dict = {}
    tts = VoicevoxTts("http://vv:50021", client=_client(counter))
    chunks = ["12345", "67890", "abcde"]

    parts = list(stream_wav(chunks, tts))

    # 各チャンクを合成している
    assert counter["synthesis"] == 3
    # 最初のパートはWAVヘッダ(RIFF....WAVE)
    assert parts[0][:4] == b"RIFF"
    assert parts[0][8:12] == b"WAVE"
    # 2つ目以降は生PCM(RIFFヘッダを含まない)
    assert all(p[:4] != b"RIFF" for p in parts[1:])
    # 全体を連結すると wave で読める(チャンク数×100フレーム)
    blob = b"".join(parts)
    # ストリーミング用にdata長は巨大値なので、PCMバイト数から実フレームを数える
    pcm = b"".join(parts[1:])
    assert len(pcm) == 3 * 100 * 2  # 3チャンク × 100フレーム × 2バイト
    assert blob[:4] == b"RIFF"


def test_stream_wav_empty_chunks_yields_nothing():
    counter: dict = {}
    tts = VoicevoxTts("http://vv:50021", client=_client(counter))
    assert list(stream_wav([], tts)) == []
