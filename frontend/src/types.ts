export type MarkerColor = "red" | "yellow" | "blue" | "green";

export const MARKER_COLORS: MarkerColor[] = ["red", "yellow", "blue", "green"];

// マーカー色の日本語ラベル(凡例・ボタン表示用)
export const MARKER_LABELS: Record<MarkerColor, string> = {
  red: "重要",
  yellow: "注意",
  blue: "参照",
  green: "具体例",
};

export interface Segment {
  id: number;
  order: number;
  text: string;
  marker: MarkerColor | null;
  page: number;
  // 段落グループ識別子。同じ block の文を1段落にまとめて改行構造を保つ。
  block?: number;
  // "text"(地の文) または "code"(コードブロック。原文のまま等幅表示)。
  kind?: "text" | "code";
}

export interface Note {
  id: number;
  document_id: number;
  segment_id: number | null;
  body: string;
  page: number;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface DocumentData {
  id: number;
  url: string;
  title: string;
  category: string | null;
  segments: Segment[];
  notes: Note[];
}

export interface DocumentSummary {
  id: number;
  url: string;
  title: string;
  category: string | null;
  created_at: string | null;
  marker_counts: Record<MarkerColor, number>;
  note_count: number;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface CreateResult {
  document: DocumentData;
  job_id: string;
}

export interface Progress {
  status: "processing" | "done" | "error";
  done: number;
  total: number;
  percent: number;
  eta_seconds: number | null;
  category: string | null;
  markers: Record<string, MarkerColor>; // order(文字列) -> 色
  detail: string | null;
}
