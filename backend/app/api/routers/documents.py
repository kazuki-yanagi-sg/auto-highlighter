"""ドキュメント関連のエンドポイント。router は薄く保ち、処理は DocumentService に委譲する。

POST は本文を即保存して 202 で返し、注釈は別スレッドで進めて progress で配信する(即開き＋追記)。
"""

from __future__ import annotations

import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.api import deps
from app.db import Database
from app.repositories.interfaces import DocumentRepository
from app.repositories.sqlalchemy_repo import SqlAlchemyDocumentRepository
from app.schemas import (
    CreateDocumentIn,
    CreateDocumentOut,
    DocumentOut,
    JobProgressOut,
    PageOut,
    document_to_out,
    summary_to_out,
)
from app.services.annotator import AiError, Annotator
from app.services.categorizer import Categorizer
from app.services.document_service import DocumentService
from app.services.jobs import store as job_store
from app.services.scraper import ScrapeError, Scraper

router = APIRouter(prefix="/documents", tags=["documents"])

# カテゴリ一覧は /documents/{id} と衝突しないよう別ルータ(プレフィックスなし)で公開する。
categories_router = APIRouter(tags=["documents"])


@categories_router.get("/categories", response_model=list[str])
def list_categories(
    repository: DocumentRepository = Depends(deps.get_document_repository),
) -> list[str]:
    return repository.list_categories()


def _run_annotation(job_id, document, scraper, annotator, categorizer, database):
    """別スレッドで注釈を進める。自前の session を開き、進捗を job_store に反映する。"""
    session = database.session()
    try:
        repo = SqlAlchemyDocumentRepository(session)
        service = DocumentService(scraper, annotator, categorizer, repo)

        def progress(done: int, total: int, markers: dict[int, str]) -> None:
            job_store.update(job_id, done=done, total=total, markers=markers)

        service.annotate_document(document, progress=progress)
        category = repo.get(document.id)
        job_store.update(
            job_id,
            status="done",
            category=category.category if category else None,
        )
    except AiError:
        job_store.update(
            job_id,
            status="error",
            detail="AIが混雑しているか利用上限に達しました。少し待って再試行してください。",
        )
    except Exception:  # noqa: BLE001 - 何が起きても500ではなくジョブのerrorに
        job_store.update(job_id, status="error", detail="解析に失敗しました。")
    finally:
        session.close()


@router.post("", response_model=CreateDocumentOut, status_code=status.HTTP_202_ACCEPTED)
def create_document(
    payload: CreateDocumentIn,
    background: BackgroundTasks,
    scraper: Scraper = Depends(deps.get_scraper),
    annotator: Annotator = Depends(deps.get_annotator),
    categorizer: Categorizer = Depends(deps.get_categorizer),
    repository: DocumentRepository = Depends(deps.get_document_repository),
    database: Database = Depends(deps.get_database),
) -> CreateDocumentOut:
    service = DocumentService(scraper, annotator, categorizer, repository)
    try:
        document = service.prepare_from_url(payload.url)
    except ScrapeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    # 注釈はレスポンス送信後に裏で進める(本文はすぐ開ける)。
    job_id = job_store.create(document.id)
    background.add_task(
        _run_annotation, job_id, document, scraper, annotator, categorizer, database
    )
    return CreateDocumentOut(document=document_to_out(document), job_id=job_id)


@router.get("/progress/{job_id}", response_model=JobProgressOut)
def get_progress(job_id: str) -> JobProgressOut:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")

    eta = None
    if job.done > 0 and job.status == "processing":
        elapsed = time.time() - job.started_at
        eta = round(elapsed / job.done * (job.total - job.done))
    percent = round(job.done / job.total * 100) if job.total else 0
    return JobProgressOut(
        status=job.status,
        done=job.done,
        total=job.total,
        percent=percent,
        eta_seconds=eta,
        category=job.category,
        markers=job.markers,
        detail=job.detail,
    )


@router.get("", response_model=PageOut)
def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    category: str | None = None,
    repository: DocumentRepository = Depends(deps.get_document_repository),
) -> PageOut:
    items = repository.list_summaries(page=page, size=size, query=q, category=category)
    total = repository.count(query=q, category=category)
    return PageOut(
        items=[summary_to_out(s) for s in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    repository: DocumentRepository = Depends(deps.get_document_repository),
) -> DocumentOut:
    document = repository.get(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return document_to_out(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    repository: DocumentRepository = Depends(deps.get_document_repository),
) -> None:
    repository.delete(document_id)
