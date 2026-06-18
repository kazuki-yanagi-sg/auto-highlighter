import { describe, it, expect } from "vitest";
import { renderSegmentHtml } from "../math";
import realSegments from "./_pdf_segments.fixture.json";

// 実PDFセグメント + 意地悪入力を renderSegmentHtml に通し、
// 例外を投げず・テキストを落とさないことを確認する(レンダリング崩れの再現用プローブ)。

const adversarial: string[] = [
  "価格は $5 で、別の $10 もある。", // 単独でない $ が2つ → 中身が数式扱いされる誤検出
  "コードは a$b の形。", // $ が1つだけ
  "数式 $x^2 + y^2 = z^2$ を見よ。", // 正常な inline math
  "別行立て $$\\frac{1}{n}$$ である。", // 正常な display math
  "壊れた $\\frac{1$ が含まれる。", // 不正な TeX
  "閉じない $$ 区切り。", // 閉じない $$
  "x_n と y^2 は a_1 などの添字。", // $ なし・MATH_SIGNAL のみ
  "ファイルパス C:\\Users\\name\\dir。", // バックスラッシュを含む地の文
  "{\\displaystyle \\sum_{i=1}^n i} を計算。", // style block
  "正規表現 a^b_c\\d といった断片。",
  "", // 空
  "。", // 句点のみ
];

function textContent(html: string): string {
  // タグを除いた可視テキスト(KaTeX のアクセシビリティ用 annotation 等は含まれうる)
  return html.replace(/<[^>]*>/g, "");
}

describe("renderSegmentHtml の堅牢性", () => {
  const cases = [...(realSegments as string[]), ...adversarial];

  it("どの入力でも例外を投げない", () => {
    const failed: string[] = [];
    for (const s of cases) {
      try {
        renderSegmentHtml(s);
      } catch (e) {
        failed.push(`${JSON.stringify(s)} -> ${String(e)}`);
      }
    }
    expect(failed).toEqual([]);
  });

  it("地の文(数式でない日本語)を取りこぼさない", () => {
    // $ を含まない実PDFセグメントは、本文の文字がそのまま残るはず。
    const dropped: string[] = [];
    for (const s of realSegments as string[]) {
      if (s.includes("$") || /[\\^_]/.test(s)) continue;
      const out = textContent(renderSegmentHtml(s));
      // 先頭10文字程度が残っているか(エスケープでの &amp; 等は無視)
      const head = s.slice(0, 8);
      if (head && !out.includes(head)) dropped.push(s);
    }
    expect(dropped).toEqual([]);
  });

  it("単独でない $ を含む地の文を数式描画しない(中身に日本語)", () => {
    const s = "価格は $5 で、別の $10 もある。";
    const html = renderSegmentHtml(s);
    expect(html).not.toContain("katex"); // KaTeX に飲み込まれない
    expect(textContent(html)).toContain("で、別の");
  });

  it("snake_case 識別子を数式描画しない(誤検出の主因)", () => {
    for (const s of [
      "スコープはread_qiitaとwrite_qiitaを選択",
      "コアテーブル: horses, race_entries, race_results",
      "分析テーブル: bloodline_stats, horse_course_stats など",
    ]) {
      const html = renderSegmentHtml(s);
      expect(html).not.toContain("katex");
      expect(html).toContain("_"); // 下線はそのまま地の文として残る
    }
  });

  it("添字記法 x_n / x^2 単独は数式描画しない(バックスラッシュ無し)", () => {
    const html = renderSegmentHtml("変数 x_n と y^2 は添字。");
    expect(html).not.toContain("katex");
  });

  it("バックスラッシュの LaTeX コマンドは従来どおり描画する", () => {
    expect(renderSegmentHtml("ここで\\etaは学習率です。")).toContain("katex");
    expect(renderSegmentHtml("質量は $E = mc^2$ である。")).toContain("katex");
  });
});
