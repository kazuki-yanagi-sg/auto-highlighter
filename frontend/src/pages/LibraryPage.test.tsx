import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LibraryPage } from "./LibraryPage";
import type { DocumentSummary, Page } from "../types";

const zero = { red: 0, yellow: 0, blue: 0, green: 0 };

function page(items: DocumentSummary[], total: number, p = 1): Page<DocumentSummary> {
  return { items, total, page: p, size: 9 };
}

const docs: DocumentSummary[] = [
  {
    id: 3, url: "https://c.com", title: "Web開発", category: "技術",
    created_at: "2026-06-01T00:00:00", marker_counts: { ...zero, red: 2 }, note_count: 1,
  },
  {
    id: 2, url: "https://b.com", title: "経済の話", category: "ビジネス",
    created_at: "2026-06-02T00:00:00", marker_counts: { ...zero }, note_count: 0,
  },
];

function fakeApi(over = {}) {
  return {
    listDocuments: vi.fn(async () => page(docs, 2)),
    listCategories: vi.fn(async () => ["技術", "ビジネス"]),
    deleteDocument: vi.fn(async () => {}),
    ...over,
  };
}

const base = { onOpen: () => {}, onSubmitUrl: () => {}, loading: false, error: null };

test("一覧とカテゴリチップを表示する", async () => {
  render(<LibraryPage {...base} api={fakeApi()} />);
  expect(await screen.findByText("Web開発")).toBeInTheDocument();
  expect(screen.getByText("経済の話")).toBeInTheDocument();
  expect(await screen.findByRole("button", { name: "技術" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "すべて" })).toBeInTheDocument();
});

test("カードに色別マーカー数を表示する", async () => {
  render(<LibraryPage {...base} api={fakeApi()} />);
  // Web開発カードに red=2 が出る
  expect(await screen.findByText("2")).toBeInTheDocument();
});

test("URLバーで送信すると onSubmitUrl が呼ばれる", async () => {
  const onSubmitUrl = vi.fn();
  render(<LibraryPage {...base} onSubmitUrl={onSubmitUrl} api={fakeApi()} />);
  await userEvent.type(
    screen.getByPlaceholderText(/記事のURL/),
    "https://example.com/a",
  );
  await userEvent.click(screen.getByRole("button", { name: "解析する" }));
  expect(onSubmitUrl).toHaveBeenCalledWith("https://example.com/a");
});

test("検索すると q 付きで再取得する", async () => {
  const api = fakeApi();
  render(<LibraryPage {...base} api={api} />);
  await screen.findByText("Web開発");
  await userEvent.type(screen.getByPlaceholderText(/検索/), "python{Enter}");
  await waitFor(() =>
    expect(api.listDocuments).toHaveBeenLastCalledWith(1, expect.any(Number), "python", ""),
  );
});

test("カテゴリチップで category 付きで再取得する", async () => {
  const api = fakeApi();
  render(<LibraryPage {...base} api={api} />);
  await userEvent.click(await screen.findByRole("button", { name: "ビジネス" }));
  await waitFor(() =>
    expect(api.listDocuments).toHaveBeenLastCalledWith(1, expect.any(Number), "", "ビジネス"),
  );
});

test("記事クリックで onOpen が呼ばれる", async () => {
  const onOpen = vi.fn();
  render(<LibraryPage {...base} onOpen={onOpen} api={fakeApi()} />);
  await userEvent.click(await screen.findByText("Web開発"));
  expect(onOpen).toHaveBeenCalledWith(3);
});

test("削除ボタンで確認後に deleteDocument が呼ばれ一覧を再取得する", async () => {
  const api = fakeApi();
  const onOpen = vi.fn();
  const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
  render(<LibraryPage {...base} onOpen={onOpen} api={api} />);
  await screen.findByText("Web開発");
  const callsBefore = api.listDocuments.mock.calls.length;

  // 1枚目(id=3)の削除ボタン
  await userEvent.click(screen.getAllByRole("button", { name: "削除" })[0]);

  expect(api.deleteDocument).toHaveBeenCalledWith(3);
  expect(onOpen).not.toHaveBeenCalled(); // カードは開かない
  expect(api.listDocuments.mock.calls.length).toBeGreaterThan(callsBefore); // 再取得
  confirmSpy.mockRestore();
});

test("確認でキャンセルすると削除しない", async () => {
  const api = fakeApi();
  const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);
  render(<LibraryPage {...base} api={api} />);
  await screen.findByText("Web開発");
  await userEvent.click(screen.getAllByRole("button", { name: "削除" })[0]);
  expect(api.deleteDocument).not.toHaveBeenCalled();
  confirmSpy.mockRestore();
});

test("次ページ(›)でページを進める", async () => {
  const api = fakeApi({ listDocuments: vi.fn(async () => page(docs, 25)) });
  render(<LibraryPage {...base} api={api} />);
  await screen.findByText("Web開発");
  await userEvent.click(screen.getByRole("button", { name: "›" }));
  await waitFor(() =>
    expect(api.listDocuments).toHaveBeenLastCalledWith(2, expect.any(Number), "", ""),
  );
});
