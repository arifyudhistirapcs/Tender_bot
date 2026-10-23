"""Parser tanggal bahasa Indonesia dan nilai rupiah.

Semua fungsi mengembalikan None bila sumber tidak memuat nilai yang jelas.
JANGAN menebak: lebih baik None daripada angka salah (lihat brief enrich).

Format tanggal yang didukung:
  - "13 Oktober 2026"
  - "Selasa, 13 Oktober 2026"            (hari di depan diabaikan)
  - "13 Oktober 2026 s.d 23 Oktober 2026" (rentang -> (mulai, selesai))
  - "13/10/2026" dan "13-10-2026"

Format rupiah yang didukung:
  - "Rp6.993.000.000,-"
  - "6.993.000.000"
  - "Rp 6.993.000.000,00"
Titik = pemisah ribuan (gaya Indonesia); koma = desimal (dibuang untuk int).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

# Nama bulan Indonesia -> nomor. Termasuk ejaan lama "Nopember" dan singkatan.
_MONTHS = {
    "januari": 1, "jan": 1,
    "februari": 2, "pebruari": 2, "feb": 2,
    "maret": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mei": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "agustus": 8, "agust": 8, "agt": 8, "agu": 8,
    "september": 9, "sep": 9, "sept": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nopember": 11, "nov": 11, "nop": 11,
    "desember": 12, "des": 12,
}

# "13 Oktober 2026" (kata bulan). Hari-nama di depan ditangani oleh pemanggil
# karena regex ini hanya menangkap angka-bulan-tahun.
_MONTH_ALT = "|".join(re.escape(m) for m in _MONTHS)
_RE_NAMED = re.compile(
    rf"\b(\d{{1,2}})\s+({_MONTH_ALT})\.?\s+(\d{{4}})\b",
    re.IGNORECASE,
)
# "13/10/2026" atau "13-10-2026".
_RE_NUMERIC = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b")

# Pemisah rentang: "s.d", "s/d", "sampai dengan", "sampai", "hingga", "-", "–".
_RANGE_SPLIT = re.compile(
    r"\s*(?:s\.?/?d\.?|sampai\s+dengan|sampai|hingga|s\.d|–|—|\bs\b|/s)\s*",
    re.IGNORECASE,
)


def _mk_date(day: int, month: int, year: int) -> Optional[date]:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_single_date(text: str) -> Optional[date]:
    """Tanggal PERTAMA yang ditemukan di teks, atau None.

    Menangani "13 Oktober 2026", "Selasa, 13 Oktober 2026" (nama hari
    diabaikan), "13/10/2026", "13-10-2026".
    """
    if not text:
        return None
    m = _RE_NAMED.search(text)
    if m:
        day = int(m.group(1))
        month = _MONTHS.get(m.group(2).lower().rstrip("."))
        year = int(m.group(3))
        if month:
            return _mk_date(day, month, year)
    m = _RE_NUMERIC.search(text)
    if m:
        return _mk_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def parse_date_range(text: str) -> tuple[Optional[date], Optional[date]]:
    """Kembalikan (mulai, selesai).

    Bila teks memuat rentang "A s.d B" -> (A, B). Bila hanya satu tanggal
    -> (tanggal, None). Bila tidak ada -> (None, None).

    Untuk rentang bergaya "13 Oktober 2026 s.d 23 Oktober 2026" kedua sisi
    diparse terpisah. Bila sisi pertama tidak memuat tahun sendiri (jarang),
    keduanya tetap diparse apa adanya; tidak ada tebakan tahun.
    """
    if not text:
        return (None, None)
    # Cari semua tanggal dulu; bila ada >=2 dan ada penanda rentang, ambil
    # dua tanggal pertama sebagai (mulai, selesai).
    all_dates = _all_dates(text)
    has_range_marker = bool(_RANGE_SPLIT.search(text))
    if len(all_dates) >= 2 and has_range_marker:
        return (all_dates[0], all_dates[1])
    if all_dates:
        return (all_dates[0], None)
    return (None, None)


def _all_dates(text: str) -> list[date]:
    """Semua tanggal dalam urutan kemunculan (named lalu numeric per posisi)."""
    found: list[tuple[int, date]] = []
    for m in _RE_NAMED.finditer(text):
        month = _MONTHS.get(m.group(2).lower().rstrip("."))
        if month:
            d = _mk_date(int(m.group(1)), month, int(m.group(3)))
            if d:
                found.append((m.start(), d))
    for m in _RE_NUMERIC.finditer(text):
        d = _mk_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if d:
            found.append((m.start(), d))
    found.sort(key=lambda t: t[0])
    return [d for _, d in found]


# ---- Rupiah ----

_RE_RUPIAH = re.compile(
    r"""
    (?:rp\.?\s*)?            # prefiks "Rp" opsional
    (\d{1,3}(?:\.\d{3})+)    # angka dengan pemisah ribuan titik (>=1 kelompok)
    (?:,\d+)?                # desimal opsional (dibuang)
    (?:\s*,?-)?              # akhiran ",-" opsional
    """,
    re.IGNORECASE | re.VERBOSE,
)


def parse_rupiah(text: str) -> Optional[int]:
    """Nilai rupiah PERTAMA sebagai int, atau None.

    Menangani "Rp6.993.000.000,-", "6.993.000.000", "Rp 6.993.000.000,00".
    Hanya menerima angka dengan pemisah ribuan titik (minimal satu kelompok
    ".000") supaya tidak salah menangkap nomor dokumen atau tahun.
    """
    if not text:
        return None
    m = _RE_RUPIAH.search(text)
    if not m:
        return None
    digits = m.group(1).replace(".", "")
    try:
        return int(digits)
    except ValueError:
        return None


def format_rupiah(value: Optional[int]) -> Optional[str]:
    """Format "Rp6.993.000.000" (tanpa desimal). None -> None."""
    if value is None:
        return None
    return "Rp" + f"{value:,}".replace(",", ".")
