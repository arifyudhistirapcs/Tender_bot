"""Klien HTTP: timeout keras, retry sekali, patuh robots.txt, deteksi blokir.

Semua akses jaringan bot lewat kelas Fetcher ini supaya aturan akses
(timeout, retry, User-Agent, robots.txt, deteksi halaman blokir) tertegakkan
di satu tempat dan bisa diganti (disuntik) dalam uji unit tanpa internet.
"""

from __future__ import annotations

import time
import urllib.robotparser
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlsplit

import requests

# User-Agent jujur: menyebut nama bot dan URL repo publiknya.
USER_AGENT = (
    "TenderBot/0.1 (+https://github.com/arifyudhistirapcs/Tender_bot) "
    "pemantau tender publik; hormati robots.txt"
)

TIMEOUT_SECONDS = 20
RETRIES = 1  # satu kali ulang (total dua percobaan)
RETRY_BACKOFF_SECONDS = 2

# Penanda halaman blokir yang dikenali (dicek case-insensitive di body).
BLOCK_MARKERS = (
    "request rejected",
    "request unsuccessful",  # Incapsula
    "please wait a while",
    "incapsula incident",
    "access denied",
    "_incapsula_resource",
)


class AccessError(Exception):
    """Gagal mengakses sumber, dengan alasan yang bisa dilaporkan."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass
class FetchResult:
    url: str
    status: int
    text: str
    content: bytes
    content_type: str


def detect_block(status: int, text: str) -> Optional[str]:
    """Kembalikan alasan blokir bila terdeteksi, atau None."""
    if status == 403:
        return "HTTP 403 (akses ditolak)"
    if status == 429:
        return "HTTP 429 (rate limited)"
    lowered = (text or "")[:4000].lower()
    for marker in BLOCK_MARKERS:
        if marker in lowered:
            return f'halaman blokir ("{marker}")'
    return None


class Fetcher:
    """Pengambil HTTP dengan kebijakan akses terpusat.

    Parameter respect_robots bisa dimatikan HANYA di uji unit.
    """

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        respect_robots: bool = True,
        timeout: int = TIMEOUT_SECONDS,
    ):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.respect_robots = respect_robots
        self.timeout = timeout
        self._robots_cache: dict[str, Optional[urllib.robotparser.RobotFileParser]] = {}

    # ---- robots.txt ----
    def _robots_for(self, url: str) -> Optional[urllib.robotparser.RobotFileParser]:
        parts = urlsplit(url)
        root = f"{parts.scheme}://{parts.netloc}"
        if root in self._robots_cache:
            return self._robots_cache[root]
        rp = urllib.robotparser.RobotFileParser()
        robots_url = f"{root}/robots.txt"
        try:
            resp = self.session.get(robots_url, timeout=self.timeout)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            else:
                # robots.txt tidak ada / 403 -> tidak ada larangan yang bisa dibaca.
                rp = None
        except requests.RequestException:
            rp = None
        self._robots_cache[root] = rp
        return rp

    def allowed_by_robots(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        rp = self._robots_for(url)
        if rp is None:
            return True
        return rp.can_fetch(USER_AGENT, url)

    # ---- fetch ----
    def fetch(self, url: str) -> FetchResult:
        """Ambil URL. Raise AccessError pada blokir, timeout, atau robots.

        Retry satu kali untuk kegagalan jaringan transien.
        """
        if not self.allowed_by_robots(url):
            raise AccessError("dilarang oleh robots.txt")

        last_exc: Optional[Exception] = None
        for attempt in range(RETRIES + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
            except requests.Timeout:
                last_exc = AccessError(f"timeout > {self.timeout}d")
            except requests.RequestException as exc:
                last_exc = AccessError(f"gagal koneksi: {type(exc).__name__}")
            else:
                block = detect_block(resp.status_code, resp.text)
                if block:
                    # Blokir bukan error transien: jangan retry, langsung gagal.
                    raise AccessError(block)
                if resp.status_code >= 400:
                    last_exc = AccessError(f"HTTP {resp.status_code}")
                else:
                    return FetchResult(
                        url=url,
                        status=resp.status_code,
                        text=resp.text,
                        content=resp.content,
                        content_type=resp.headers.get("Content-Type", ""),
                    )
            if attempt < RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS)
        assert last_exc is not None
        raise last_exc
