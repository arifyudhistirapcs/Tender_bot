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
