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


def _replace_math_with_tex(soup: BeautifulSoup) -> None:
    """<math> を LaTeX 区切り文字に置換する(arXiv HTML / LaTeXML 対応)。

    MathML をそのまま get_text すると「見た目(Sn)+TeX注釈(S_{n})」が連結され、
    数式が壊れる。alttext(無ければ x-tex 注釈)の TeX を取り出し、
    display=block なら $$...$$、それ以外は $...$ で囲んで差し替える。
    """
    for math in soup.find_all("math"):
        tex = (math.get("alttext") or "").strip()
        if not tex:
            ann = math.find("annotation", attrs={"encoding": "application/x-tex"})
            tex = ann.get_text().strip() if ann else ""
        if not tex:
            math.decompose()  # TeXが取れない場合は二重テキストを残さず捨てる
            continue
        wrapped = f"$${tex}$$" if math.get("display") == "block" else f"${tex}$"
        math.replace_with(wrapped)


def _is_block_element(tag) -> bool:
    """本文ブロックとして拾う要素か。別行立て数式(LaTeXMLの数式テーブル)も含める。"""
    if tag.name in ("h1", "h2", "h3", "p", "li"):
        return True
    return tag.name == "table" and "ltx_equation" in (tag.get("class") or [])


def extract_content(html: str) -> ScrapedContent:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    # 数式はテキスト抽出前に LaTeX 区切りへ変換しておく。
    _replace_math_with_tex(soup)

    title = soup.title.get_text(strip=True) if soup.title else ""

    main = soup.find("article") or soup.find("main") or soup.body or soup
    blocks: list[Block] = []
    for el in main.find_all(_is_block_element):
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


def _is_textual(content_type: str) -> bool:
    """取り込み可能なテキスト系コンテンツか判定する(content_type は小文字前提)。"""
    return (
        content_type.startswith("text/")
        or "html" in content_type
        or "xml" in content_type
    )


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

        # PDF/画像 等のバイナリを text として処理すると本文が壊れ(NUL混入で保存失敗)、
        # 原因の分からない500になる。HTML/テキスト系以外はここで明示的に弾く。
        content_type = response.headers.get("content-type", "").lower()
        if content_type and not _is_textual(content_type):
            raise ScrapeError(
                f"このページはHTMLではないため取り込めません"
                f"(content-type: {content_type}): {url}"
            )
        return extract_content(response.text)
