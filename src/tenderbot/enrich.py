"""Pengayaan detail: buka halaman detail item, baca lampiran PDF yang ditaut,
ekstrak field opsional ke Item.

Batas (brief enrich):
  - maksimal 3 PDF per item;
  - timeout 20 detik per permintaan (ditegakkan di Fetcher);
  - patuhi robots.txt (ditegakkan di Fetcher);
  - PDF teks dibaca dengan PyMuPDF versi pasti (pymupdf==1.24.14).

Ekstraksi field memakai pencocokan label bahasa Indonesia pada teks (halaman
detail + teks PDF). Bila label tidak ada, field dibiarkan None. JANGAN menebak.
"""

from __future__ import annotations

import io
import re
from typing import Optional
from urllib.parse import urljoin

from .collectors.base import extract_links, html_to_text
from .dates_id import parse_date_range, parse_rupiah, parse_single_date
from .http_client import AccessError, Fetcher
from .models import Item

MAX_PDFS_PER_ITEM = 3

try:  # PyMuPDF
    import fitz  # type: ignore
    _HAVE_FITZ = True
except Exception:  # pragma: no cover - lingkungan tanpa PyMuPDF
    _HAVE_FITZ = False


def pdf_bytes_to_text(data: bytes) -> str:
    """Ekstrak teks dari byte PDF memakai PyMuPDF. '' bila gagal/kosong."""
    if not _HAVE_FITZ or not data:
        return ""
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        return ""
    try:
        parts = [doc[i].get_text() for i in range(doc.page_count)]
    except Exception:
        parts = []
    finally:
        doc.close()
    return "\n".join(parts)


# ---- Ekstraksi field dari teks ----

def _norm_ws(text: str) -> str:
    return re.sub(r"[ \t]+", " ", (text or "").replace("\r", " "))


def _flat(text: str) -> str:
    """Satukan newline jadi spasi (untuk pencocokan label lintas-baris)."""
    return re.sub(r"\s+", " ", text or "").strip()


def extract_fields(text: str) -> dict:
    """Ekstrak field opsional dari teks pengumuman (PDF atau halaman detail).

    Mengembalikan dict field yang DITEMUKAN saja (tanpa None), supaya pemanggil
    bisa menerapkan "isi hanya bila belum ada" tanpa menimpa dengan None.
    """
    out: dict = {}
    if not text:
        return out
    flat = _flat(text)

    # Nilai HPS/pagu/nilai: cari di sekitar kata HPS / Harga Perkiraan Sendiri /
    # pagu / nilai; bila tak ketemu, ambil rupiah pertama yang bergaya ribuan.
    value = _extract_value(flat)
    if value is not None:
        out["value_idr"] = value

    # Volume: "500 (lima ratus) Unit" atau "500 unit".
    volume = _extract_volume(flat)
    if volume:
        out["volume"] = volume

    # Durasi: "36 (tiga puluh enam) Bulan" atau "36 bulan".
    duration = _extract_duration(flat)
    if duration:
        out["duration"] = duration

    # Metode: "Pelelangan Umum dengan Sistem Pascakualifikasi".
    method = _extract_method(flat)
    if method:
        out["method"] = method

    # Pendaftaran / pengambilan dokumen: rentang tanggal.
    reg_open, reg_close = _extract_reg_dates(flat)
    if reg_open:
        out["reg_open"] = reg_open
    if reg_close:
        out["reg_close"] = reg_close

    # Batas pemasukan penawaran.
    submit_close = _extract_submit_close(flat)
    if submit_close:
        out["submit_close"] = submit_close

    # Tempat daftar.
    place = _extract_place(flat)
    if place:
        out["reg_place"] = place

    # Kontak.
    contact = _extract_contact(flat)
    if contact:
        out["contact"] = contact

    # Tanggal posting: "Medan, 13 Oktober 2026" (kota + tanggal di akhir) atau
    # label "tanggal pengumuman".
    posted = _extract_posted(flat)
    if posted:
        out["posted"] = posted

    return out


