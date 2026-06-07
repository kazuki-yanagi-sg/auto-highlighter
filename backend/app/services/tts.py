"""テキストを音声(WAV)に変換する TtsService と、ストリーミング再生用のユーティリティ。

長文を1回で合成するとVOICEVOXが遅く(かつOOMしやすい)なるため、
テキストを小さなチャンクに分割し、`stream_wav` が各チャンクを順に合成しながら
「先頭に1回だけWAVヘッダ → 以降は各チャンクのPCMフレーム」を逐次 yield する。
これで最初の一句が数秒で鳴り始め、連続再生できる。

- TtsService.synthesize(text) は「1チャンク=1往復=1完全WAV」を返すプリミティブ(SRP)。
- チャンク分割(`_chunk_text`)とストリーミング組立(`stream_wav`)はサービス層の関数。
"""

from __future__ import annotations

import io
import struct
import wave
from abc import ABC, abstractmethod
from collections.abc import Iterator

import httpx

# 1チャンクあたりの最大文字数。VOICEVOXのレイテンシ/メモリを抑える。
DEFAULT_MAX_CHARS = 120

# チャンクを切る際に優先する文末記号。
_SENTENCE_ENDINGS = "。.!?！？"

# ストリーミングWAVの data 長に入れる「未知(巨大)」値。プレイヤーが途中で止まらないように。
_STREAM_DATA_SIZE = 0xFFFFFFFF - 64


class TtsError(Exception):
    """音声合成に失敗したことを表す。"""


def _chunk_text(text: str, max_chars: int) -> list[str]:
    """text を max_chars 以下のチャンクに分割する。改行・文末で優先的に区切る。"""
    chunks: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        while len(line) > max_chars:
            cut = _find_cut(line, max_chars)
            chunks.append(line[:cut].strip())
            line = line[cut:].strip()
        if line:
            chunks.append(line)
    return chunks


def _find_cut(line: str, max_chars: int) -> int:
    """max_chars 以内でできるだけ後ろの文末記号の直後を切れ目に。無ければ max_chars。"""
    window = line[:max_chars]
    best = max((window.rfind(ch) for ch in _SENTENCE_ENDINGS), default=-1)
    if best >= 0:
        return best + 1
    return max_chars


class TtsService(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """1チャンク分のテキストを合成し、完全なWAVバイト列を返す。"""


def _build_streaming_header(params: wave._wave_params) -> bytes:
    """data長を巨大値にした44バイトのWAVヘッダ(ストリーミング再生用)。"""
    byte_rate = params.framerate * params.nchannels * params.sampwidth
    block_align = params.nchannels * params.sampwidth
    bits = params.sampwidth * 8
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        _STREAM_DATA_SIZE + 36,
        b"WAVE",
        b"fmt ",
        16,
        1,  # PCM
        params.nchannels,
        params.framerate,
        byte_rate,
        block_align,
        bits,
        b"data",
        _STREAM_DATA_SIZE,
    )


def _pcm_frames(wav_bytes: bytes) -> bytes:
    with wave.open(io.BytesIO(wav_bytes)) as reader:
        return reader.readframes(reader.getnframes())


def _wav_params(wav_bytes: bytes) -> wave._wave_params:
    with wave.open(io.BytesIO(wav_bytes)) as reader:
        return reader.getparams()


def stream_wav(chunks: list[str], tts: TtsService) -> Iterator[bytes]:
    """チャンクを順に合成し、先頭ヘッダ＋各チャンクPCMを逐次 yield する。"""
    header_sent = False
    for chunk in chunks:
        wav = tts.synthesize(chunk)
        if not header_sent:
            yield _build_streaming_header(_wav_params(wav))
            header_sent = True
        yield _pcm_frames(wav)


class VoicevoxTts(TtsService):
    def __init__(
        self,
        base_url: str,
        speaker: int = 1,
        client: httpx.Client | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._speaker = speaker
        self._client = client or httpx.Client(timeout=60.0)

    def synthesize(self, text: str) -> bytes:
        try:
            query = self._client.post(
                f"{self._base_url}/audio_query",
                params={"text": text, "speaker": self._speaker},
            )
            query.raise_for_status()
            audio = self._client.post(
                f"{self._base_url}/synthesis",
                params={"speaker": self._speaker},
                json=query.json(),
            )
            audio.raise_for_status()
        except httpx.HTTPError as exc:
            raise TtsError("音声合成に失敗しました") from exc
        return audio.content
