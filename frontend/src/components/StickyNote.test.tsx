import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StickyNote } from "./StickyNote";
import type { Note } from "../types";

const note: Note = {
  id: 5,
  document_id: 1,
  segment_id: null,
  body: "ここ疑問",
  page: 0,
  x: 10,
  y: 20,
  w: 176,
  h: 150,
};

const noop = () => {};
const handlers = { onSave: noop, onDelete: noop, onMove: noop, onResize: noop };

test("本文・座標・サイズを反映する", () => {
  render(<StickyNote note={note} {...handlers} />);
  expect(screen.getByText("ここ疑問")).toBeInTheDocument();
  const el = screen.getByTestId("note-5");
  expect(el).toHaveStyle({ left: "10px", top: "20px", width: "176px", height: "150px" });
});

test("本文が空のときは「メモ」をプレースホルダー表示する", () => {
  render(<StickyNote note={{ ...note, body: "" }} {...handlers} />);
  const ph = screen.getByText("メモ");
  expect(ph).toHaveClass("sticky-note-placeholder");
});

test("削除ボタンで onDelete が呼ばれる", async () => {
  const onDelete = vi.fn();
  render(<StickyNote note={note} {...handlers} onDelete={onDelete} />);
  await userEvent.click(screen.getByRole("button", { name: "削除" }));
  expect(onDelete).toHaveBeenCalledWith(5);
});

test("編集して保存すると onSave が呼ばれる", async () => {
  const onSave = vi.fn();
  render(<StickyNote note={note} {...handlers} onSave={onSave} />);
  await userEvent.click(screen.getByRole("button", { name: "編集" }));
  const box = screen.getByRole("textbox");
  await userEvent.clear(box);
  await userEvent.type(box, "やっぱり重要");
  await userEvent.click(screen.getByRole("button", { name: "保存" }));
  expect(onSave).toHaveBeenCalledWith(5, "やっぱり重要");
});

test("グリップのドラッグで onMove(新しい座標) が呼ばれる", () => {
  const onMove = vi.fn();
  render(<StickyNote note={note} {...handlers} onMove={onMove} />);
  const grip = screen.getByTestId("note-grip-5");
  fireEvent.pointerDown(grip, { clientX: 0, clientY: 0, pointerId: 1 });
  fireEvent.pointerMove(grip, { clientX: 30, clientY: 40, pointerId: 1 });
  fireEvent.pointerUp(grip, { pointerId: 1 });
  expect(onMove).toHaveBeenCalledWith(5, 40, 60); // x:10+30, y:20+40
});

test("右下ハンドルのドラッグで onResize(新しいサイズ) が呼ばれる", () => {
  const onResize = vi.fn();
  render(<StickyNote note={note} {...handlers} onResize={onResize} />);
  const handle = screen.getByTestId("note-resize-5");
  fireEvent.pointerDown(handle, { clientX: 0, clientY: 0, pointerId: 1 });
  fireEvent.pointerMove(handle, { clientX: 50, clientY: 40, pointerId: 1 });
  fireEvent.pointerUp(handle, { pointerId: 1 });
  expect(onResize).toHaveBeenCalledWith(5, 226, 190); // w:176+50, h:150+40
});

test("最小サイズより小さくはならない", () => {
  const onResize = vi.fn();
  render(<StickyNote note={note} {...handlers} onResize={onResize} />);
  const handle = screen.getByTestId("note-resize-5");
  fireEvent.pointerDown(handle, { clientX: 0, clientY: 0, pointerId: 1 });
  fireEvent.pointerMove(handle, { clientX: -500, clientY: -500, pointerId: 1 });
  fireEvent.pointerUp(handle, { pointerId: 1 });
  const [, w, h] = onResize.mock.calls[0];
  expect(w).toBeGreaterThanOrEqual(120);
  expect(h).toBeGreaterThanOrEqual(90);
});