def _extract_value(flat: str) -> Optional[int]:
    # Prioritaskan konteks HPS/pagu/nilai.
    for label in (
        r"harga perkiraan sendiri[^0-9]*\(?hps\)?",
        r"\bhps\b",
        r"\bpagu\b",
        r"nilai paket",
        r"nilai hps",
        r"\bnilai\b",
    ):
        m = re.search(label, flat, re.IGNORECASE)
        if m:
            window = flat[m.end(): m.end() + 120]
            val = parse_rupiah(window)
            if val is not None:
                return val
    # Fallback: rupiah bergaya ribuan di seluruh teks.
    return parse_rupiah(flat)


_RE_VOLUME = re.compile(
    r"(\d[\d.]*)\s*(?:\([^)]*\)\s*)?(unit|mesin|buah|pcs|terminal)\b",
    re.IGNORECASE,
)


def _extract_volume(flat: str) -> Optional[str]:
    m = _RE_VOLUME.search(flat)
    if not m:
        return None
    num = m.group(1).replace(".", "")
    return f"{num} {m.group(2).lower()}"


_RE_DURATION = re.compile(
    r"(\d[\d.]*)\s*(?:\([^)]*\)\s*)?(bulan|tahun|hari|minggu)\b",
    re.IGNORECASE,
)


def _extract_duration(flat: str) -> Optional[str]:
    m = _RE_DURATION.search(flat)
    if not m:
        return None
    num = m.group(1).replace(".", "")
    return f"{num} {m.group(2).lower()}"


_RE_METHOD = re.compile(
    r"(pelelangan\s+umum|pelelangan\s+terbatas|seleksi\s+umum|seleksi\s+sederhana|"
    r"penunjukan\s+langsung|pengadaan\s+langsung|tender\s+terbatas|"
    r"tender\s+cepat)"
    r"(?:\s+(?:dengan\s+sistem\s+)?(?:pra|pasca)kualifikasi)?",
    re.IGNORECASE,
)


def _extract_method(flat: str) -> Optional[str]:
    m = _RE_METHOD.search(flat)
    if not m:
        return None
    phrase = _norm_ws(m.group(0)).strip()
    # Rapikan "dengan Sistem Pascakualifikasi" -> judul ringkas.
    phrase = re.sub(r"\s+dengan\s+sistem\s+", " ", phrase, flags=re.IGNORECASE)
    return " ".join(w.capitalize() if w.islower() else w for w in phrase.split())


def _extract_reg_dates(flat: str) -> tuple[Optional[str], Optional[str]]:
    """Cari rentang tanggal di konteks pendaftaran/pengambilan dokumen."""
    m = re.search(
        r"(pendaftaran|pengambilan\s+dokumen)",
        flat,
        re.IGNORECASE,
    )
    if not m:
        return (None, None)
    window = flat[m.start(): m.start() + 220]
    start, end = parse_date_range(window)
    s = start.isoformat() if start else None
    e = end.isoformat() if end else None
    return (s, e)


def _extract_submit_close(flat: str) -> Optional[str]:
    for label in (
        r"pemasukan\s+(?:dokumen\s+)?penawaran",
        r"batas\s+(?:akhir\s+)?penawaran",
        r"pemasukan\s+dokumen",
    ):
        m = re.search(label, flat, re.IGNORECASE)
        if m:
            window = flat[m.end(): m.end() + 160]
            start, end = parse_date_range(window)
            picked = end or start
            if picked:
                return picked.isoformat()
    return None


def _extract_place(flat: str) -> Optional[str]:
    m = re.search(r"\btempat\b\s*:?\s*", flat, re.IGNORECASE)
    if not m:
        return None
    tail = flat[m.end(): m.end() + 200]
    # Potong di label berikutnya yang umum (case-insensitive) ATAU penanda
    # bagian Romawi huruf besar "IV."/"V." (case-sensitive, supaya tidak
    # keliru memotong kata kecil yang kebetulan mirip angka Romawi).
    tail = re.split(
        r"\s+(?i:waktu|hari\s*/?\s*tanggal|rapat|syarat|untuk\s+informasi)\b"
        r"|\s+[IVX]{1,4}\.(?=\s)",
        tail,
        maxsplit=1,
    )[0]
    tail = tail.strip(" :.-")
    return tail[:160] or None


