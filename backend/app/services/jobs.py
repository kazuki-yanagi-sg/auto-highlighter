"""解析ジョブの進捗を保持するインメモリストア(スレッドセーフ)。

POST /documents は本文を即保存して job を作り、別スレッドで注釈を進めながら
この store を更新する。フロントは GET /documents/progress/{id} でポーリングする。
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Job:
    id: str
    document_id: int
    status: str = "processing"  # processing | done | error
    done: int = 0
    total: int = 0
    markers: dict[int, str] = field(default_factory=dict)  # order -> color名
    category: str | None = None
    detail: str | None = None
    started_at: float = field(default_factory=time.time)


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, document_id: int) -> str:
        job_id = uuid.uuid4().hex
        with self._lock:
            self._jobs[job_id] = Job(id=job_id, document_id=document_id)
        return job_id

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **fields) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for key, value in fields.items():
                setattr(job, key, value)


# アプリ全体で共有するストア(単一backendプロセス前提)。
store = JobStore()
