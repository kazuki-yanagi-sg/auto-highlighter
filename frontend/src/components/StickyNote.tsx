import { useEffect, useRef, useState } from "react";
import type { Note } from "../types";

interface Props {
  note: Note;
  onSave: (noteId: number, body: string) => void;
  onDelete: (noteId: number) => void;
  onMove: (noteId: number, x: number, y: number) => void;
  onResize: (noteId: number, w: number, h: number) => void;
}

const MIN_W = 120;
const MIN_H = 90;

// 紙の上でも黒い余白でも自由に置ける手書き付箋。
// グリップでドラッグ移動、右下ハンドルでリサイズ。位置基準は左上。
export function StickyNote({ note, onSave, onDelete, onMove, onResize }: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(note.body);
  const [pos, setPos] = useState({ x: note.x, y: note.y });
  const [size, setSize] = useState({ w: note.w, h: note.h });
  const posRef = useRef(pos);
  const sizeRef = useRef(size);
  const moveDrag = useRef<{ sx: number; sy: number; ox: number; oy: number } | null>(null);
  const sizeDrag = useRef<{ sx: number; sy: number; ow: number; oh: number } | null>(null);

  useEffect(() => {
    posRef.current = { x: note.x, y: note.y };
    setPos({ x: note.x, y: note.y });
  }, [note.x, note.y]);

  useEffect(() => {
    sizeRef.current = { w: note.w, h: note.h };
    setSize({ w: note.w, h: note.h });
  }, [note.w, note.h]);

  // --- 移動 ---
  function onMoveDown(e: React.PointerEvent) {
    moveDrag.current = { sx: e.clientX, sy: e.clientY, ox: pos.x, oy: pos.y };
    e.currentTarget.setPointerCapture?.(e.pointerId);
  }
  function onMoveMove(e: React.PointerEvent) {
    if (!moveDrag.current) return;
    const next = {
      x: moveDrag.current.ox + (e.clientX - moveDrag.current.sx),
      y: moveDrag.current.oy + (e.clientY - moveDrag.current.sy),
    };
    posRef.current = next;
    setPos(next);
  }
  function onMoveUp() {
    if (!moveDrag.current) return;
    moveDrag.current = null;
    onMove(note.id, posRef.current.x, posRef.current.y);
  }

  // --- リサイズ(右下) ---
  function onSizeDown(e: React.PointerEvent) {
    e.stopPropagation();
    sizeDrag.current = { sx: e.clientX, sy: e.clientY, ow: size.w, oh: size.h };
    e.currentTarget.setPointerCapture?.(e.pointerId);
  }
  function onSizeMove(e: React.PointerEvent) {
    if (!sizeDrag.current) return;
    const next = {
      w: Math.max(MIN_W, sizeDrag.current.ow + (e.clientX - sizeDrag.current.sx)),
      h: Math.max(MIN_H, sizeDrag.current.oh + (e.clientY - sizeDrag.current.sy)),
    };
    sizeRef.current = next;
    setSize(next);
  }
  function onSizeUp() {
    if (!sizeDrag.current) return;
    sizeDrag.current = null;
    onResize(note.id, sizeRef.current.w, sizeRef.current.h);
  }

  return (
    <div
      className="sticky-note"
      data-testid={`note-${note.id}`}
      style={{ left: pos.x, top: pos.y, width: size.w, height: size.h }}
    >
      <div
        className="sticky-grip"
        data-testid={`note-grip-${note.id}`}
        onPointerDown={onMoveDown}
        onPointerMove={onMoveMove}
        onPointerUp={onMoveUp}
      >
        ⠿
      </div>

      {editing ? (
        <>
          <textarea
            value={draft}
            placeholder="メモ"
            onChange={(e) => setDraft(e.target.value)}
          />
          <div className="sticky-note-actions">
            <button
              onClick={() => {
                onSave(note.id, draft);
                setEditing(false);
              }}
            >
              保存
            </button>
            <button onClick={() => setEditing(false)}>取消</button>
          </div>
        </>
      ) : (
        <>
          {note.body ? (
            <p className="sticky-note-body">{note.body}</p>
          ) : (
            <p className="sticky-note-body sticky-note-placeholder">メモ</p>
          )}
          <div className="sticky-note-actions">
            <button onClick={() => setEditing(true)}>編集</button>
            <button onClick={() => onDelete(note.id)}>削除</button>
          </div>
        </>
      )}

      <div
        className="sticky-resize"
        data-testid={`note-resize-${note.id}`}
        onPointerDown={onSizeDown}
        onPointerMove={onSizeMove}
        onPointerUp={onSizeUp}
      />
    </div>
  );
}
