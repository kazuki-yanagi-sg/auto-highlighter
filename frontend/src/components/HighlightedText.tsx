import type { Segment } from "../types";
import { renderSegmentHtml } from "../math";

interface Props {
  segments: Segment[];
  onSelectSegment: (segmentId: number) => void;
}

// 日本語(ひらがな・カタカナ・漢字)を含むか。含まない文は数式/行列の行とみなし、
// 1行ずつ縦に並べる(行列が横につながって読めなくなるのを防ぐ)。
const CJK = /[぀-ヿ㐀-鿿一-龥]/;

// 連続するセグメントを block 単位の段落にまとめる。block が無い場合は
// 1セグメント=1段落として扱う(後方互換)。これで改行・段落構造を保てる。
function groupByBlock(segments: Segment[]): Segment[][] {
  const groups: Segment[][] = [];
  for (const segment of segments) {
    const last = groups[groups.length - 1];
    const sameBlock =
      last && segment.block !== undefined && last[0].block === segment.block;
    if (sameBlock) {
      last.push(segment);
    } else {
      groups.push([segment]);
    }
  }
  return groups;
}

// マーカーの色を本文に重ねて描画する。要約はせず原文をそのまま出す。
// 本文中の数式は KaTeX でコンパイルして表示する(renderSegmentHtml)。
export function HighlightedText({ segments, onSelectSegment }: Props) {
  return (
    <div className="reader-text">
      {/* 段落は div で包む(p だと別行立て数式の KaTeX block を内包できないため)。 */}
      {groupByBlock(segments).map((group) => {
        // コードブロックは原文のまま <pre> で等幅表示(KaTeX/文分割を通さない)。
        if (group.length === 1 && group[0].kind === "code") {
          const seg = group[0];
          return (
            <pre
              className="code-block"
              key={seg.id}
              onClick={() => onSelectSegment(seg.id)}
            >
              {seg.text}
            </pre>
          );
        }
        // 段落全体が日本語を含まない = 数式/行列の固まり。詰めて縦並びの数式ブロックにする。
        const isMathGroup = group.every((s) => !CJK.test(s.text));
        return (
          <div
            className={isMathGroup ? "para para-math" : "para"}
            key={group[0].id}
          >
            {group.map((segment) => {
              const html = renderSegmentHtml(segment.text);
              // 別行立て数式($$..$$)= seg-display。日本語を含まない行 = seg-line(詰めた縦並び)。
              const base = segment.marker ? `mk mk-${segment.marker}` : "seg";
              let className = base;
              if (html.includes("katex-display")) className = `${base} seg-display`;
              else if (!CJK.test(segment.text)) className = `${base} seg-line`;
              return (
                <span
                  key={segment.id}
                  className={className}
                  onClick={() => onSelectSegment(segment.id)}
                  role="button"
                  tabIndex={0}
                  title="クリックで付箋を追加"
                  dangerouslySetInnerHTML={{ __html: html }}
                />
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
