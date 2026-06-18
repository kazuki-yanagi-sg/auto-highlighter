"""PDF 本文抽出 extract_pdf_content の単体テスト。

ネットワーク非依存で検証するため、テスト内で最小の有効な PDF バイト列を生成する。
日本語の埋め込みフォントは持たないので、抽出ロジック(行連結・タイトル採用・ブロック化)
を ASCII で検証する。実 PDF(日本語)は別途ライブ実行で確認する。
"""

from __future__ import annotations

from app.services.pdf import (
    _paragraphs,
    _reconstruct_matrices,
    extract_pdf_content,
)


def make_pdf(pages: list[list[str]], title: str | None = None) -> bytes:
    """各ページの行リストから最小の PDF バイト列を組み立てる(text-layer 付き)。"""
    contents: list[bytes] = []
    for lines in pages:
        ops = "BT /F1 18 Tf 72 720 Td 24 TL\n"
        for i, line in enumerate(lines):
            esc = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops += f"({esc}) Tj\n" if i == 0 else f"T* ({esc}) Tj\n"
        ops += "ET"
        contents.append(ops.encode("latin-1"))

    objects: list[bytes] = []

    def page_obj(idx: int) -> bytes:
        font = b" /Resources << /Font << /F1 %d 0 R >> >>" % font_num
        return (
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 612 792]" % pages_num
            + font
            + b" /Contents %d 0 R >>" % content_nums[idx]
        )

    n_pages = len(contents)
    # 採番: 1=Catalog, 2=Pages, 3..=Page, ..=Contents, font, (info)
    catalog_num, pages_num = 1, 2
    page_nums = list(range(3, 3 + n_pages))
    content_nums = list(range(3 + n_pages, 3 + 2 * n_pages))
    font_num = 3 + 2 * n_pages
    info_num = font_num + 1 if title else None

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = b" ".join(b"%d 0 R" % n for n in page_nums)
    objects.append(b"<< /Type /Pages /Kids [%b] /Count %d >>" % (kids, n_pages))
    for i in range(n_pages):
        objects.append(page_obj(i))
    for i in range(n_pages):
        stream = contents[i]
        objects.append(
            b"<< /Length %d >>\nstream\n%b\nendstream" % (len(stream), stream)
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    if title:
        objects.append(b"<< /Title (%b) >>" % title.encode("latin-1"))

    parts = [b"%PDF-1.4\n"]
    offsets: list[int] = []
    for num, body in enumerate(objects, start=1):
        offsets.append(sum(len(p) for p in parts))
        parts.append(b"%d 0 obj\n%b\nendobj\n" % (num, body))

    xref_pos = sum(len(p) for p in parts)
    total = len(objects)
    xref = b"xref\n0 %d\n0000000000 65535 f \n" % (total + 1)
    for off in offsets:
        xref += b"%010d 00000 n \n" % off
    trailer = b"trailer\n<< /Size %d /Root 1 0 R" % (total + 1)
    if info_num:
        trailer += b" /Info %d 0 R" % info_num
    trailer += b" >>\nstartxref\n%d\n%%%%EOF" % xref_pos
    return b"".join(parts) + xref + trailer


def test_extract_pdf_content_pulls_text():
    data = make_pdf([["Hello PDF world.", "This is the second line."]])
    content = extract_pdf_content(data)
    assert "Hello PDF world." in content.text
    assert "This is the second line." in content.text


def test_extract_pdf_content_uses_metadata_title():
    data = make_pdf([["body text here."]], title="My Paper Title")
    content = extract_pdf_content(data)
    assert content.title == "My Paper Title"


def test_extract_pdf_content_falls_back_to_first_line_for_title():
    data = make_pdf([["An Introduction to Things", "details follow."]])
    content = extract_pdf_content(data)
    assert content.title == "An Introduction to Things"


def test_extract_pdf_content_makes_text_blocks_per_page():
    data = make_pdf([["page one text."], ["page two text."]])
    content = extract_pdf_content(data)
    assert all(b.kind == "text" for b in content.blocks)
    assert any("page one" in b.text for b in content.blocks)
    assert any("page two" in b.text for b in content.blocks)


def test_extract_pdf_content_joins_wrapped_english_lines_with_space():
    # 折り返された英文は単語が密着しないよう空白でつなぐ。
    data = make_pdf([["the quick brown", "fox jumps."]])
    content = extract_pdf_content(data)
    assert "brown fox" in content.text


def test_extract_pdf_content_empty_pdf_returns_empty():
    data = make_pdf([[]])
    content = extract_pdf_content(data)
    assert content.text == ""
    assert content.blocks == []


# --- _paragraphs: 改行・段落構造の復元(pdfminer は行ごとに空行を挟む前提) ---


def test_paragraphs_joins_wrapped_japanese_sentence():
    # 折り返された1文(句点なしで行が割れる)は1段落に連結する。
    page = "ここでは, リー代数を紹\n\n介する.\n\n次の話題.\n"
    paras = _paragraphs(page)
    assert "ここでは, リー代数を紹介する." in paras
    assert "次の話題." in paras


def test_paragraphs_keeps_display_equation_on_own_block():
    # 別行立て数式(日本語を含まない数式行)は独立した段落にして改行を保つ。
    page = "積の定義より,\n\n[X, [Y, Z]] = X(Y Z - ZY)\n\nとなる.\n"
    paras = _paragraphs(page)
    assert any(p.startswith("[X, [Y, Z]]") for p in paras)
    assert any(p.startswith("積の定義より") for p in paras)
    assert any(p.startswith("となる") for p in paras)


def test_paragraphs_section_heading_is_separate():
    page = "6.2.1 リー代数の例\n\nここでは紹介する.\n"
    paras = _paragraphs(page)
    assert "6.2.1 リー代数の例" in paras
    assert "ここでは紹介する." in paras


def test_paragraphs_groups_consecutive_math_rows_into_one_block():
    # 行列など連続する数式行(日本語なし)は1ブロックに改行付きでまとまる。
    page = "f : g -> gl2(R) :\n\nb a\n\n0 -a\n\n(6.3)\n\n次の話.\n"
    paras = _paragraphs(page)
    math = next(p for p in paras if p.startswith("f :"))
    assert "\n" in math
    assert "b a" in math and "0 -a" in math and "(6.3)" in math
    assert "次の話." in paras


def test_paragraphs_strips_cid_artifacts():
    # pdfminer が出す未マップグリフ (cid:NNN) は本文に残さない。
    page = "証明おわり (cid:164)\n"
    paras = _paragraphs(page)
    assert paras
    assert all("cid:" not in p for p in paras)


def test_paragraphs_drops_page_number_lines():
    # ノンブル(ページ番号)だけの行は本文ではないので落とす。
    page = "47\n\nここに本文がある.\n"
    paras = _paragraphs(page)
    assert "47" not in paras
    assert "ここに本文がある." in paras


def test_paragraphs_strips_footnote_glossary_keeps_body():
    # ページ下部の脚注定義(*N 英単語)は除去し、混在した本文は残す。
    page = (
        "*1 Lie algebra *2 real Lie algebra\n\n"
        "(i) f は全単射, *9 Lie subalgebra *10 homomorphism\n"
    )
    paras = _paragraphs(page)
    assert all("Lie algebra" not in p for p in paras)
    assert all("subalgebra" not in p for p in paras)
    assert any("全単射" in p for p in paras)


def test_paragraphs_keeps_inline_footnote_marker():
    # 本文の脚注マーカー(後ろが日本語)は壊さない。
    page = "これは リー代数*1 と呼ぶ.\n"
    paras = _paragraphs(page)
    assert any("リー代数*1" in p for p in paras)


def test_running_header_deduplicated_across_pages():
    # 各ページで繰り返される節見出し(ランニングヘッダ)は1回だけ残す。
    data = make_pdf(
        [
            ["6.2 Examples", "First body sentence."],
            ["6.2 Examples", "Second body sentence."],
        ]
    )
    content = extract_pdf_content(data)
    headers = [b.text for b in content.blocks if b.text == "6.2 Examples"]
    assert len(headers) == 1


# --- 行列の座標再構成 ---


def test_matrix_reconstructed_from_coordinates():
    # (6.3) の行列: a,b(上段) / 0,−a(下段) を pmatrix に組み立てる。
    lines = [
        {"x0": 363.5, "x1": 369.8, "yc": 216.4, "text": "a"},
        {"x0": 392.3, "x1": 397.4, "yc": 216.4, "text": "b"},
        {"x0": 363.8, "x1": 397.4, "yc": 202.0, "text": "0 −a"},
    ]
    out = _reconstruct_matrices(lines)
    mats = [l["text"] for l in out if "pmatrix" in l["text"]]
    assert mats == [r"$$\begin{pmatrix} a & b \\ 0 & -a \end{pmatrix}$$"]


def test_inconsistent_rows_not_treated_as_matrix():
    # 各行のセル数が揃わない塊は行列と断定しない(誤った行列を出さない)。
    lines = [
        {"x0": 100.0, "x1": 140.0, "yc": 200.0, "text": "x y z"},
        {"x0": 100.0, "x1": 110.0, "yc": 188.0, "text": "w"},
        {"x0": 120.0, "x1": 130.0, "yc": 188.0, "text": "v"},
    ]
    out = _reconstruct_matrices(lines)
    assert all("pmatrix" not in l["text"] for l in out)
