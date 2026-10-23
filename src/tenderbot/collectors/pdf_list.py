"""Kolektor daftar PDF: halaman yang menaut PDF pengumuman (pola Bank Jatim).

Mengambil semua tautan .pdf dari halaman, memakai teks tautan sebagai judul.
Isi PDF TIDAK diunduh di sini (hemat jaringan); pembacaan PDF adalah langkah
terpisah yang dipakai bila rincian diperlukan. Untuk saringan light, teks
tautan + nama file biasanya cukup memuat kata kunci.
"""

from __future__ import annotations

from urllib.parse import urljoin, unquote

from ..config import Bank
from ..http_client import AccessError, Fetcher
from ..models import Item
from .base import CollectResult, extract_links


def _filename_words(href: str) -> str:
    """Ubah nama file PDF jadi teks kata (pengumuman_website_pengadaan_... )."""
    tail = unquote(href.rsplit("/", 1)[-1])
    tail = tail.rsplit(".", 1)[0]
    return tail.replace("_", " ").replace("-", " ")


def collect_pdf_list(fetcher: Fetcher, bank: Bank, url: str) -> CollectResult:
    try:
        res = fetcher.fetch(url)
    except AccessError as exc:
        return CollectResult(ok=False, error=exc.reason)

    items: list[Item] = []
    seen_urls: set[str] = set()
    for href, text in extract_links(res.text):
        if ".pdf" not in href.lower():
            continue
        abs_url = urljoin(url, href)
        if abs_url in seen_urls:
            continue
        seen_urls.add(abs_url)
        # Judul = teks tautan; tambahan kata dari nama file untuk pencocokan.
        title = text.strip() or _filename_words(href)
        evidence = f"{text} {_filename_words(href)}".strip()
        items.append(
            Item(
                bank=bank.name,
                title=title,
                url=abs_url,
                source_type="portal",
                evidence=evidence[:500],
            )
        )
    return CollectResult(items=items, ok=True)
