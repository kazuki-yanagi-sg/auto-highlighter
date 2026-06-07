import { MARKER_COLORS, MARKER_LABELS, type DocumentData } from "../types";

interface Props {
  document: DocumentData;
  onBack?: () => void;
  placing: boolean;
  onTogglePlacing: () => void;
  onToggleTweaks: () => void;
  onToggleSidebar: () => void;
  sidebarOpen: boolean;
}

function hostOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

export function ReaderTopBar({
  document,
  onBack,
  placing,
  onTogglePlacing,
  onToggleTweaks,
  onToggleSidebar,
  sidebarOpen,
}: Props) {
  return (
    <header className="reader-topbar">
      {onBack && (
        <button className="topbar-back" onClick={onBack} aria-label="一覧へ戻る">
          ←
        </button>
      )}
      <button
        className={`topbar-btn ${sidebarOpen ? "on" : ""}`}
        onClick={onToggleSidebar}
        aria-label="目次"
      >
        ☰ 目次
      </button>
      <div className="topbar-title">
        <span className="topbar-cat">
          {hostOf(document.url)}
          {document.category ? ` · ${document.category}` : ""}
        </span>
        <span className="topbar-name">{document.title}</span>
      </div>

      <ul className="legend-chips">
        {MARKER_COLORS.map((c) => (
          <li key={c}>
            <span className={`mk-dot ${c}`} />
            {MARKER_LABELS[c]}
          </li>
        ))}
      </ul>

      <div className="topbar-actions">
        <button
          className={`topbar-btn ${placing ? "on" : ""}`}
          onClick={onTogglePlacing}
        >
          ＋付箋
        </button>
        <button className="topbar-btn" onClick={onToggleTweaks}>
          ⚙ 設定
        </button>
      </div>
    </header>
  );
}
