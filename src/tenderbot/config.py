"""Pemuat konfigurasi: banks.yaml, keywords.yaml, holidays.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

# data/ relatif ke akar repo (dua tingkat di atas src/tenderbot/config.py).
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"


@dataclass
class Source:
    url: str
    type: str  # rss | html | pdf_list
    needs_js: bool = False  # situs dirender JavaScript; kolektor light melewati


@dataclass
class Bank:
    name: str
    aliases: list[str] = field(default_factory=list)
    group: str = ""  # bumn | swasta | bpd
    access: str = "not_found"  # public | vendor_login | not_found | blocked
    sources: list[Source] = field(default_factory=list)
    notes: str = ""
    needs_js: bool = False  # portal utama bank dirender JavaScript (butuh browser)
    vendor_registration_url: str = ""  # diisi agen riset lain nanti; boleh kosong

    @property
    def news_terms(self) -> list[str]:
        """Nama untuk kueri berita; fallback ke name bila aliases kosong."""
        return self.aliases or [self.name]


@dataclass
class Keywords:
    procurement: list[str]
    edc: list[str]
    reject: list[str]
    credible_news_domains: list[str] = field(default_factory=list)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} bukan dokumen YAML map")
    return data


def load_banks(path: Optional[Path] = None) -> list[Bank]:
    path = path or (DATA_DIR / "banks.yaml")
    data = _load_yaml(path)
    banks: list[Bank] = []
    for raw in data.get("banks", []):
        sources = [
            Source(
                url=s["url"],
                type=s["type"],
                needs_js=bool(s.get("needs_js", False)),
            )
            for s in (raw.get("sources") or [])
        ]
        banks.append(
            Bank(
                name=raw["name"],
                aliases=list(raw.get("aliases") or []),
                group=raw.get("group", ""),
                access=raw.get("access", "not_found"),
                sources=sources,
                notes=raw.get("notes", "") or "",
                needs_js=bool(raw.get("needs_js", False)),
                vendor_registration_url=raw.get("vendor_registration_url", "") or "",
            )
        )
    if not banks:
        raise ValueError(f"{path} tidak memuat bank")
    return banks


def load_keywords(path: Optional[Path] = None) -> Keywords:
    path = path or (DATA_DIR / "keywords.yaml")
    data = _load_yaml(path)
    kw = Keywords(
        procurement=list(data.get("procurement") or []),
        edc=list(data.get("edc") or []),
        reject=list(data.get("reject") or []),
        credible_news_domains=list(data.get("credible_news_domains") or []),
    )
    if not kw.procurement or not kw.edc:
        raise ValueError(f"{path} harus memuat kata procurement dan edc")
    return kw


def load_holidays(path: Optional[Path] = None) -> set[str]:
    """Kembalikan set tanggal libur ISO "YYYY-MM-DD"."""
    path = path or (DATA_DIR / "holidays.yaml")
    data = _load_yaml(path)
    return {str(h["date"]) for h in (data.get("holidays") or []) if h.get("date")}
