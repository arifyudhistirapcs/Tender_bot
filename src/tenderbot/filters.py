"""Saringan aturan: procurement AND edc AND NOT reject, dan batas usia 90 hari."""

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

    Teks yang diperiksa = judul + evidence (keduanya dinormalisasi).
    Urutan: reject dulu (buang), lalu usia, lalu wajib procurement + edc.
    """
    text = normalize_text(f"{item.title} {item.evidence}")

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

    hit_edc = _contains_any(text, keywords.edc)
    if not hit_edc:
        return FilterResult(False, "tidak ada kata EDC")

    return FilterResult(True, "")
