"""ステップ4: Scraper のテスト。

- 本文抽出は純粋関数 extract_content として単体テストする。
- ネットワークは httpx.MockTransport で差し替え、成功/失敗の両方を検証する。
"""

import httpx
import pytest

from app.services.scraper import HttpScraper, ScrapeError, extract_content

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
