"""Dedup: fingerprint persis + judul mirip dari bank sama dalam 60 hari."""

from __future__ import annotations

import difflib
import re
from datetime import date, timedelta
from typing import Iterable
from urllib.parse import urlsplit

from .enrich import _is_shared_list_url
from .models import Item, fingerprint, normalize_text, parse_iso_date, strip_title_date

NEAR_DUP_WINDOW_DAYS = 60
NEAR_DUP_RATIO = 0.90

_BRANCH_MARKER = re.compile(
    r"\b(?:kantor\s+cabang|kc|kcu|kcp|cabang|kanwil|wilayah)\s+([a-z0-9]+)",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\b\d+\b")
# Akhiran dalam kurung yang hanya berisi metode pengadaan, mis.
# "(Pelelangan Umum Pascakualifikasi)". "(Tender Ulang)" tidak dibuang.
_METHOD_SUFFIX = re.compile(
    r"\s*\(\s*(?:(?:pelelangan\s+umum|pascakualifikasi|prakualifikasi|seleksi\s+umum"
    r"|penunjukan\s+langsung|pemilihan\s+langsung)\s*)+\)\s*$",
    re.IGNORECASE,
)


# Halaman pengumuman bernomor (mis. /berita/pengumuman-lelang-33) memuat banyak
# item; heuristik enrich._is_shared_list_url tidak menangkapnya.
_NUMBERED_LIST_SLUG = re.compile(r"^(?:pengumuman|lelang)[a-z-]*-\d+$", re.IGNORECASE)


def _is_shared_url(url: str) -> bool:
    if _is_shared_list_url(url):
        return True
    last = [p for p in urlsplit(url).path.split("/") if p][-1:]
    return bool(last and _NUMBERED_LIST_SLUG.match(last[0]))


def _strip_method_suffix(title: str) -> str:
    return _METHOD_SUFFIX.sub("", title or "")


def is_same_url_duplicate(item: Item, seen_urls: Iterable[tuple[str, str]]) -> bool:
    """True bila bank dan url sama persis dengan entri seen.

    Halaman daftar bersama (banyak item satu url) dikecualikan.
    seen_urls: iterable (bank, url).
    """
    if not item.url or _is_shared_url(item.url):
        return False
    item_bank = normalize_text(item.bank)
    return any(
        url == item.url and normalize_text(bank) == item_bank for bank, url in seen_urls
    )


def _branch_words(title: str) -> set[str]:
    """Kata sesudah penanda cabang/wilayah pada judul ternormalisasi."""
    return {match.group(1).lower() for match in _BRANCH_MARKER.finditer(title)}


def _has_distinct_identity(left: str, right: str) -> bool:
    """Cabang atau nomor paket/tahun berbeda tidak boleh disatukan."""
    left_branches, right_branches = _branch_words(left), _branch_words(right)
    if left_branches and right_branches and left_branches != right_branches:
        return True
    return set(_NUMBER.findall(left)) != set(_NUMBER.findall(right))


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
    item_title = normalize_text(strip_title_date(_strip_method_suffix(item.title)))
    item_bank = normalize_text(item.bank)
    window = timedelta(days=NEAR_DUP_WINDOW_DAYS)

    for bank, title, seen_iso in seen_titles:
        if normalize_text(bank) != item_bank:
            continue
        seen_date = parse_iso_date(seen_iso) or item_date
        if abs((item_date - seen_date).days) > window.days:
            continue
        seen_title = normalize_text(strip_title_date(_strip_method_suffix(title)))
        ratio = difflib.SequenceMatcher(None, item_title, seen_title).ratio()
        if ratio >= NEAR_DUP_RATIO and not _has_distinct_identity(item_title, seen_title):
            return True
    return False
