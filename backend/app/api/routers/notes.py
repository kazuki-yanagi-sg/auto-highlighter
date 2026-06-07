"""付箋(StickyNote)のエンドポイント。ユーザーが手動で貼る/編集する。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api import deps
from app.domain.models import StickyNote
from app.repositories.interfaces import DocumentRepository, NoteRepository
from app.schemas import CreateNoteIn, NoteOut, UpdateNoteIn, note_to_out

router = APIRouter(tags=["notes"])


@router.post(
    "/documents/{document_id}/notes",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    document_id: int,
    payload: CreateNoteIn,
    documents: DocumentRepository = Depends(deps.get_document_repository),
    notes: NoteRepository = Depends(deps.get_note_repository),
) -> NoteOut:
    if documents.get(document_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    note = notes.add(
        StickyNote(
            document_id=document_id,
            segment_id=payload.segment_id,
            body=payload.body,
            page=payload.page,
            x=payload.x,
            y=payload.y,
        )
    )
    return note_to_out(note)


@router.get("/documents/{document_id}/notes", response_model=list[NoteOut])
def list_notes(
    document_id: int,
    notes: NoteRepository = Depends(deps.get_note_repository),
) -> list[NoteOut]:
    return [note_to_out(n) for n in notes.list_for_document(document_id)]


@router.patch("/notes/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    payload: UpdateNoteIn,
    notes: NoteRepository = Depends(deps.get_note_repository),
) -> NoteOut:
    note = notes.get(note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    if payload.body is not None:
        note.body = payload.body
    if payload.x is not None:
        note.x = payload.x
    if payload.y is not None:
        note.y = payload.y
    if payload.w is not None:
        note.w = payload.w
    if payload.h is not None:
        note.h = payload.h
    return note_to_out(notes.update(note))


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    notes: NoteRepository = Depends(deps.get_note_repository),
) -> None:
    notes.delete(note_id)
