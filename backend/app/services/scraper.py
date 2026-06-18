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
    """本文ブロックとして拾う要素か。コードブロック(pre)・別行立て数式も含める。"""
    if tag.name in ("h1", "h2", "h3", "p", "li", "pre"):
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
        # コードブロック内の要素(span等)は pre 側でまとめて取るので個別には拾わない。
        if el.name != "pre" and el.find_parent("pre") is not None:
            continue
        if el.name == "pre":
            # コードは改行・字下げをそのまま保持する(strip すると整形が壊れる)。
            text = el.get_text().strip("\n")
            kind = "code"
        else:
            text = el.get_text(strip=True)
            kind = "heading" if el.name in _HEADING_TAGS else "text"
        if not text:
            continue
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


def _is_pdf(content_type: str, url: str) -> bool:
    """PDF として扱うか。content-type が pdf、または URL 末尾が .pdf なら真。

    一部サーバは PDF を application/octet-stream で返すため URL 拡張子も見る。
    """
    return "pdf" in content_type or url.split("?", 1)[0].lower().endswith(".pdf")


def _filename(url: str) -> str:
    """URL 末尾のファイル名から拡張子を除いた名前(タイトル代用)。"""
    path = url.split("?", 1)[0].rstrip("/")
    name = path.rsplit("/", 1)[-1]
    return name.rsplit(".", 1)[0] if "." in name else name


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

        content_type = response.headers.get("content-type", "").lower()

        # PDF は本文抽出する(遅延 import: pdfminer を HTML 専用利用時に読み込まない)。
        # 解析失敗(壊れたPDF/依存欠落等)は原因不明の500ではなく ScrapeError にして伝える。
        if _is_pdf(content_type, url):
            try:
                from app.services.pdf import extract_pdf_content

                return extract_pdf_content(
                    response.content, fallback_title=_filename(url)
                )
            except ScrapeError:
                raise
            except Exception as exc:  # noqa: BLE001
                raise ScrapeError(
                    f"PDFの解析に失敗しました({type(exc).__name__}): {url}"
                ) from exc

        # 画像 等のバイナリを text として処理すると本文が壊れ(NUL混入で保存失敗)、
        # 原因の分からない500になる。HTML/テキスト系以外はここで明示的に弾く。
        if content_type and not _is_textual(content_type):
            raise ScrapeError(
                f"このページはHTMLではないため取り込めません"
                f"(content-type: {content_type}): {url}"
            )
        return extract_content(response.text)
