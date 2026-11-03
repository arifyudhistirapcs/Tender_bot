"""Kolektor daftar HTML: ambil tautan pengumuman dari halaman arsip.

Dipakai untuk Bank Sumut (arsip jasa_barang) dan Bank Jatim (Lelang
Pengadaan). Strategi sengaja sederhana dan tahan-banting: ambil semua
<a>, buang yang jelas navigasi, jadikan teks tautan sebagai judul. Saringan
aturan (procurement + edc) yang akan menyisihkan tautan yang tidak relevan,
jadi kolektor tidak perlu menebak struktur tiap situs.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from ..config import Bank
from ..dates_id import parse_single_date
from ..http_client import AccessError, Fetcher
from ..models import Item
from .base import CollectResult, extract_listed_links

# Teks tautan yang jelas bukan judul pengumuman.
_SKIP_TEXTS = {
    "", "home", "beranda", "selengkapnya", "read more", "baca selengkapnya",
    "next", "prev", "previous", "berikutnya", "sebelumnya", "login", "masuk",
    "daftar", "english", "indonesia", "en", "id",
}
# Fragmen href yang bukan halaman pengumuman.
_SKIP_HREF_FRAGMENTS = (
    "mailto:", "tel:", "javascript:", "#", "/wp-login", "/feed",
    "facebook.com", "twitter.com", "instagram.com", "youtube.com",
    "linkedin.com", "/lelang/",  # menu lelang agunan Bank Sumut
    "lelangagunan.bankaltimtara.co.id",  # lelang jaminan, bukan pengadaan
)

# Tanggal awal yang kadang disatukan ke teks tautan daftar. Judul dibersihkan
# sesudah tanggal ini dibaca, agar fingerprint dan kartu tidak membawa prefix.
_RE_LEADING_DATE = re.compile(
    r"^\s*(?:[A-Za-z]+,\s*)?\d{1,2}\s+[A-Za-z]+\.?\s+\d{2,4}"
    r"\s*(?:[-|:\u2013\u2014]\s*)?",
    re.IGNORECASE,
)
_RE_TRAILING_DATE = re.compile(
    r"\s*(?:[-|:\u2013\u2014]\s*)?\d{1,2}\s+[A-Za-z]+\.?\s+\d{2,4}\s*$",
    re.IGNORECASE,
)


def _strip_date(pattern: re.Pattern, title: str) -> str:
    """Buang tanggal di awal/akhir judul HANYA bila potongan itu tanggal sah.

    Regex di atas menerima kata apa pun di posisi bulan, jadi judul seperti
    "10 Paket 2026 ..." akan ikut terpotong tanpa cek parse_single_date ini.
    """
    m = pattern.search(title)
    if m and parse_single_date(m.group(0)):
        return title[:m.start()] + title[m.end():]
    return title


def _looks_like_announcement(href: str, text: str) -> bool:
    low_href = href.lower()
    low_text = text.strip().lower()
    if low_text in _SKIP_TEXTS or len(low_text) < 8:
        return False
    for frag in _SKIP_HREF_FRAGMENTS:
        if frag in low_href:
            return False
    return True


def collect_html_list(fetcher: Fetcher, bank: Bank, url: str) -> CollectResult:
    try:
        res = fetcher.fetch(url)
    except AccessError as exc:
        return CollectResult(ok=False, error=exc.reason)

    items: list[Item] = []
    seen_urls: set[str] = set()
    for href, raw_title, context in extract_listed_links(res.text):
        published = parse_single_date(context)
        title = _strip_date(_RE_TRAILING_DATE, _strip_date(_RE_LEADING_DATE, raw_title)).strip()
        if not _looks_like_announcement(href, title):
            continue
        abs_url = urljoin(url, href)
        if abs_url in seen_urls:
            continue
        seen_urls.add(abs_url)
        items.append(
            Item(
                bank=bank.name,
                title=title,
                url=abs_url,
                published=published.isoformat() if published else None,
                source_type="portal",
                evidence=context,
            )
        )
    return CollectResult(items=items, ok=True)
