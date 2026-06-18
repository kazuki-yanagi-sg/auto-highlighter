const fs = require("fs");

const TEMPLATE = "/Users/kazukiyanagi/.claude/skills/make-marker/template.html";
const OUT = "/Users/kazukiyanagi/Desktop/3_学習/マーカー機能/backend/app/repositories/orm.marker.html";
const TITLE = "orm.py";

const SEGMENTS = [
  { text: '"""SQLAlchemy テーブル定義。ドメインモデルとは分離する(永続化の都合をdomainに漏らさない)。"""', color: "red", reason: "このモジュールの責務＝永続化とドメインの分離方針を定義する核", paragraph_break: true },

  { text: "from __future__ import annotations", color: "blue", reason: "将来の型アノテーション機能を参照", paragraph_break: true },
  { text: "from datetime import datetime, timezone", color: "blue", reason: "日時型を外部から参照" },
  { text: "from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text", color: "blue", reason: "カラム型を SQLAlchemy から参照" },
  { text: "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship", color: "blue", reason: "ORM マッピング機能を参照" },

  { text: "def _utcnow() -> datetime:", color: null, paragraph_break: true },
  { text: "return datetime.now(timezone.utc)", color: "green", reason: "UTC の現在時刻という具体値を返す" },

  { text: "class Base(DeclarativeBase):", color: "red", reason: "全テーブルの基底クラス＝永続化の土台", paragraph_break: true },
  { text: "pass", color: null },

  { text: "class DocumentRow(Base):", color: "red", reason: "文書テーブルの定義", paragraph_break: true },
  { text: '__tablename__ = "documents"', color: "green", reason: "テーブル名の具体値" },
  { text: "id: Mapped[int] = mapped_column(Integer, primary_key=True)", color: null },
  { text: "url: Mapped[str] = mapped_column(String(2048))", color: "green", reason: "URL 列の最大長 2048 という具体指定" },
  { text: "title: Mapped[str] = mapped_column(String(512))", color: "green", reason: "タイトル列の最大長 512 という具体指定" },
  { text: "category: Mapped[str | None] = mapped_column(String(64), nullable=True)", color: "yellow", reason: "null 許容＝未設定を許す点に注意" },
  { text: "created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)", color: "green", reason: "作成時刻のデフォルトを具体指定" },
  { text: 'segments: Mapped[list["SegmentRow"]] = relationship(back_populates="document", cascade="all, delete-orphan", order_by="SegmentRow.order")', color: "red", reason: "文書→文の1対多関係（削除カスケード）を定義する核" },
  { text: 'notes: Mapped[list["NoteRow"]] = relationship(back_populates="document", cascade="all, delete-orphan", order_by="NoteRow.id")', color: "red", reason: "文書→付箋の1対多関係を定義する核" },

  { text: "class SegmentRow(Base):", color: "red", reason: "文セグメントテーブルの定義", paragraph_break: true },
  { text: '__tablename__ = "segments"', color: "green", reason: "テーブル名の具体値" },
  { text: "id: Mapped[int] = mapped_column(Integer, primary_key=True)", color: null },
  { text: 'document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))', color: "blue", reason: "文書テーブルへの外部キー参照" },
  { text: "order: Mapped[int] = mapped_column(Integer)", color: null },
  { text: "text: Mapped[str] = mapped_column(Text)", color: "red", reason: "原文そのものを保持する核の列" },
  { text: "marker: Mapped[str | None] = mapped_column(String(16), nullable=True)", color: "red", reason: "4色マーカーの色を保持する本機能の核" },
  { text: "page: Mapped[int] = mapped_column(Integer, default=0)", color: null },
  { text: "# 段落グループ識別子。表示側で同じ block の文を1段落にまとめる。", color: "yellow", reason: "表示側のまとめ方を決める運用ルールの注意書き" },
  { text: 'block: Mapped[int] = mapped_column(Integer, default=0, server_default="0")', color: "green", reason: "server_default=\"0\" という具体デフォルト" },
  { text: 'document: Mapped[DocumentRow] = relationship(back_populates="segments")', color: null },

  { text: "class NoteRow(Base):", color: "red", reason: "付箋（正方形コメント）テーブルの定義", paragraph_break: true },
  { text: '__tablename__ = "sticky_notes"', color: "green", reason: "テーブル名の具体値" },
  { text: "id: Mapped[int] = mapped_column(Integer, primary_key=True)", color: null },
  { text: 'document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))', color: "blue", reason: "文書テーブルへの外部キー参照" },
  { text: 'segment_id: Mapped[int | None] = mapped_column(ForeignKey("segments.id"), nullable=True)', color: "blue", reason: "どの文に紐づくかの参照（null 可）" },
  { text: "body: Mapped[str] = mapped_column(Text)", color: "red", reason: "付箋本文を保持する核の列" },
  { text: "page: Mapped[int] = mapped_column(Integer, default=0)", color: null },
  { text: "x: Mapped[float] = mapped_column(Float, default=0.0)", color: "green", reason: "貼付座標 x のデフォルト具体値" },
  { text: "y: Mapped[float] = mapped_column(Float, default=0.0)", color: null },
  { text: "w: Mapped[float] = mapped_column(Float, default=176.0)", color: "green", reason: "付箋の幅 176.0 という具体デフォルト" },
  { text: "h: Mapped[float] = mapped_column(Float, default=150.0)", color: "green", reason: "付箋の高さ 150.0 という具体デフォルト" },
  { text: "created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)", color: null },
  { text: 'document: Mapped[DocumentRow] = relationship(back_populates="notes")', color: null },
];

let html = fs.readFileSync(TEMPLATE, "utf8");
html = html.replace("/*__DATA__*/[]", JSON.stringify(SEGMENTS, null, 2));
html = html.split("__TITLE__").join(TITLE);
fs.writeFileSync(OUT, html, "utf8");
console.log("wrote", OUT, "segments:", SEGMENTS.length);
