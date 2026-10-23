"""Kolektor daftar HTML: ambil tautan pengumuman dari halaman arsip.

Dipakai untuk Bank Sumut (arsip jasa_barang) dan Bank Jatim (Lelang
Pengadaan). Strategi sengaja sederhana dan tahan-banting: ambil semua
<a>, buang yang jelas navigasi, jadikan teks tautan sebagai judul. Saringan
aturan (procurement + edc) yang akan menyisihkan tautan yang tidak relevan,
jadi kolektor tidak perlu menebak struktur tiap situs.
"""

from __future__ import annotations

from urllib.parse import urljoin

from ..config import Bank
from ..http_client import AccessError, Fetcher
from ..models import Item
from .base import CollectResult, extract_links

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
)


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
    for href, text in extract_links(res.text):
        if not _looks_like_announcement(href, text):
            continue
        abs_url = urljoin(url, href)
        if abs_url in seen_urls:
            continue
        seen_urls.add(abs_url)
        items.append(
            Item(
                bank=bank.name,
                title=text,
                url=abs_url,
                source_type="portal",
                evidence=text,
            )
        )
    return CollectResult(items=items, ok=True)
