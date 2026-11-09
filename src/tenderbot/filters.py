"""Saringan aturan kategori: procurement, kategori, bukan reject, usia <=90 hari."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from .config import Keywords
from .models import Item, normalize_text, parse_iso_date

MAX_AGE_DAYS = 90


@dataclass
class FilterResult:
    passed: bool
    reason: str  # alasan ditolak (kosong bila lolos)


def _contains_any(haystack: str, needles: list[str]) -> Optional[str]:
    """Kembalikan kata pertama yang cocok, atau None."""
    for needle in needles:
        if normalize_text(needle) in haystack:
            return needle
    return None


def evaluate(item: Item, keywords: Keywords, today: date) -> FilterResult:
    """Terapkan aturan saringan ke satu item.

    Procurement dan reject diperiksa pada judul + evidence. Kategori EDC juga
    memakai keduanya, sedangkan kategori alih daya/data hanya memakai judul
    portal agar bukti kartu tetangga dan berita umum tidak ikut lolos.
    """
    text = normalize_text(f"{item.title} {item.evidence}")
    title = normalize_text(item.title)
    supplied_category = (
        item.category if item.category in {"edc", "alih_daya", "alih_data"} else None
    )
    item.category = None

    hit_reject = _contains_any(text, keywords.reject)
    if hit_reject:
        return FilterResult(False, f'kata buang "{hit_reject}"')

    published = parse_iso_date(item.published)
    if published is not None:
        age = today - published
        if age > timedelta(days=MAX_AGE_DAYS):
            return FilterResult(False, f"lebih tua dari {MAX_AGE_DAYS} hari ({item.published})")
        if age < timedelta(days=0):
            return FilterResult(False, f"tanggal terbit di masa depan ({item.published})")

    hit_proc = _contains_any(text, keywords.procurement)
    if not hit_proc:
        return FilterResult(False, "tidak ada kata pengadaan")

    # Prioritas kategori: EDC, lalu alih data, lalu alih daya. EDC tetap
    # melihat evidence seperti perilaku lama; dua kategori baru hanya portal
    # dan hanya judul agar berita umum outsourcing tidak ikut dilaporkan.
    # Kategori alih daya/data dari riset penuh hanya dipercaya bila item portal.
    # Di luar portal, nilai ulang dari judul/evidence dengan aturan biasa.
    if supplied_category == "edc" or (
        supplied_category in {"alih_daya", "alih_data"} and item.source_type == "portal"
    ):
        item.category = supplied_category
    elif _contains_any(text, keywords.edc):
        item.category = "edc"
    elif item.source_type == "portal" and _contains_any(title, keywords.alih_data):
        item.category = "alih_data"
    elif item.source_type == "portal" and _contains_any(title, keywords.alih_daya):
        item.category = "alih_daya"
    else:
        return FilterResult(False, "tidak ada kata EDC/alih daya/alih data")

    return FilterResult(True, "")
