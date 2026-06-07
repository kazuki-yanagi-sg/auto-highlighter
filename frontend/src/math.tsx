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
    return {
      tex: text.slice(i + d.open.length, end),
      display: d.display,
      end: end + d.close.length,
    };
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
const MATH_SIGNAL = /[\\^_]/;

// 区切り記号のない地の文から、\ ^ _ を含む塊を数式とみなして KaTeX 描画する。
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
