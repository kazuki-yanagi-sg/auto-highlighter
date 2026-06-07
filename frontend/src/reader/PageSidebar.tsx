interface PageItem {
  page: number;
  label: string;
}

interface Props {
  pages: PageItem[];
  current: number;
  onSelect: (page: number) => void;
}

// PDFビューア風の左サイド目次。各ページの見出し(先頭文)でジャンプできる。
export function PageSidebar({ pages, current, onSelect }: Props) {
  return (
    <aside className="page-sidebar scroll" aria-label="ページ目次">
      <div className="page-sidebar-title">目次</div>
      <ul>
        {pages.map((p) => (
          <li key={p.page}>
            <button
              type="button"
              data-testid={`page-item-${p.page}`}
              className={`page-item ${p.page === current ? "current" : ""}`}
              onClick={() => onSelect(p.page)}
            >
              <span className="page-item-num">{p.page + 1}</span>
              <span className="page-item-label">{p.label || `ページ ${p.page + 1}`}</span>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
