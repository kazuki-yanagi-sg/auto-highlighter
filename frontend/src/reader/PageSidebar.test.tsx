import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PageSidebar } from "./PageSidebar";

const pages = [
  { page: 0, label: "はじめに" },
  { page: 1, label: "本論" },
  { page: 2, label: "まとめ" },
];

test("各ページの見出しラベルを表示する", () => {
  render(<PageSidebar pages={pages} current={0} onSelect={() => {}} />);
  expect(screen.getByText("はじめに")).toBeInTheDocument();
  expect(screen.getByText("本論")).toBeInTheDocument();
  expect(screen.getByText("まとめ")).toBeInTheDocument();
});

test("クリックで onSelect(ページ番号) が呼ばれる", async () => {
  const onSelect = vi.fn();
  render(<PageSidebar pages={pages} current={0} onSelect={onSelect} />);
  await userEvent.click(screen.getByText("本論"));
  expect(onSelect).toHaveBeenCalledWith(1);
});

test("現在のページを強調する", () => {
  render(<PageSidebar pages={pages} current={1} onSelect={() => {}} />);
  expect(screen.getByTestId("page-item-1")).toHaveClass("current");
  expect(screen.getByTestId("page-item-0")).not.toHaveClass("current");
});
