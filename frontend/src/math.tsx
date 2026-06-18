import katex from "katex";

// 表示用: 本文中の数式を KaTeX でコンパイルし、地の文はエスケープして連結する。
// バックエンドの math_speech.to_speech と同じ数式区切りを共有する:
//   display: $$...$$ / \[...\] / {\displaystyle ...}   inline: $...$ / \(...\)

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderTex(tex: string, display: boolean): string {
  try {
    return katex.renderToString(tex, { throwOnError: false, displayMode: display });
  } catch {
    return escapeHtml(tex);
  }
}

// 区切りの数式(先頭が i に一致するもの)。一致したら {tex, display, end} を返す。
const DELIMS: Array<{ open: string; close: string; display: boolean }> = [
  { open: "$$", close: "$$", display: true },
  { open: "\\[", close: "\\]", display: true },
  { open: "\\(", close: "\\)", display: false },
  { open: "$", close: "$", display: false },
];

function matchDelim(text: string, i: number) {
  for (const d of DELIMS) {
    if (!text.startsWith(d.open, i)) continue;
    const end = text.indexOf(d.close, i + d.open.length);
    if (end === -1) continue;
    const tex = text.slice(i + d.open.length, end);
    // 中身に日本語を含む区切りは数式ではない(地の文中の単独 $ などの誤検出を防ぐ)。
    // 例: 「価格は $5 で、別の $10」を数式として飲み込まない。
    if (JP.test(tex)) continue;
    return { tex, display: d.display, end: end + d.close.length };
  }
  return null;
}

// {\displaystyle ...} / {\textstyle ...} を中括弧の対応をとって取り出す。
function matchStyleBlock(text: string, i: number) {
  const m = /^\{\\(?:displaystyle|textstyle)\s*/.exec(text.slice(i));
  if (!m) return null;
  let depth = 1;
  let k = i + m[0].length;
  while (k < text.length && depth > 0) {
    if (text[k] === "{") depth++;
    else if (text[k] === "}") depth--;
    k++;
  }
  return { tex: text.slice(i + m[0].length, k - 1), end: k };
}

// 日本語の連なり。これは数式に含まれない区切り。
const JP = /[぀-ヿ一-鿿　-〿＀-￯]/;
const JP_SPLIT = /([぀-ヿ一-鿿　-〿＀-￯]+)/;
// 区切り記号のない地の文の数式判定はバックスラッシュ(LaTeXコマンド)に限定する。
// _ や ^ 単独では数式とみなさない: snake_case 識別子(read_qiita, race_entries)や
// ファイルパス・添字付き変数を誤って KaTeX で描画して崩すのを防ぐ(誤検出の主因)。
const MATH_SIGNAL = /\\/;

// 区切り記号のない地の文から、\ を含む塊(LaTeXコマンド)を数式とみなして描画する。
function renderPlain(plain: string): string {
  let out = "";
  for (const part of plain.split(JP_SPLIT)) {
    if (!part) continue;
    if (JP.test(part) || !MATH_SIGNAL.test(part) || !part.trim()) {
      out += escapeHtml(part);
    } else {
      out += renderTex(part.trim(), false);
    }
  }
  return out;
}

export function renderSegmentHtml(text: string): string {
  // 想定外の入力でも本文全体の描画を巻き込んで壊さないよう、最終防衛で素のテキストに退避する。
  try {
    return renderSegmentHtmlUnsafe(text);
  } catch {
    return escapeHtml(text);
  }
}

function renderSegmentHtmlUnsafe(text: string): string {
  let out = "";
  let plain = "";
  let i = 0;
  const flush = () => {
    if (plain) {
      out += renderPlain(plain);
      plain = "";
    }
  };
  while (i < text.length) {
    const block = matchStyleBlock(text, i);
    if (block) {
      flush();
      out += renderTex(block.tex, true);
      i = block.end;
      continue;
    }
    const delim = matchDelim(text, i);
    if (delim) {
      flush();
      out += renderTex(delim.tex, delim.display);
      i = delim.end;
      continue;
    }
    plain += text[i];
    i++;
  }
  flush();
  return out;
}
