import { useEffect, useRef, useState } from "react";
import { LibraryPage } from "./pages/LibraryPage";
import { ReaderPage } from "./pages/ReaderPage";
import { createDocument, getDocument, getProgress } from "./api/client";
import type { DocumentData, Progress } from "./types";

const POLL_MS = 500;

function mergeProgress(doc: DocumentData, p: Progress): DocumentData {
  return {
    ...doc,
    category: p.category ?? doc.category,
    segments: doc.segments.map((s) => ({
      ...s,
      marker: p.markers[String(s.order)] ?? s.marker,
    })),
  };
}

export function App() {
  const [doc, setDoc] = useState<DocumentData | null>(null);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function stopPolling() {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }
  }
  useEffect(() => stopPolling, []);

  function poll(jobId: string) {
    const tick = async () => {
      try {
        const p = await getProgress(jobId);
        setProgress(p);
        setDoc((prev) => (prev ? mergeProgress(prev, p) : prev));
        if (p.status === "processing") {
          timer.current = setTimeout(tick, POLL_MS);
        }
      } catch {
        // 進捗取得に失敗したらポーリング停止(本文は開けている)
      }
    };
    tick();
  }

  async function load(url: string) {
    setLoading(true);
    setError(null);
    setProgress(null);
    stopPolling();
    try {
      const { document, job_id } = await createDocument(url);
      setDoc(document); // 本文をすぐ開く(色は後から付く)
      poll(job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  }

  async function open(id: number) {
    setError(null);
    setProgress(null);
    stopPolling();
    try {
      setDoc(await getDocument(id)); // 既存記事は解析済み
    } catch (e) {
      setError(e instanceof Error ? e.message : "記事を開けませんでした");
    }
  }

  function back() {
    stopPolling();
    setProgress(null);
    setDoc(null);
  }

  if (doc) {
    return (
      <ReaderPage
        key={doc.id}
        document={doc}
        progress={progress}
        onBack={back}
      />
    );
  }
  return (
    <LibraryPage
      onOpen={open}
      onSubmitUrl={load}
      loading={loading}
      error={error}
    />
  );
}
