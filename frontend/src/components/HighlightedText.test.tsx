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

test("同じ block の文は1段落にまとめ、別 block は段落を分ける", () => {
  const segs: Segment[] = [
    { id: 1, order: 0, text: "一文目。", marker: null, page: 0, block: 0 },
    { id: 2, order: 1, text: "二文目。", marker: null, page: 0, block: 0 },
    { id: 3, order: 2, text: "別段落。", marker: null, page: 0, block: 1 },
  ];
  const { container } = render(
    <HighlightedText segments={segs} onSelectSegment={() => {}} />,
  );
  const paras = container.querySelectorAll(".para");
  expect(paras.length).toBe(2);
  // 1段落目に block 0 の2文がまとまる。
  expect(paras[0].querySelectorAll(".seg").length).toBe(2);
});

test("日本語を含まない数式/行列行は1段落に縦並び(seg-display)でまとめる", () => {
  // PDFの行列: 同じ block の数式行を1段落に、各行をブロック表示で縦に積む。
  const matrix: Segment[] = [
    { id: 1, order: 0, text: "f : g → gl2(R) : aA + bX →", marker: null, page: 0, block: 5 },
    { id: 2, order: 1, text: "b a", marker: null, page: 0, block: 5 },
    { id: 3, order: 2, text: "0 −a", marker: null, page: 0, block: 5 },
    { id: 4, order: 3, text: "(6.3)", marker: null, page: 0, block: 5 },
  ];
  const { container } = render(
    <HighlightedText segments={matrix} onSelectSegment={() => {}} />,
  );
  // 行列は1段落にまとまり、数式ブロック(.para-math)として詰めて表示する。
  expect(container.querySelectorAll(".para-math").length).toBe(1);
  // 各行は seg-line(詰めた縦並び)で表示する。
  expect(container.querySelectorAll(".seg-line").length).toBe(4);
});

test("コードブロックは pre で原文のまま表示する(改行・記号を保持)", () => {
  const code = "def f():\n    return a_b * 2  # $x";
  const segs: Segment[] = [
    { id: 1, order: 0, text: code, marker: null, page: 0, block: 0, kind: "code" },
  ];
  const { container } = render(
    <HighlightedText segments={segs} onSelectSegment={() => {}} />,
  );
  const pre = container.querySelector("pre.code-block");
  expect(pre).not.toBeNull();
  // 改行・字下げ・記号($や_)がそのまま残る(KaTeXに飲み込まれない)。
  expect(pre?.textContent).toBe(code);
  expect(container.querySelector(".katex")).toBeNull();
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
