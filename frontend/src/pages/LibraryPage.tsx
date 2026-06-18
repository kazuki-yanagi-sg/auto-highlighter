import { useCallback, useEffect, useState } from "react";
import { deleteDocument as defaultDeleteDocument, listCategories as defaultListCategories, listDocuments as defaultListDocuments } from "../api/client";
import { MARKER_COLORS, type DocumentSummary, type Page } from "../types";

const PAGE_SIZE = 9;

interface LibraryApi {
  listDocuments: (page: number, size: number, q: string, category: string) => Promise<Page<DocumentSummary>>;
  listCategories: () => Promise<string[]>;
  deleteDocument: (id: number) => Promise<void>;
}

interface Props {
  onOpen: (id: number) => void;
  onSubmitUrl: (url: string) => void;
  loading: boolean;
  error: string | null;
  api?: LibraryApi;
}

const defaultApi: LibraryApi = {
  listDocuments: defaultListDocuments,
  listCategories: defaultListCategories,
  deleteDocument: defaultDeleteDocument,
};

function hostOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}

export function LibraryPage({ onOpen, onSubmitUrl, loading, error, api = defaultApi }: Props) {
  const [result, setResult] = useState<Page<DocumentSummary> | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [urlDraft, setUrlDraft] = useState("");
  const [searchDraft, setSearchDraft] = useState("");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);

  const load = useCallback(() => {
    api
      .listDocuments(page, PAGE_SIZE, query, category)
      .then(setResult)
      .catch(() => setResult(null));
  }, [api, page, query, category]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    api
      .listCategories()
      .then(setCategories)
      .catch(() => setCategories([]));
  }, [api]);

  function submitUrl(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = urlDraft.trim();
    if (trimmed) onSubmitUrl(trimmed);
  }

  async function remove(e: React.MouseEvent, id: number, title: string) {
    e.stopPropagation(); // カードを開かない
    if (!window.confirm(`「${title}」を削除しますか?`)) return;
    await api.deleteDocument(id);
    load(); // 一覧を再取得
  }

  function search(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    setQuery(searchDraft.trim());
  }

  function pickCategory(c: string) {
    setPage(1);
    setCategory(c);
  }

  const total = result?.total ?? 0;
  const totalPages = result ? Math.max(1, Math.ceil(result.total / result.size)) : 1;

  return (
    <main className="page scroll">
      <header className="brand">
        <span className="brand-logo">マーカー</span>
        <span className="brand-sub">Marker</span>
      </header>
      <p className="lead">
        WEB記事や<b>PDF論文</b>のURLを貼ると本文を取り込み、<b>4色のマーカー</b>
        を引きながら読むためのリーダー。
      </p>

      <form className="urlbar" onSubmit={submitUrl}>
        <div className="urlbar-field">
          <span aria-hidden>🔗</span>
          <input type="url" placeholder="記事のURLやPDFを貼り付け… 例) https://…/paper.pdf" value={urlDraft} onChange={(e) => setUrlDraft(e.target.value)} />
        </div>
        <button className="btn-accent" type="submit" disabled={loading}>
          {loading ? "解析中…" : "解析する"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}

      <div className="section-bar">
        <div>
          <span className="section-title">ライブラリ</span>
          <span className="section-meta">{total}件の解析履歴</span>
        </div>
        <form className="search" onSubmit={search}>
          <span aria-hidden>🔍</span>
          <input placeholder="タイトル・URLで検索" value={searchDraft} onChange={(e) => setSearchDraft(e.target.value)} />
        </form>
      </div>

      <div className="chips">
        <button className={`chip ${category === "" ? "active" : ""}`} onClick={() => pickCategory("")}>
          すべて
        </button>
        {categories.map((c) => (
          <button key={c} className={`chip ${category === c ? "active" : ""}`} onClick={() => pickCategory(c)}>
            {c}
          </button>
        ))}
      </div>

      <div className="card-grid">
        {result?.items.map((doc) => (
          <div key={doc.id} className="card" role="button" tabIndex={0} onClick={() => onOpen(doc.id)}>
            <div className="card-top">
              <span className="card-domain">
                <img className="favicon" alt="" src={`https://www.google.com/s2/favicons?domain=${hostOf(doc.url)}`} />
                {hostOf(doc.url)}
              </span>
              <button className="card-delete" aria-label="削除" onClick={(e) => remove(e, doc.id, doc.title)}>
                🗑
              </button>
            </div>
            {doc.category && <span className="card-cat">{doc.category}</span>}
            <span className="card-title">{doc.title}</span>
            <div className="card-foot">
              <div className="mk-counts">
                {MARKER_COLORS.filter((c) => doc.marker_counts[c] > 0).map((c) => (
                  <span key={c} className="mk-count">
                    <span className={`mk-dot ${c}`} />
                    {doc.marker_counts[c]}
                  </span>
                ))}
              </div>
              <div className="card-meta">
                <span>🗒 {doc.note_count}</span>
                <span>{formatDate(doc.created_at)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {result && result.total === 0 && <p className="empty">保存された記事はまだありません。上のバーにURLを貼って始めましょう。</p>}

      <div className="pager">
        <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          ‹
        </button>
        <span className="page-num">{page}</span>
        <span style={{ color: "var(--ink-faint)" }}>/ {totalPages}</span>
        <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
          ›
        </button>
      </div>
    </main>
  );
}
