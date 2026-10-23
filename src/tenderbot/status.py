"""Hitung status tender dan kelayakan tampil di laporan.

Status (relatif terhadap hari ini WIB):
  - akan_dibuka : reg_open > hari ini
  - berjalan    : reg_open <= hari ini <= tutup terakhir
  - tutup       : tutup terakhir < hari ini
  - tidak_diketahui : tidak ada tanggal tutup

"tutup terakhir" = yang paling akhir di antara reg_close dan submit_close.

Aturan laporan (lihat brief enrich):
  - status "tutup" DIBUANG dari laporan tapi tetap ditandai seen;
  - status "tidak_diketahui" hanya dikirim bila tanggal posting (atau perkiraan
    dari pola URL lampiran /YYYY/<bulan>/) berada dalam 45 hari terakhir;
  - selain itu akan_dibuka dan berjalan selalu dikirim.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional

from .dates_id import _MONTHS
from .models import Item, parse_iso_date

STALE_UNKNOWN_DAYS = 45

STATUS_UPCOMING = "akan_dibuka"
STATUS_ONGOING = "berjalan"
STATUS_CLOSED = "tutup"
STATUS_UNKNOWN = "tidak_diketahui"


def _last_close(item: Item) -> Optional[date]:
    """Tanggal tutup terakhir: max(reg_close, submit_close, deadline)."""
    candidates = [
        parse_iso_date(item.reg_close),
        parse_iso_date(item.submit_close),
        parse_iso_date(item.deadline),
    ]
    dates = [d for d in candidates if d is not None]
    return max(dates) if dates else None


def compute_status(item: Item, today: date) -> str:
    """Kembalikan salah satu status dan tidak mengubah item."""
    reg_open = parse_iso_date(item.reg_open)
    last_close = _last_close(item)

    if last_close is None:
        # Tanpa tutup, tapi bila reg_open jelas di masa depan -> akan_dibuka.
        if reg_open is not None and reg_open > today:
            return STATUS_UPCOMING
        return STATUS_UNKNOWN

    if reg_open is not None and reg_open > today:
        return STATUS_UPCOMING
    if last_close < today:
        return STATUS_CLOSED
    return STATUS_ONGOING


# Perkiraan tanggal dari pola URL lampiran "/YYYY/<bulan>/" (mis. /2026/mei/).
_RE_URL_YM = re.compile(r"/((?:19|20)\d{2})/([a-zA-Z]+)/")


def estimate_date_from_url(url: str) -> Optional[date]:
    """Perkiraan tanggal (hari ke-1) dari pola "/YYYY/<bulan-indonesia>/".

    Contoh: ".../2026/mei/..." -> date(2026, 5, 1). Kembalikan None bila pola
    tidak ada atau nama bulan tak dikenal.
    """
    if not url:
        return None
    m = _RE_URL_YM.search(url)
    if not m:
        return None
    year = int(m.group(1))
    month = _MONTHS.get(m.group(2).lower())
    if not month:
        return None
    try:
        return date(year, month, 1)
    except ValueError:
        return None


def report_decision(item: Item, today: date) -> tuple[bool, str]:
    """(boleh_dikirim, alasan_bila_dibuang). Status harus sudah dihitung.

    - tutup -> dibuang ("sudah tutup").
    - tidak_diketahui -> hanya bila posting/perkiraan dalam 45 hari terakhir,
      selain itu dibuang ("tanggal tidak diketahui dan sudah lama").
    - akan_dibuka / berjalan -> selalu dikirim.
    """
    status = item.status or compute_status(item, today)

    if status == STATUS_CLOSED:
        return (False, "sudah tutup")

    if status == STATUS_UNKNOWN:
        ref = (
            parse_iso_date(item.posted)
            or parse_iso_date(item.published)
            or estimate_date_from_url(item.attachment_url or "")
            or estimate_date_from_url(item.url or "")
        )
        if ref is not None and (today - ref) <= timedelta(days=STALE_UNKNOWN_DAYS) \
                and (today - ref) >= timedelta(days=0):
            return (True, "")
        return (False, "tanggal tidak diketahui dan sudah lama")

    return (True, "")
