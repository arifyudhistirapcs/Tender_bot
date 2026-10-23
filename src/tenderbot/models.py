"""Model data dan normalisasi teks."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


@dataclass
class Item:
    """Satu kandidat tender."""

    bank: str
    title: str
    url: str
    published: Optional[str] = None  # ISO date "YYYY-MM-DD" bila diketahui
    deadline: Optional[str] = None
    value_idr: Optional[int] = None
    source_type: str = "portal"  # portal | berita | rilis
    evidence: str = ""
    media_name: str = ""  # nama media untuk item berita (host atau nama sumber)
    media_url: str = ""  # URL penerbit (dari Google News <source url>), untuk kredibilitas
    unverified_source: bool = False  # True bila media di luar daftar kredibel
    fingerprint: str = field(default="", compare=False)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        allowed = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in allowed})


_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)


def normalize_text(text: str) -> str:
    """Normalisasi untuk pencocokan kata kunci dan fingerprint judul.

    Lowercase, buang aksen, buang tanda baca, rapatkan spasi.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def canonical_url(url: str) -> str:
    """URL kanonik: skema+host lowercase, buang fragment, buang query pelacak.

    Query pelacak umum (utm_*, fbclid, gclid) dibuang supaya URL yang sama
    dengan jejak kampanye berbeda tidak dianggap item berbeda.
    """
    if not url:
        return ""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not (k.lower().startswith("utm_") or k.lower() in {"fbclid", "gclid"})
    ]
    query = urlencode(sorted(query_pairs))
    return urlunsplit((scheme, netloc, path, query, ""))


def fingerprint(bank: str, title: str, url: str) -> str:
    """sha256(bank + judul dinormalisasi + url kanonik)."""
    basis = f"{normalize_text(bank)}|{normalize_text(title)}|{canonical_url(url)}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    """Parse "YYYY-MM-DD" longgar; kembalikan None bila gagal."""
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


def host_of(url: str) -> str:
    """Host URL dalam huruf kecil tanpa port (kosong bila tak ada)."""
    netloc = urlsplit(url or "").netloc.lower()
    return netloc.split("@")[-1].split(":")[0]


def is_credible_domain(url: str, credible_domains: list[str]) -> bool:
    """True bila host URL sama dengan, atau subdomain dari, salah satu domain.

    "www.kompas.com" cocok dengan "kompas.com"; "evilkompas.com" TIDAK.
    """
    host = host_of(url)
    if not host:
        return False
    for dom in credible_domains:
        dom = dom.lower().strip()
        if host == dom or host.endswith("." + dom):
            return True
    return False
