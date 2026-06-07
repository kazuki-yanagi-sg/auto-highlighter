import { fireEvent, render, screen } from "@testing-library/react";
import { NotesLayer } from "./NotesLayer";
import type { Note } from "../types";

const notes: Note[] = [
  { id: 1, document_id: 1, segment_id: null, body: "メモ1", page: 0, x: 30, y: 40, w: 176, h: 150 },
];

const handlers = {
  onCreate: () => {},
  onMove: () => {},
  onResize: () => {},
  onSave: () => {},
  onDelete: () => {},
};

test("既存の付箋を座標に描画する", () => {
  render(<NotesLayer notes={notes} placing={false} {...handlers} />);
  expect(screen.getByText("メモ1")).toBeInTheDocument();
  expect(screen.getByTestId("note-1")).toHaveStyle({ left: "30px", top: "40px" });
});

test("配置モードで紙をクリックすると onCreate がクリック座標で呼ばれる", () => {
  const onCreate = vi.fn();
  render(
    <NotesLayer notes={[]} placing={true} {...handlers} onCreate={onCreate} />,
  );
  const layer = screen.getByTestId("notes-layer");
  fireEvent.click(layer, { clientX: 0, clientY: 0 });
  expect(onCreate).toHaveBeenCalledTimes(1);
  // 引数は (x, y) の2つ
  expect(onCreate.mock.calls[0]).toHaveLength(2);
});

test("配置モードでないときはクリックしても onCreate を呼ばない", () => {
  const onCreate = vi.fn();
  render(
    <NotesLayer notes={[]} placing={false} {...handlers} onCreate={onCreate} />,
  );
  fireEvent.click(screen.getByTestId("notes-layer"), { clientX: 5, clientY: 5 });
  expect(onCreate).not.toHaveBeenCalled();
});
