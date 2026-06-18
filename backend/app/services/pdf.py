"""PDF バイト列から本文を取り出す純粋関数。

HTML 用の extract_content と対になる存在(SRP: PDF 解析だけを担う)。
出力は同じ ScrapedContent なので、segmenter 以降の下流は無改修で再利用できる。
ネットワーク I/O は持たない(取得は Scraper 側)。

抽出エンジンは pdfminer.six(pure-python)。pypdf は dvipdfmx 製の日本語 PDF
(Identity-H 埋め込み + ToUnicode 欠落)でグリフIDを誤変換し文字化けするため使わない。
"""

from __future__ import annotations

import io
import re

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTTextLine
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.psparser import PSLiteral

from app.services.scraper import Block, ScrapedContent

# タイトルが取れない時の見出し代用にする最大文字数(長すぎる先頭行を丸ごと使わない)。
_TITLE_MAX = 80

# 日本語(ひらがな・カタカナ・漢字)。これを含む行は地の文とみなす。
_CJK = re.compile(r"[぀-ヿ㐀-鿿一-龥]")
# 章節番号で始まる見出し行(例: "6.2.1 リー代数の例")。
_SECTION_HEAD = re.compile(r"^\d+(?:\.\d+)+\s+\S")
# 数式行の目印。地の文に出る句読点(. , ( ) - 等)は誤検出を避けるため含めない。
# $ と \ (LaTeX) も含め、再構成した数式($$..$$)を数式行として扱えるようにする。
_MATH_SIGNAL = re.compile(r"[=<>≤≥×÷∈∋∉⊂⊃⊆⊇∪∩∀∃∑∏∫√≠≈±·∘⊕⊗→↦⟶↔−$\\]")
# 数式行とみなす短さの上限(行列の行 "b a" / 式番号 "(6.3)" 等を拾う)。
_VERBATIM_MAX = 6
# pdfminer が出す未マップグリフ表現 (cid:NNN)。本文に残すと読めないので除去する。
_CID = re.compile(r"\(cid:\d+\)")
# ページ下部の脚注定義(例: "*1 Lie algebra" "*8 genral linear Lie algebra")。
# 「数字の後に空白+英単語」のみを対象にし、本文の脚注マーカー("リー代数*1"=後ろが
# 日本語)は壊さない。読みの邪魔になるページ付帯物なので本文からは取り除く。
_FOOTNOTE_DEF = re.compile(r"\s*\*\d+\s+[A-Za-z][A-Za-z]*(?:\s+[A-Za-z][A-Za-z]*)*")
# ノンブル(ページ番号)だけの行。本文ではないので落とす。
_PAGE_NUMBER = re.compile(r"^\d{1,4}$")
# 各ページ上部で繰り返されるランニングヘッダ(章見出し/節見出し)。重複は1つだけ残す。
_RUNNING_HEADER = re.compile(r"^(?:第\s*\d+\s*章|\d+(?:\.\d+)*\s)")

# --- 行列の座標再構成 ---
# セル候補とみなす文字数の上限(行列の要素は短い)。
_CELL_MAX = 8
# 同一行とみなす y(中心)の許容差 / 同一行列クラスタとみなす近さ。
_ROW_Y_TOL = 7.0
_CLUSTER_DX = 55.0
_CLUSTER_DY = 18.0
# ページ余白(ノンブル等を除外する y 帯)。
_MARGIN_TOP = 720.0
_MARGIN_BOTTOM = 70.0
# 同じ視覚行(同一ベースライン)とみなす y 差。これ以内は1行として左→右で並べる。
_ROW_SORT_TOL = 6.0
# セルには現れない関係/集合記号(これを含む断片は行列セルではなくラベル)。
_NON_CELL = re.compile(r"[∈∋|=≤≥<>]|:=")
# 式番号 "(6.3)" など。
_EQ_NUMBER = re.compile(r"^\(\d")
# 文末とみなす記号(これで終わる行は段落/文の区切り)。
_SENTENCE_END = ("。", ".", "．", "!", "?", "！", "？", ":", "：")


def _page_lines(page) -> list[dict]:
    """1ページの各テキスト行を {x0,x1,yc,text} で取り出す(座標つき)。"""
    lines: list[dict] = []
    for element in page:
        if not isinstance(element, LTTextContainer):
            continue
        for line in element:
            if not isinstance(line, LTTextLine):
                continue
            text = _CID.sub("", line.get_text()).strip()
            if text:
                lines.append(
                    {
                        "x0": line.x0,
                        "x1": line.x1,
                        "yc": (line.y0 + line.y1) / 2,
                        "text": text,
                    }
                )
    return lines


