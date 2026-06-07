"""URLから記事本文を取得する Scraper。

- extract_content: HTML→本文の純粋関数(ネットワーク非依存でテストしやすい)。
- HttpScraper: httpx で取得して extract_content に渡す具象。client を注入できる(DIP)。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

# 本文として無関係なタグ。抽出前に取り除く。
_NOISE_TAGS = ["script", "style", "nav", "header", "footer", "aside", "form"]

# Wikipedia 等は python-httpx の既定UAを 403 で弾くため、ブラウザ風のヘッダを送る。
_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36 (marker-reader)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.8",
}


_HEADING_TAGS = {"h1", "h2", "h3"}


@dataclass
class Block:
    """本文の1ブロック。kind は "heading"(見出し) または "text"(段落)。"""

    kind: str
    text: str


@dataclass
class ScrapedContent:
    title: str
    text: str  # 改行連結(互換用)
    blocks: list[Block] = field(default_factory=list)


class ScrapeError(Exception):
    """スクレイピングに失敗したことを表す明示的な例外。"""


def extract_content(html: str) -> ScrapedContent:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""

    main = soup.find("article") or soup.find("main") or soup.body or soup
    blocks: list[Block] = []
    for el in main.find_all(["h1", "h2", "h3", "p", "li"]):
        text = el.get_text(strip=True)
        if not text:
            continue
        kind = "heading" if el.name in _HEADING_TAGS else "text"
        blocks.append(Block(kind=kind, text=text))

    text = "\n".join(b.text for b in blocks)
    if not text:
        text = main.get_text(separator="\n", strip=True)
        if text:
            blocks = [Block(kind="text", text=text)]

    return ScrapedContent(title=title, text=text, blocks=blocks)


class Scraper(ABC):
    @abstractmethod
    def fetch(self, url: str) -> ScrapedContent:
        ...


class HttpScraper(Scraper):
    def __init__(self, client: httpx.Client | None = None):
        # 大きめ/低速なページでもタイムアウトしにくいよう20sに余裕を持たせる。
        self._client = client or httpx.Client(timeout=20.0, follow_redirects=True)

    def fetch(self, url: str) -> ScrapedContent:
        try:
            # 注入された client でもUAが効くよう、リクエスト毎にヘッダを渡す。
            response = self._client.get(url, headers=_DEFAULT_HEADERS)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # 実ステータスを含めることで次回以降の原因調査を不要にする。
            raise ScrapeError(
                f"取得に失敗しました(HTTP {exc.response.status_code}): {url}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ScrapeError(
                f"取得に失敗しました({type(exc).__name__}): {url}"
            ) from exc
        return extract_content(response.text)
