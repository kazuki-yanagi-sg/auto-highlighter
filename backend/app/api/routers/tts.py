"""色を指定して、その色のマーカーが付いた文だけを音声合成して返すエンドポイント。

長文でも待たせないよう、チャンクごとに合成して逐次ストリーミングする。
`<audio src>` から直接叩けるよう GET にする。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api import deps
from app.repositories.interfaces import DocumentRepository
from app.schemas import color_from_api
from app.services.math_speech import to_speech
from app.services.tts import DEFAULT_MAX_CHARS, TtsService, _chunk_text, stream_wav

router = APIRouter(tags=["tts"])


@router.get("/documents/{document_id}/tts")
def synthesize(
    document_id: int,
    color: str,
    documents: DocumentRepository = Depends(deps.get_document_repository),
    tts: TtsService = Depends(deps.get_tts),
) -> StreamingResponse:
    document = documents.get(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")

    parsed = color_from_api(color)
    if parsed is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"未知の色です: {color}",
        )

    texts = [s.text for s in document.segments if s.marker == parsed]
    if not texts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="その色のマーカーは付いていません",
        )

    # 数式を日本語の読みに変換してから合成(VOICEVOXにバックスラッシュを渡さない)。
    spoken = "\n".join(to_speech(t) for t in texts)
    chunks = _chunk_text(spoken, DEFAULT_MAX_CHARS)
    return StreamingResponse(stream_wav(chunks, tts), media_type="audio/wav")