def _is_cell(line: dict) -> bool:
    """行列セル候補か。短い・日本語/関係記号なし・本文余白でない断片に限る。"""
    text = line["text"]
    if _has_cjk(text) or len(text) > _CELL_MAX:
        return False
    if _NON_CELL.search(text) or _EQ_NUMBER.match(text):
        return False
    if not re.search(r"[0-9A-Za-z]", text):  # 記号のみ(. , 等)は除外
        return False
    return _MARGIN_BOTTOM < line["yc"] < _MARGIN_TOP


def _x_gap(a: dict, b: dict) -> float:
    return max(0.0, max(a["x0"], b["x0"]) - min(a["x1"], b["x1"]))


def _cluster_cells(cells: list[dict]) -> list[list[dict]]:
    """近接するセル候補を1つの行列クラスタにまとめる(union-find)。"""
    parent = list(range(len(cells)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            near_y = abs(cells[i]["yc"] - cells[j]["yc"]) <= _CLUSTER_DY
            near_x = _x_gap(cells[i], cells[j]) <= _CLUSTER_DX
            if near_y and near_x:
                parent[find(i)] = find(j)

    groups: dict[int, list[dict]] = {}
    for idx, cell in enumerate(cells):
        groups.setdefault(find(idx), []).append(cell)
    return list(groups.values())


def _tex_cell(text: str) -> str:
    return text.replace("−", "-").replace("×", r"\times")


def _matrix_latex(cluster: list[dict]) -> str | None:
    """クラスタが整合した2列以上のグリッドなら pmatrix の LaTeX を返す。さもなくば None。

    行=y(上から)、列=x(左から)。各行のセル数が揃っていなければ行列と断定せず None
    (誤った行列を出さない=保守的)。
    """
    rows: list[list[dict]] = []
    for cell in sorted(cluster, key=lambda c: -c["yc"]):
        if rows and abs(rows[-1][0]["yc"] - cell["yc"]) <= _ROW_Y_TOL:
            rows[-1].append(cell)
        else:
            rows.append([cell])

    grid: list[list[str]] = []
    for row in rows:
        cells: list[str] = []
        for frag in sorted(row, key=lambda c: c["x0"]):
            cells.extend(frag["text"].split())
        grid.append(cells)

    widths = {len(r) for r in grid}
    if len(grid) < 2 or len(widths) != 1:
        return None
    if widths.pop() < 2:
        return None

    body = r" \\ ".join(" & ".join(_tex_cell(c) for c in row) for row in grid)
    return r"$$\begin{pmatrix} " + body + r" \end{pmatrix}$$"


def _reconstruct_matrices(lines: list[dict]) -> list[dict]:
    """行をスキャンし、行列を成すセル群を1つの $$pmatrix$$ 行に置き換える。"""
    cells = [line for line in lines if _is_cell(line)]
    if len(cells) < 3:
        return lines

    remove: set[int] = set()
    added: list[dict] = []
    for cluster in _cluster_cells(cells):
        if len(cluster) < 3:
            continue
        latex = _matrix_latex(cluster)
        if latex is None:
            continue
        for member in cluster:
            remove.add(id(member))
        ys = [m["yc"] for m in cluster]
        added.append(
            {
                "x0": min(m["x0"] for m in cluster),
                "x1": max(m["x1"] for m in cluster),
                "yc": (min(ys) + max(ys)) / 2,  # 中心。読み順で式リードと同じ行に並ぶ
                "text": latex,
            }
        )

    if not added:
        return lines
    kept = [line for line in lines if id(line) not in remove]
    return kept + added


def _page_text(page) -> str:
    """1ページを行列再構成つきで読み順(上→下, 左→右)のテキストにする。

    同じベースライン(y が近い)の断片は1つの視覚行とみなし、左→右に並べる。
    こうしないと「f(...)↦[行列](6.3)」が y のわずかな差で逆順に並んでしまう。
    """
    lines = _reconstruct_matrices(_page_lines(page))
    rows: list[list[dict]] = []
    for line in sorted(lines, key=lambda line: -line["yc"]):
        if rows and rows[-1][0]["yc"] - line["yc"] <= _ROW_SORT_TOL:
            rows[-1].append(line)
        else:
            rows.append([line])

    ordered: list[dict] = []
    for row in rows:
        row.sort(key=lambda line: line["x0"])
        ordered.extend(row)
    return "\n".join(line["text"] for line in ordered)


def _join_wrapped(lines: list[str]) -> str:
    """折り返された行を1つの文字列に連結する。

    英文は単語が密着しないよう空白でつなぎ、日本語(非ASCII境界)は密着させる。
    こうしておくと segmenter が行ではなく句点「。」で文分割でき、文が壊れない。
    """
    out = ""
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if not out:
            out = line
            continue
        out += (" " + line) if out[-1].isascii() else line
    return out


def _has_cjk(line: str) -> bool:
    return bool(_CJK.search(line))


def _is_verbatim(line: str) -> bool:
    """数式/行列の行とみなすか。日本語なし かつ (とても短い or 数式記号を含む)。

    PDF には2次元配置(行列・分数)の情報が無く、行ごとにバラけて抽出される。
    連続する verbatim 行は1ブロックに改行付きでまとめ、隙間なく縦に並べて崩れを防ぐ。
    「日本語なし」だけだと英文の地の文まで巻き込むため、短さ/数式記号で絞り込む。
    """
    if _has_cjk(line):
        return False
    return len(line) <= _VERBATIM_MAX or bool(_MATH_SIGNAL.search(line))


def _paragraphs(page_text: str) -> list[str]:
    """1ページ分のテキストを段落に復元する。

    pdfminer は折り返し位置にも空行を挿入するため、空行だけでは段落を判定できない。
    そこで「文末記号で終わる行」「章節見出し」を区切りに、折り返し行は前行へ連結する。
    日本語を含まない行(数式/行列の各行)は、連続するものを改行付きで1ブロックにまとめ、
    別行立ての固まりとして縦に並ぶようにする(行列が大きな余白で分断されるのを防ぐ)。
    """
    paragraphs: list[str] = []
    prose: list[str] = []  # 折り返し連結する地の文
    verbatim: list[str] = []  # 連続する数式/行列行(改行を保つ)

    def flush_prose() -> None:
        if prose:
            paragraphs.append(_join_wrapped(prose))
            prose.clear()

    def flush_verbatim() -> None:
        if verbatim:
            paragraphs.append("\n".join(verbatim))
            verbatim.clear()

    for raw in page_text.split("\n"):
        line = _FOOTNOTE_DEF.sub("", _CID.sub("", raw)).strip()
        if not line or _PAGE_NUMBER.fullmatch(line):
            continue
        if _SECTION_HEAD.match(line):
            flush_verbatim()
            flush_prose()
            paragraphs.append(line)
            continue
        if _is_verbatim(line):
            flush_prose()
            verbatim.append(line)
            continue
        flush_verbatim()
        prose.append(line)
        if line.endswith(_SENTENCE_END):
            flush_prose()
    flush_verbatim()
    flush_prose()
    return [p for p in paragraphs if p]


def _first_meaningful_line(text: str) -> str:
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped[:_TITLE_MAX]
    return ""


def _decode_pdf_string(value) -> str:
    """PDF メタデータの値(bytes/PSLiteral/str)を可能な範囲で文字列化する。"""
    if isinstance(value, PSLiteral):
        value = value.name
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
        if raw.startswith(b"\xfe\xff"):  # UTF-16BE BOM
            return raw.decode("utf-16", errors="ignore").strip()
        for enc in ("utf-8", "latin-1"):
            try:
                return raw.decode(enc).strip()
            except UnicodeDecodeError:
                continue
    return ""


def _metadata_title(data: bytes) -> str:
    try:
        document = PDFDocument(PDFParser(io.BytesIO(data)))
    except Exception:  # noqa: BLE001 - 壊れたメタデータでも本文抽出は続けたい
        return ""
    for info in document.info or []:
        title = _decode_pdf_string(info.get("Title", b""))
        if title:
            return title[:_TITLE_MAX]
    return ""


def extract_pdf_content(data: bytes, fallback_title: str = "") -> ScrapedContent:
    """PDF を本文抽出する。

    title の優先順位: メタデータ /Title → fallback_title(URLのファイル名など) → 先頭行。
    学術 PDF は /Title を持たないことが多く、先頭行がノンブルになりがちなので
    呼び出し側からファイル名を渡せるようにしている。
    """
    # 座標つきで取得し、行列を再構成しながらページ本文を組み立てる。
    page_texts = [
        _page_text(page)
        for page in extract_pages(io.BytesIO(data), laparams=LAParams())
    ]

    blocks: list[Block] = []
    seen_headers: set[str] = set()
    for page_text in page_texts:
        for paragraph in _paragraphs(page_text):
            # 各ページ上部で繰り返されるランニングヘッダは最初の1回だけ残す。
            if _RUNNING_HEADER.match(paragraph) and len(paragraph) <= 40:
                if paragraph in seen_headers:
                    continue
                seen_headers.add(paragraph)
            blocks.append(Block(kind="text", text=paragraph))

    title = (
        _metadata_title(data)
        or fallback_title.strip()
        or _first_meaningful_line("\n".join(page_texts))
    )

    text = "\n".join(b.text for b in blocks)
    return ScrapedContent(title=title, text=text, blocks=blocks)
