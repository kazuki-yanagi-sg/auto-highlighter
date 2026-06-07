import { useState } from "react";
import { HighlightedText } from "../components/HighlightedText";
import { NotesLayer } from "../reader/NotesLayer";
import { PageSidebar } from "../reader/PageSidebar";
import { ReaderTopBar } from "../reader/ReaderTopBar";
import { TweaksPanel } from "../reader/TweaksPanel";
import { VoicePlayer } from "../reader/VoicePlayer";
import { useReaderSettings } from "../reader/useReaderSettings";
import {
  createNote as defaultCreate,
  deleteNote as defaultDelete,
  updateNote as defaultUpdate,
  type NotePatch,
} from "../api/client";
import type { DocumentData, Note, Progress } from "../types";
import type { CSSProperties } from "react";

interface NoteApi {
  createNote: (
    documentId: number,
    body: string,
    x: number,
    y: number,
    page: number,
    segmentId: number | null,
  ) => Promise<Note>;
  updateNote: (noteId: number, patch: NotePatch) => Promise<Note>;
  deleteNote: (noteId: number) => Promise<void>;
}

interface Props {
  document: DocumentData;
  api?: NoteApi;
  onBack?: () => void;
  progress?: Progress | null;
}

const defaultApi: NoteApi = {
  createNote: defaultCreate,
  updateNote: defaultUpdate,
  deleteNote: defaultDelete,
};

export function ReaderPage({
  document,
  api = defaultApi,
  onBack,
  progress = null,
}: Props) {
  const [settings, updateSettings] = useReaderSettings();
  const [notes, setNotes] = useState<Note[]>(document.notes);
  const [placing, setPlacing] = useState(false);
  const [showTweaks, setShowTweaks] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [page, setPage] = useState(0);

  const pageCount = document.segments.reduce((m, s) => Math.max(m, s.page), 0) + 1;
  const pageSegments = document.segments.filter((s) => s.page === page);
  const pageNotes = notes.filter((n) => n.page === page);

  // 目次: 各ページの先頭セグメント(多くは見出し)をラベルにする
  const pageItems = Array.from({ length: pageCount }, (_, p) => {
    const first = document.segments.find((s) => s.page === p);
    return { page: p, label: first ? first.text.slice(0, 40) : "" };
  });

  async function createAt(x: number, y: number) {
    // 本文は空で作成し、「メモ」はプレースホルダー表示。付箋は現在のページに紐づく。
    const note = await api.createNote(document.id, "", x, y, page, null);
    setNotes((prev) => [...prev, note]);
    setPlacing(false);
  }
  async function move(id: number, x: number, y: number) {
    await api.updateNote(id, { x, y });
    setNotes((prev) => prev.map((n) => (n.id === id ? { ...n, x, y } : n)));
  }
  async function resize(id: number, w: number, h: number) {
    await api.updateNote(id, { w, h });
    setNotes((prev) => prev.map((n) => (n.id === id ? { ...n, w, h } : n)));
  }
  async function save(id: number, body: string) {
    const updated = await api.updateNote(id, { body });
    setNotes((prev) => prev.map((n) => (n.id === id ? updated : n)));
  }
  async function remove(id: number) {
    await api.deleteNote(id);
    setNotes((prev) => prev.filter((n) => n.id !== id));
  }

  const style = {
    "--reading-size": `${settings.sizePx}px`,
    "--mk-opacity": settings.markerOpacity,
    "--accent": settings.accent,
    "--reading-font": settings.font,
  } as CSSProperties;

  return (
    <div className={`reader-root sheet-${settings.sheet}`} style={style}>
      <ReaderTopBar
        document={document}
        onBack={onBack}
        placing={placing}
        onTogglePlacing={() => setPlacing((p) => !p)}
        onToggleTweaks={() => setShowTweaks((s) => !s)}
        onToggleSidebar={() => setSidebarOpen((s) => !s)}
        sidebarOpen={sidebarOpen}
      />

      {progress && progress.status === "processing" && (
        <div className="reader-progress" role="status">
          <div className="reader-progress-bar">
            <span style={{ width: `${progress.percent}%` }} />
          </div>
          <span className="reader-progress-text">
            解析中 {progress.done}/{progress.total}
            {progress.eta_seconds != null && `・残り約${progress.eta_seconds}秒`}
          </span>
        </div>
      )}

      <div className="reader-body">
        {sidebarOpen && pageCount > 1 && (
          <PageSidebar pages={pageItems} current={page} onSelect={setPage} />
        )}

        <main className="reader scroll">
          <div className="reader-stage">
            <article className="paper">
              {document.category && (
                <span className="paper-cat">{document.category}</span>
              )}
              <h1>{document.title}</h1>
              <HighlightedText segments={pageSegments} onSelectSegment={() => {}} />
              {pageCount > 1 && (
                <nav className="page-nav">
                  <button
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page <= 0}
                    aria-label="前のページ"
                  >
                    ← 前へ
                  </button>
                  <span>
                    {page + 1} / 全{pageCount}ページ
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
                    disabled={page >= pageCount - 1}
                    aria-label="次のページ"
                  >
                    次へ →
                  </button>
                </nav>
              )}
            </article>
          </div>
          {/* 付箋レイヤは紙の外(黒い領域)も含む全幅キャンバス。 */}
          <NotesLayer
            notes={pageNotes}
            placing={placing}
            onCreate={createAt}
            onMove={move}
            onResize={resize}
            onSave={save}
            onDelete={remove}
          />
        </main>
      </div>

      <VoicePlayer documentId={document.id} />

      {showTweaks && (
        <TweaksPanel
          settings={settings}
          onChange={updateSettings}
          onClose={() => setShowTweaks(false)}
        />
      )}
    </div>
  );
}