_RE_CONTACT = re.compile(
    r"\b(telp|telepon|hp|whatsapp|email|e-mail)\b\.?\s*[:.]?\s*"
    r"([0-9+][0-9()\-.,\sextX]{5,60}|[^\s@]+@[^\s]+)",
    re.IGNORECASE,
)


def _extract_contact(flat: str) -> Optional[str]:
    m = _RE_CONTACT.search(flat)
    if not m:
        return None
    label = m.group(1)
    value = _norm_ws(m.group(2)).strip(" .,-")
    if not value:
        return None
    return _norm_ws(f"{label}. {value}")[:120]


def _extract_posted(flat: str) -> Optional[str]:
    # "tanggal pengumuman: 13 Oktober 2026"
    m = re.search(r"tanggal\s+pengumuman\s*:?\s*([^\n]{6,40})", flat, re.IGNORECASE)
    if m:
        d = parse_single_date(m.group(1))
        if d:
            return d.isoformat()
    # Kota + tanggal di dekat akhir: "Medan, 13 Oktober 2026".
    m = re.search(
        r"\b[A-Z][a-z]+,\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b",
        flat,
    )
    if m:
        d = parse_single_date(m.group(1))
        if d:
            return d.isoformat()
    return None


# ---- Alur pengayaan satu item ----

def _is_pdf(href: str, content_type: str = "") -> bool:
    return ".pdf" in href.lower() or "application/pdf" in content_type.lower()


def enrich_item(item: Item, fetcher: Fetcher, max_pdfs: int = MAX_PDFS_PER_ITEM) -> Item:
    """Buka halaman detail item lalu lampiran PDF; isi field yang kosong.

    Tidak pernah menimpa field yang SUDAH terisi (mis. dari inbox agen AI).
    Gagal akses (robots/timeout/blokir) -> item dikembalikan apa adanya.
    """
    detail_text = ""
    pdf_links: list[str] = []

    # 1. Halaman detail.
    try:
        res = fetcher.fetch(item.url)
    except AccessError:
        res = None
    if res is not None:
        ctype = res.content_type.lower()
        if _is_pdf(item.url, ctype):
            # URL item sendiri adalah PDF.
            detail_text = pdf_bytes_to_text(res.content)
            item.attachment_url = item.attachment_url or item.url
        else:
            detail_text = html_to_text(res.text)
            for href, _ in extract_links(res.text):
                if _is_pdf(href):
                    pdf_links.append(urljoin(item.url, href))

    # Terapkan field dari halaman detail.
    _apply_fields(item, extract_fields(detail_text))

    # 2. Lampiran PDF (maksimal N).
    for pdf_url in pdf_links[:max_pdfs]:
        try:
            pres = fetcher.fetch(pdf_url)
        except AccessError:
            continue
        ptext = pdf_bytes_to_text(pres.content)
        if not ptext:
            continue
        before = _snapshot(item)
        _apply_fields(item, extract_fields(ptext))
        if item.attachment_url is None and _snapshot(item) != before:
            item.attachment_url = pdf_url
        elif item.attachment_url is None:
            # Simpan lampiran pertama yang terbaca walau tak menambah field,
            # supaya tombol "Lampiran" tetap ada dan perkiraan tanggal URL jalan.
            item.attachment_url = pdf_url

    return item


_ENRICH_FIELDS = (
    "value_idr", "volume", "duration", "method", "reg_open", "reg_close",
    "submit_close", "reg_place", "contact", "posted",
)


def _apply_fields(item: Item, fields: dict) -> None:
    """Isi hanya field yang masih None pada item. JANGAN menimpa."""
    for key in _ENRICH_FIELDS:
        if key in fields and getattr(item, key) is None:
            setattr(item, key, fields[key])


def _snapshot(item: Item) -> tuple:
    return tuple(getattr(item, f) for f in _ENRICH_FIELDS)
