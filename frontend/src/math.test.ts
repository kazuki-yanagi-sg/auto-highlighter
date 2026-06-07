import { renderSegmentHtml } from "./math";

test("インライン数式を KaTeX でレンダリングする", () => {
  const html = renderSegmentHtml("質量は $E = mc^2$ である。");
  expect(html).toContain("katex");
  expect(html).toContain("である。");
});

test("displaystyle ブロックもレンダリングする", () => {
  const html = renderSegmentHtml("確率 {\\displaystyle P(A)=\\frac{1}{2}} です。");
  expect(html).toContain("katex");
});

test("数式なしの文はそのまま(エスケープされて)返る", () => {
  const html = renderSegmentHtml("これは普通の文です。");
  expect(html).toBe("これは普通の文です。");
  expect(html).not.toContain("katex");
});

test("地の文の HTML 特殊文字はエスケープされる", () => {
  const html = renderSegmentHtml("a < b かつ c > d");
  expect(html).toContain("&lt;");
  expect(html).toContain("&gt;");
  expect(html).not.toContain("<b");
});

test("壊れた数式でも例外を投げない(throwOnError:false)", () => {
  expect(() => renderSegmentHtml("$\\frac{1}{$")).not.toThrow();
});

// 区切り記号のない地の文中の LaTeX も KaTeX で描画する(AI記事に多い)
test("区切りなしのコマンドを描画する", () => {
  const html = renderSegmentHtml("ここで\\etaは学習率です。");
  expect(html).toContain("katex");
  expect(html).toContain("学習率です。");
});

test("区切りなしの分数を描画する", () => {
  const html = renderSegmentHtml("勾配は \\frac{\\partial u}{\\partial w} = x です。");
  expect(html).toContain("katex");
});

test("手がかりのない英字は数式にしない", () => {
  const html = renderSegmentHtml("これは DL の話です。");
  expect(html).not.toContain("katex");
  expect(html).toContain("DL");
});
