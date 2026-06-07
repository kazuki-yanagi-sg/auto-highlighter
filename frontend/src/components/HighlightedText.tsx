import type { Segment } from "../types";
import { renderSegmentHtml } from "../math";

interface Props {
  segments: Segment[];
  onSelectSegment: (segmentId: number) => void;
}

// マーカーの色を本文に重ねて描画する。要約はせず原文をそのまま出す。
// 本文中の数式は KaTeX でコンパイルして表示する(renderSegmentHtml)。
export function HighlightedText({ segments, onSelectSegment }: Props) {
  return (
    <div className="reader-text">
      {segments.map((segment) => {
        const html = renderSegmentHtml(segment.text);
        // 別行立て数式($$...$$)を含む文は、改行を保つためブロック表示にする。
        const base = segment.marker ? `mk mk-${segment.marker}` : "seg";
        const className = html.includes("katex-display") ? `${base} seg-display` : base;
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
}
