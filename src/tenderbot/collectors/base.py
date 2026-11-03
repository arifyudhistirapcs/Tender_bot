"""Alat bersama kolektor dan tipe hasil."""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Optional

from ..models import Item


@dataclass
class CollectResult:
    """Hasil satu kolektor terhadap satu sumber."""

    items: list[Item] = field(default_factory=list)
    ok: bool = True
    error: Optional[str] = None  # alasan gagal akses bila ok=False


class _LinkExtractor(HTMLParser):
    """Ambil (href, teks) dari semua <a>."""

    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: Optional[str] = None
        self._text_parts: list[str] = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._href = href
                self._text_parts = []
                self._depth = 1

    def handle_data(self, data):
        if self._href is not None:
            self._text_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            text = " ".join(" ".join(self._text_parts).split())
            self.links.append((self._href, text))
            self._href = None
            self._text_parts = []


def extract_links(html: str) -> list[tuple[str, str]]:
    """Daftar (href, teks) dari HTML."""
    parser = _LinkExtractor()
    parser.feed(html)
    return parser.links


class _ListedLinkExtractor(HTMLParser):
    """Ambil tautan beserta teks elemen ``li`` tempat tautan berada."""

    def __init__(self):
        super().__init__()
        self._stack: list[dict] = []
        self._links: list[dict] = []

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag.lower(), "attrs": dict(attrs), "text": [],
                "ancestors": tuple(self._stack)}
        self._stack.append(node)
        if node["tag"] == "a" and node["attrs"].get("href"):
            self._links.append(node)

    def handle_data(self, data):
        for node in self._stack:
            node["text"].append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index]["tag"] == tag:
                del self._stack[index:]
                break

    @staticmethod
    def _text(node: dict) -> str:
        return " ".join(" ".join(node["text"]).split())

    def links(self) -> list[tuple[str, str, str]]:
        out: list[tuple[str, str, str]] = []
        for node in self._links:
            href = node["attrs"]["href"]
            title = self._text(node)
            container = next(
                (parent for parent in reversed(node["ancestors"])
                 if parent["tag"] == "li"),
                None,
            )
            context = self._text(container) if container else title
            out.append((href, title, context))
        return out


def extract_listed_links(html: str) -> list[tuple[str, str, str]]:
    """Daftar ``(href, judul, teks_li)`` dari HTML daftar pengumuman.

    Tanggal sering berada di elemen saudara tautan judul, misalnya ``<time>``
    atau ``<li>`` lain dalam kartu daftar. Teks kontainer terdekat membuatnya
    tersedia bagi kolektor tanpa mengikat parser ke markup satu bank.
    """
    parser = _ListedLinkExtractor()
    parser.feed(html)
    return parser.links()


class _TextStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = _TextStripper()
    parser.feed(html)
    joined = " ".join(p for p in parser.parts if p.strip())
    return " ".join(joined.split())
