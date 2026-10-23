"""Kolektor RSS: feed situs bank dan Google News RSS per bank."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from urllib.parse import quote
from xml.etree import ElementTree as ET

from ..config import Bank
from ..http_client import AccessError, Fetcher
from ..models import Item
from .base import CollectResult

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"

# CATATAN KEPATUHAN (keputusan koordinator):
#   news.google.com/robots.txt memuat "Disallow: /" dan allow-list pendek yang
#   TIDAK mencakup /rss/search. Fetcher default MEMATUHI robots.txt, jadi kueri
#   berita ini akan gagal dengan "dilarang oleh robots.txt" dan jalur Tier-3
#   (berita per bank) tidak menghasilkan kandidat. Ini perilaku SENGAJA, sesuai
#   DESIGN.md ("Robots.txt dipatuhi") dan laporan riset ("blokir tidak diakali").
#   Bila koordinator memutuskan feed RSS sindikasi ini boleh diakses, caranya
#   BUKAN mengakali blokir, melainkan keputusan kebijakan yang dicatat: jalankan
#   Fetcher(respect_robots=False) HANYA untuk host news.google.com, atau pakai
#   sumber berita lain. Jangan ubah deteksi blokir/robots secara diam-diam.


def _text(elem: Optional[ET.Element]) -> str:
    return (elem.text or "").strip() if elem is not None else ""


def _parse_rss_date(raw: str) -> Optional[str]:
    """Parse tanggal RSS (RFC 822) -> "YYYY-MM-DD", atau None."""
    raw = (raw or "").strip()
    if not raw:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Fallback ISO.
    try:
        return datetime.fromisoformat(raw[:19]).strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_rss(xml_text: str, bank_name: str, source_type: str) -> list[Item]:
    """Ubah XML RSS/Atom menjadi daftar Item mentah (belum disaring)."""
    items: list[Item] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    # RSS 2.0: channel/item
    for node in root.iter("item"):
        title = _text(node.find("title"))
        link = _text(node.find("link"))
        desc = _text(node.find("description"))
        pub = _parse_rss_date(_text(node.find("pubDate")))
        # Google News RSS menaruh nama media di <source url="...">.
        source_el = node.find("source")
        media = _text(source_el) if source_el is not None else ""
        source_url = source_el.get("url", "") if source_el is not None else ""
        if title and link:
            items.append(
                Item(
                    bank=bank_name,
                    title=title,
                    url=link,
                    published=pub,
                    source_type=source_type,
                    evidence=desc[:500],
                    media_name=media,
                    # Simpan URL penerbit sementara di evidence-tail tidak perlu;
                    # dipakai langsung untuk penilaian kredibilitas via media_url.
                    media_url=source_url,
                )
            )

    # Atom: entry
    atom_ns = "{http://www.w3.org/2005/Atom}"
    for node in root.iter(f"{atom_ns}entry"):
        title = _text(node.find(f"{atom_ns}title"))
        link_el = node.find(f"{atom_ns}link")
        link = link_el.get("href", "") if link_el is not None else ""
        summary = _text(node.find(f"{atom_ns}summary"))
        pub = _parse_rss_date(_text(node.find(f"{atom_ns}updated")))
        if title and link:
            items.append(
                Item(
                    bank=bank_name,
                    title=title,
                    url=link,
                    published=pub,
                    source_type=source_type,
                    evidence=summary[:500],
                )
            )
    return items


def collect_rss(fetcher: Fetcher, bank: Bank, url: str) -> CollectResult:
    """Ambil satu feed RSS sumber `public`."""
    try:
        res = fetcher.fetch(url)
    except AccessError as exc:
        return CollectResult(ok=False, error=exc.reason)
    items = parse_rss(res.text, bank.name, source_type="portal")
    return CollectResult(items=items, ok=True)


def build_news_query(bank: Bank, edc_terms: list[str]) -> str:
    """Bangun kueri Google News: (alias1 OR alias2) (edc1 OR edc2 ...)."""
    names = " OR ".join(f'"{a}"' for a in bank.news_terms)
    edc = " OR ".join(f'"{t}"' for t in edc_terms)
    return f"({names}) ({edc})"


def collect_news(
    fetcher: Fetcher, bank: Bank, edc_terms: list[str]
) -> CollectResult:
    """Cari berita per bank lewat Google News RSS memakai aliases + kata EDC."""
    query = build_news_query(bank, edc_terms)
    url = GOOGLE_NEWS_RSS.format(query=quote(query))
    try:
        res = fetcher.fetch(url)
    except AccessError as exc:
        return CollectResult(ok=False, error=exc.reason)
    items = parse_rss(res.text, bank.name, source_type="berita")
    return CollectResult(items=items, ok=True)
