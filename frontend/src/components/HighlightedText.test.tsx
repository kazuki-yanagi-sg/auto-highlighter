import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HighlightedText } from "./HighlightedText";
import type { Segment } from "../types";

const segments: Segment[] = [
  { id: 1, order: 0, text: "重要な主張。", marker: "red", page: 0 },
  { id: 2, order: 1, text: "ただの説明。", marker: null, page: 0 },
  { id: 3, order: 2, text: "例えば〜。", marker: "green", page: 0 },
];

test("全ての文を表示する", () => {
  render(<HighlightedText segments={segments} onSelectSegment={() => {}} />);
  expect(screen.getByText("重要な主張。")).toBeInTheDocument();
  expect(screen.getByText("ただの説明。")).toBeInTheDocument();
  expect(screen.getByText("例えば〜。")).toBeInTheDocument();
});

test("マーカー付きの文に色クラスを付ける", () => {
  render(<HighlightedText segments={segments} onSelectSegment={() => {}} />);
  expect(screen.getByText("重要な主張。")).toHaveClass("mk-red");
  expect(screen.getByText("例えば〜。")).toHaveClass("mk-green");
  expect(screen.getByText("ただの説明。")).not.toHaveClass("mk-red");
});

test("文をクリックすると onSelectSegment が呼ばれる", async () => {
  const onSelect = vi.fn();
  render(<HighlightedText segments={segments} onSelectSegment={onSelect} />);
  await userEvent.click(screen.getByText("重要な主張。"));
  expect(onSelect).toHaveBeenCalledWith(1);
});

test("別行立て数式($$...$$)の文はブロック表示クラスを付ける", () => {
  const eq: Segment[] = [
    { id: 9, order: 0, text: "$$\\lim_{n\\to\\infty}x_{n}=x$$", marker: null, page: 0 },
  ];
  const { container } = render(
    <HighlightedText segments={eq} onSelectSegment={() => {}} />,
  );
  // KaTeX の別行立て(katex-display)を含む文は seg-display で改行を保つ。
  expect(container.querySelector(".seg-display")).not.toBeNull();
});
