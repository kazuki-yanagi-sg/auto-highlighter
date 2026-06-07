import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll } from "vitest";
import { App } from "../App";

// MSW で backend をモック: 即開き(POSTで本文・色なし) → progressで色が付く流れを検証。
const server = setupServer(
  http.get("*/api/documents", () =>
    HttpResponse.json({ items: [], total: 0, page: 1, size: 9 }),
  ),
  http.get("*/api/categories", () => HttpResponse.json([])),
  http.post("*/api/documents", () =>
    HttpResponse.json({
      document: {
        id: 1,
        url: "https://example.com/a",
        title: "モック記事",
        category: null,
        segments: [
          { id: 10, order: 0, text: "重要な主張。", marker: null, page: 0 },
          { id: 11, order: 1, text: "ただの説明。", marker: null, page: 0 },
        ],
        notes: [],
      },
      job_id: "j1",
    }),
  ),
  http.get("*/api/documents/progress/j1", () =>
    HttpResponse.json({
      status: "done",
      done: 1,
      total: 1,
      percent: 100,
      eta_seconds: null,
      category: "技術",
      markers: { "0": "red" },
      detail: null,
    }),
  ),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test("ライブラリのURLバーから解析→マーカー付きで表示する", async () => {
  render(<App />);

  expect(await screen.findByText("ライブラリ")).toBeInTheDocument();

  await userEvent.type(
    screen.getByPlaceholderText(/記事のURL/),
    "https://example.com/a",
  );
  await userEvent.click(screen.getByRole("button", { name: "解析する" }));

  expect(
    await screen.findByRole("heading", { name: "モック記事" }),
  ).toBeInTheDocument();
  // 本文に限定(目次サイドバーが同じ見出し文を持つため)。色は解析(progress)後に付く。
  const body = () =>
    within(document.querySelector(".reader-text") as HTMLElement);
  await waitFor(() =>
    expect(body().getByText("重要な主張。")).toHaveClass("mk-red"),
  );
});
