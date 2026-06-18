"""ステップ4: Scraper のテスト。

- 本文抽出は純粋関数 extract_content として単体テストする。
- ネットワークは httpx.MockTransport で差し替え、成功/失敗の両方を検証する。
"""

import httpx
import pytest

from app.services.scraper import HttpScraper, ScrapeError, extract_content
from tests.unit.test_pdf import make_pdf

_HTML = """
<html>
  <head><title>テスト記事のタイトル</title></head>
  <body>
    <script>var a = 1;</script>
    <style>.x{color:red}</style>
    <nav>メニュー</nav>
    <article>
      <h1>見出し</h1>
      <p>これは第一段落です。</p>
      <p>これは第二段落です。</p>
    </article>
    <footer>フッター</footer>
  </body>
</html>
"""


def test_extract_content_pulls_title_and_body():
    content = extract_content(_HTML)
    assert content.title == "テスト記事のタイトル"
    assert "これは第一段落です。" in content.text
    assert "これは第二段落です。" in content.text


def test_extract_content_drops_script_and_style():
    content = extract_content(_HTML)
    assert "var a" not in content.text
    assert "color:red" not in content.text


# arXiv HTML(LaTeXML)の数式。<math> は MathML の見た目と TeX 注釈の二重構造。
_ARXIV_INLINE = """
<html><head><title>arXiv paper</title></head><body><article>
<p>the symmetric group<math alttext="S_{n}" display="inline"><semantics>
<msub><mi>S</mi><mi>n</mi></msub>
<annotation encoding="application/x-tex">S_{n}</annotation></semantics></math>here.</p>
</article></body></html>
"""

_ARXIV_DISPLAY = """
<html><head><title>arXiv paper</title></head><body><article>
<div class="ltx_para"><p class="ltx_p">We have the limit.</p></div>
<table class="ltx_equation ltx_eqn_table"><tbody><tr class="ltx_equation"><td class="ltx_eqn_cell">
<math alttext="\\lim_{n\\to\\infty}x_{n}=x." display="block"><semantics>
<annotation encoding="application/x-tex">\\lim_{n\\to\\infty}x_{n}=x.</annotation></semantics></math>
</td></tr></tbody></table>
</article></body></html>
"""


def test_extract_content_inline_math_uses_tex_not_doubled_mathml():
    content = extract_content(_ARXIV_INLINE)
    # MathML の見た目とTeXが連結された "SnS_{n}" が出てはいけない。
    assert "SnS_{n}" not in content.text
    # alttext の TeX を $...$ で囲んで出す(フロントの KaTeX がそのまま描画できる)。
    assert "$S_{n}$" in content.text


def test_extract_content_captures_display_equation_table():
    content = extract_content(_ARXIV_DISPLAY)
    # 別行立て数式は table.ltx_equation 内にあるが、$$...$$ で本文に含める。
    assert "$$\\lim_{n\\to\\infty}x_{n}=x.$$" in content.text
    assert "We have the limit." in content.text


def _scraper_with_handler(handler) -> HttpScraper:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return HttpScraper(client=client)


def test_fetch_returns_content_on_success():
    scraper = _scraper_with_handler(lambda req: httpx.Response(200, text=_HTML))
    content = scraper.fetch("https://example.com/a")
    assert content.title == "テスト記事のタイトル"
    assert "第一段落" in content.text


def test_fetch_sends_browser_like_user_agent():
    # Wikipedia 等は python-httpx の既定UAを 403 で弾くため、ブラウザ風UAを送る。
    seen: dict[str, str] = {}

    def handler(req):
        seen["ua"] = req.headers.get("user-agent", "")
        return httpx.Response(200, text=_HTML)

    scraper = _scraper_with_handler(handler)
    scraper.fetch("https://example.com/a")
    assert seen["ua"]
    assert "python-httpx" not in seen["ua"].lower()


def test_fetch_raises_on_http_error_with_status_in_message():
    scraper = _scraper_with_handler(lambda req: httpx.Response(404, text="nope"))
    with pytest.raises(ScrapeError) as excinfo:
        scraper.fetch("https://example.com/missing")
    # 次回以降の調査を不要にするため、実ステータスをメッセージに含める。
    assert "404" in str(excinfo.value)


def test_fetch_raises_on_connection_error_with_cause_in_message():
    def boom(req):
        raise httpx.ConnectError("失敗", request=req)

    scraper = _scraper_with_handler(boom)
    with pytest.raises(ScrapeError) as excinfo:
        scraper.fetch("https://example.com/down")
    assert "ConnectError" in str(excinfo.value)


def test_fetch_rejects_non_html_non_pdf_binary():
    # 画像等のバイナリを text として処理すると NUL 混入でDB保存が壊れ500になる。
    # HTML/テキスト/PDF 以外は取得段階で明示的に弾き、分かるメッセージで知らせる。
    def handler(req):
        return httpx.Response(
            200,
            content=b"\x89PNG\x00binary",
            headers={"content-type": "image/png"},
        )

    scraper = _scraper_with_handler(handler)
    with pytest.raises(ScrapeError) as excinfo:
        scraper.fetch("https://example.com/photo.png")
    assert "image/png" in str(excinfo.value)


def test_fetch_extracts_pdf_when_content_type_is_pdf():
    # PDF は拒否せず本文抽出する(application/pdf)。
    data = make_pdf([["Hello from a PDF."]], title="PDF Title")

    def handler(req):
        return httpx.Response(
            200, content=data, headers={"content-type": "application/pdf"}
        )

    scraper = _scraper_with_handler(handler)
    content = scraper.fetch("https://example.com/paper.pdf")
    assert content.title == "PDF Title"
    assert "Hello from a PDF." in content.text


def test_fetch_extracts_pdf_by_url_suffix_when_content_type_generic():
    # サーバが octet-stream を返しても、URL が .pdf なら PDF として扱う。
    data = make_pdf([["Body of the document."]])

    def handler(req):
        return httpx.Response(
            200,
            content=data,
            headers={"content-type": "application/octet-stream"},
        )

    scraper = _scraper_with_handler(handler)
    content = scraper.fetch("https://example.com/files/doc.pdf")
    assert "Body of the document." in content.text


def test_fetch_wraps_broken_pdf_as_scrape_error():
    # 壊れたPDF/解析失敗は原因不明の500ではなく ScrapeError にして伝える。
    def handler(req):
        return httpx.Response(
            200,
            content=b"%PDF-1.4 not really a pdf",
            headers={"content-type": "application/pdf"},
        )

    scraper = _scraper_with_handler(handler)
    with pytest.raises(ScrapeError):
        scraper.fetch("https://example.com/broken.pdf")


_HTML_CODE = """
<html><head><title>コード記事</title></head><body><article>
<p>本文の説明です。</p>
<div class="code-frame"><pre><code>def foo():
    return 1</code></pre></div>
</article></body></html>
"""


def test_extract_content_keeps_code_block_verbatim():
    # <pre> のコードは改行・字下げを保ったまま kind="code" で取り込む。
    content = extract_content(_HTML_CODE)
    codes = [b for b in content.blocks if b.kind == "code"]
    assert len(codes) == 1
    assert "def foo():" in codes[0].text
    assert "\n    return 1" in codes[0].text  # 改行と字下げが残る
    # 地の文は従来どおり取れる。
    assert any(b.kind == "text" and "本文の説明" in b.text for b in content.blocks)
