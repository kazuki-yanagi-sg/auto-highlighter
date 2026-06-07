import { StickyNote } from "../components/StickyNote";
import type { Note } from "../types";

interface Props {
  notes: Note[];
  placing: boolean; // 配置モード中か
  onCreate: (x: number, y: number) => void;
  onMove: (noteId: number, x: number, y: number) => void;
  onResize: (noteId: number, w: number, h: number) => void;
  onSave: (noteId: number, body: string) => void;
  onDelete: (noteId: number) => void;
}

// 紙に重ねる付箋レイヤ。配置モード中はクリックした位置に付箋を作る。
export function NotesLayer({
  notes,
  placing,
  onCreate,
  onMove,
  onResize,
  onSave,
  onDelete,
}: Props) {
  function handleClick(e: React.MouseEvent<HTMLDivElement>) {
    if (!placing) return;
    const rect = e.currentTarget.getBoundingClientRect();
    onCreate(e.clientX - rect.left, e.clientY - rect.top);
  }

  return (
    <div
      className={`notes-layer ${placing ? "placing" : ""}`}
      data-testid="notes-layer"
      onClick={handleClick}
    >
      {notes.map((note) => (
        <StickyNote
          key={note.id}
          note={note}
          onSave={onSave}
          onDelete={onDelete}
          onMove={onMove}
          onResize={onResize}
        />
      ))}
    </div>
  );
}
