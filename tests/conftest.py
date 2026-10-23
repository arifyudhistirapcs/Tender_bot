"""Alat bantu uji: Fetcher palsu yang melayani fixture lokal tanpa internet."""

from __future__ import annotations

from pathlib import Path

from tenderbot.http_client import AccessError, FetchResult, detect_block

FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeFetcher:
    """Meniru antarmuka Fetcher.fetch(url) dari peta url -> (status, teks).

    Mendeteksi blokir memakai logika produksi yang sama (detect_block),
    jadi fixture halaman blokir menghasilkan AccessError seperti di produksi.
    DILARANG menyentuh jaringan.
    """

    def __init__(self, routes: dict[str, tuple[int, str]]):
        # routes: url -> (status_code, body_text)
        self.routes = routes
        self.calls: list[str] = []

    def fetch(self, url: str) -> FetchResult:
        self.calls.append(url)
        if url not in self.routes:
            raise AccessError("gagal koneksi: tidak ada rute fixture")
        status, text = self.routes[url]
        block = detect_block(status, text)
        if block:
            raise AccessError(block)
        if status >= 400:
            raise AccessError(f"HTTP {status}")
        return FetchResult(
            url=url, status=status, text=text,
            content=text.encode("utf-8"), content_type="text/html",
        )

    def allowed_by_robots(self, url: str) -> bool:
        return True
