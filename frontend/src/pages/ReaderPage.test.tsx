import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReaderPage } from "./ReaderPage";
import type { DocumentData, Note } from "../types";

beforeAll(() => {
  HTMLMediaElement.prototype.play = () => Promise.resolve();
  HTMLMediaElement.prototype.pause = () => {};
});
beforeEach(() => localStorage.clear());

const doc: DocumentData = {
  id: 1,
  url: "https://example.com/a",
  title: "サンプル記事",
  category: "技術",
  segments: [
    { id: 10, order: 0, text: "重要な主張。", marker: "red", page: 0 },
    { id: 11, order: 1, text: "ただの説明。", marker: null, page: 0 },
    { id: 12, order: 2, text: "二ページ目の文。", marker: null, page: 1 },
  ],
  notes: [
    { id: 99, document_id: 1, segment_id: null, body: "既存メモ", page: 0, x: 20, y: 30, w: 176, h: 150 },
    { id: 98, document_id: 1, segment_id: null, body: "二頁の付箋", page: 1, x: 20, y: 30, w: 176, h: 150 },
  ],
};

function fakeApi(over = {}) {
  return {
    createNote: vi.fn(
      async (
        documentId: number,
        body: string,
        x: number,
        y: number,
        page: number,
      ): Promise<Note> => ({
        id: 100,
        document_id: documentId,
        segment_id: null,
        body,
        page,
        x,
        y,
        w: 176,
        h: 150,
      }),
    ),
    updateNote: vi.fn(async (id: number): Promise<Note> => ({
      id,
      document_id: 1,
      segment_id: null,
      body: "x",
      page: 0,
      x: 0,
      y: 0,
      w: 176,
      h: 150,
    })),
    deleteNote: vi.fn(async () => {}),
    ...over,
  };
}

// 本文(reader-text)に限定して探す。目次サイドバーは同じ見出し文を持つため。
function body(container: HTMLElement) {
  return within(container.querySelector(".reader-text") as HTMLElement);
}

test("タイトル・カテゴリ・本文・既存付箋を表示する", () => {
  const { container } = render(<ReaderPage document={doc} api={fakeApi()} />);
  expect(
    screen.getByRole("heading", { name: "サンプル記事" }),
  ).toBeInTheDocument();
  expect(body(container).getByText("重要な主張。")).toHaveClass("mk-red");
  expect(screen.getByText("既存メモ")).toBeInTheDocument();
});

test("ページ送りで表示する文と付箋が切り替わる", async () => {
  const { container } = render(<ReaderPage document={doc} api={fakeApi()} />);
  // 1ページ目(本文)
  expect(body(container).getByText("重要な主張。")).toBeInTheDocument();
  expect(body(container).queryByText("二ページ目の文。")).not.toBeInTheDocument();
  // 付箋(ページ単位)
  expect(screen.getByText("既存メモ")).toBeInTheDocument();
  expect(screen.queryByText("二頁の付箋")).not.toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: "次のページ" }));

  // 2ページ目
  expect(body(container).getByText("二ページ目の文。")).toBeInTheDocument();
  expect(body(container).queryByText("重要な主張。")).not.toBeInTheDocument();
  expect(screen.getByText("二頁の付箋")).toBeInTheDocument();
  expect(screen.queryByText("既存メモ")).not.toBeInTheDocument();
});

test("設定パネルを開閉できる", async () => {
  render(<ReaderPage document={doc} api={fakeApi()} />);
  expect(screen.queryByText("Tweaks")).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: /設定/ }));
  expect(screen.getByText("Tweaks")).toBeInTheDocument();
  expect(screen.getByText("読書面")).toBeInTheDocument();
});

test("付箋追加モードで紙をクリックすると createNote が呼ばれる", async () => {
  const api = fakeApi();
  render(<ReaderPage document={doc} api={api} />);
  await userEvent.click(screen.getByRole("button", { name: /付箋/ }));
  await userEvent.click(screen.getByTestId("notes-layer"));
  expect(api.createNote).toHaveBeenCalled();
});

test("戻るボタンで onBack が呼ばれる", async () => {
  const onBack = vi.fn();
  render(<ReaderPage document={doc} api={fakeApi()} onBack={onBack} />);
  await userEvent.click(screen.getByRole("button", { name: "一覧へ戻る" }));
  expect(onBack).toHaveBeenCalled();
});
