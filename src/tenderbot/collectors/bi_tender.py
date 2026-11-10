"""Kolektor tabel tender Bank Indonesia."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin

from ..config import Bank
from ..dates_id import parse_single_date
from ..http_client import AccessError, Fetcher
from ..models import Item
from .base import CollectResult

_OPEN_TABLE_MARKER = "Pengadaan yang sedang dibuka"
_ROW_RE = re.compile(
    r'<tr\b[^>]*\bclass\s*=\s*["\']table-body-om["\'][^>]*>.*?</tr>',
    re.IGNORECASE | re.DOTALL,
)
_TABLE_RE = re.compile(r"<table\b[^>]*>.*?</table>", re.IGNORECASE | re.DOTALL)


class _TenderRowParser(HTMLParser):
    """Ambil lima sel dari satu baris tender BI tanpa memisah span judul."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cells: list[str] = []
        self._cell_parts: list[str] | None = None
        self.href = ""
        self._in_link = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "td":
            self._cell_parts = []
        elif tag.lower() == "a" and self._cell_parts is not None:
            self._in_link = True
            self.href = dict(attrs).get("href") or ""

    def handle_data(self, data: str) -> None:
        if self._cell_parts is not None:
            # BI memecah kata (mis. P|eng|adaan) menjadi banyak span. Simpan
            # node persis berurutan, lalu rapikan hanya setelah seluruh sel.
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a":
            self._in_link = False
        elif tag.lower() == "td" and self._cell_parts is not None:
            self.cells.append("".join(self._cell_parts))
            self._cell_parts = None


def _clean_text(value: str) -> str:
    return " ".join((value or "").replace("\u200b", "").split())


def parse_bi_tender(html: str, bank: Bank, source_url: str) -> list[Item]:
    """Parse hanya tabel pertama setelah label pengadaan BI yang sedang buka."""
    marker_at = html.find(_OPEN_TABLE_MARKER)
    if marker_at < 0:
        return []
    table = _TABLE_RE.search(html, marker_at)
    if table is None:
        return []

    items: list[Item] = []
    for row in _ROW_RE.findall(table.group(0)):
        parser = _TenderRowParser()
        parser.feed(row)
        if len(parser.cells) < 4 or not parser.href:
            continue
        posted = parse_single_date(_clean_text(parser.cells[0]))
        reg_close = parse_single_date(_clean_text(parser.cells[2]))
        title = _clean_text(parser.cells[1])
        status = _clean_text(parser.cells[3])
        if not title:
            continue
        evidence = " | ".join(
            value for value in (
                _clean_text(parser.cells[0]), title, _clean_text(parser.cells[2]), status,
            ) if value
        )
        items.append(Item(
            bank=bank.name,
            group=bank.group,
            title=title,
            url=urljoin(source_url, parser.href),
            published=posted.isoformat() if posted else None,
            posted=posted.isoformat() if posted else None,
            reg_close=reg_close.isoformat() if reg_close else None,
            source_type="portal",
            evidence=evidence,
        ))
    return items


def collect_bi_tender(fetcher: Fetcher, bank: Bank, url: str) -> CollectResult:
    """Ambil tabel pengadaan BI yang sedang dibuka."""
    try:
        response = fetcher.fetch(url)
    except AccessError as exc:
        return CollectResult(ok=False, error=exc.reason)
    items = parse_bi_tender(response.text, bank, url)
    if not items:
        return CollectResult(ok=False, error="0 baris tabel pengadaan BI")
    return CollectResult(items=items)
