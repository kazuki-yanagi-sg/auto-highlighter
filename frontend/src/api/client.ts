import type {
  CreateResult,
  DocumentData,
  DocumentSummary,
  Note,
  Page,
  Progress,
} from "../types";

// vite proxy 経由で backend に届く。/api → backend:8000
const BASE = "/api";

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `リクエストに失敗しました (${res.status})`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") message = body.detail;
    } catch {
      // JSONでなければ既定メッセージのまま
    }
    throw new Error(message);
  }
  return (await res.json()) as T;
}

export async function createDocument(url: string): Promise<CreateResult> {
  const res = await fetch(`${BASE}/documents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return asJson<CreateResult>(res);
}

export async function getProgress(jobId: string): Promise<Progress> {
  return asJson<Progress>(await fetch(`${BASE}/documents/progress/${jobId}`));
}

export async function getDocument(id: number): Promise<DocumentData> {
  return asJson<DocumentData>(await fetch(`${BASE}/documents/${id}`));
}

export async function listDocuments(
  page: number,
  size: number,
  q: string,
  category: string,
): Promise<Page<DocumentSummary>> {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  if (q) params.set("q", q);
  if (category) params.set("category", category);
  return asJson<Page<DocumentSummary>>(
    await fetch(`${BASE}/documents?${params.toString()}`),
  );
}

export async function listCategories(): Promise<string[]> {
  return asJson<string[]>(await fetch(`${BASE}/categories`));
}

export async function deleteDocument(id: number): Promise<void> {
  const res = await fetch(`${BASE}/documents/${id}`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error(`削除に失敗しました (${res.status})`);
  }
}

export async function listNotes(documentId: number): Promise<Note[]> {
  return asJson<Note[]>(await fetch(`${BASE}/documents/${documentId}/notes`));
}

export async function createNote(
  documentId: number,
  body: string,
  x: number,
  y: number,
  page: number,
  segmentId: number | null = null,
): Promise<Note> {
  const res = await fetch(`${BASE}/documents/${documentId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ segment_id: segmentId, body, page, x, y }),
  });
  return asJson<Note>(res);
}

export interface NotePatch {
  body?: string;
  x?: number;
  y?: number;
  w?: number;
  h?: number;
}

export async function updateNote(noteId: number, patch: NotePatch): Promise<Note> {
  const res = await fetch(`${BASE}/notes/${noteId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  return asJson<Note>(res);
}

export async function deleteNote(noteId: number): Promise<void> {
  const res = await fetch(`${BASE}/notes/${noteId}`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error(`削除に失敗しました (${res.status})`);
  }
}

// 音声は <audio src="/api/documents/{id}/tts?color=..."> で直接ストリーミング再生する
// (VoicePlayer 参照)。色ごとの音声取得用クライアント関数は不要になった。
