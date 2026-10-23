"""Dedup: fingerprint persis + judul mirip dari bank sama dalam 60 hari."""

from __future__ import annotations

import difflib
from datetime import date, timedelta
from typing import Iterable

from .models import Item, fingerprint, normalize_text, parse_iso_date

NEAR_DUP_WINDOW_DAYS = 60
NEAR_DUP_RATIO = 0.90


def ensure_fingerprint(item: Item) -> str:
    if not item.fingerprint:
        item.fingerprint = fingerprint(item.bank, item.title, item.url)
    return item.fingerprint


def is_near_duplicate(
    item: Item,
    seen_titles: Iterable[tuple[str, str, str]],
    today: date,
) -> bool:
    """True bila ada judul mirip dari bank sama dalam jendela 60 hari.

    seen_titles: iterable (bank, judul_ternormalisasi, tanggal_iso).
    Tanggal acuan item memakai published bila ada, selain itu today.
    """
    item_date = parse_iso_date(item.published) or today
    item_title = normalize_text(item.title)
    item_bank = normalize_text(item.bank)
    window = timedelta(days=NEAR_DUP_WINDOW_DAYS)

    for bank, title, seen_iso in seen_titles:
        if normalize_text(bank) != item_bank:
            continue
        seen_date = parse_iso_date(seen_iso) or item_date
        if abs((item_date - seen_date).days) > window.days:
            continue
        ratio = difflib.SequenceMatcher(None, item_title, title).ratio()
        if ratio >= NEAR_DUP_RATIO:
            return True
    return False
