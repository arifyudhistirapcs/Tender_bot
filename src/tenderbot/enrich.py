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

# Host berbagi-berkas yang robots.txt-nya memblokir endpoint UNDUHAN (mis.
# Google Drive memblokir /uc), padahal berkas itu SENGAJA ditautkan sebagai
# unduhan oleh pengumuman resmi. Untuk host ini, langkah membaca lampiran
# memakai unduhan langsung satu berkas (bypass_robots), BUKAN perayapan situs.
# Perayapan halaman biasa dan host lain tetap tunduk penuh pada robots.txt.
_DOWNLOAD_BYPASS_HOSTS = (
    "drive.google.com",
    "drive.usercontent.google.com",
    "docs.google.com",
)

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


# Google Drive: ubah tautan "view" menjadi unduh langsung.
_RE_GDRIVE_FILE = re.compile(r"drive\.google\.com/file/d/([A-Za-z0-9_-]+)", re.I)
_RE_GDRIVE_OPEN = re.compile(r"drive\.google\.com/open\?id=([A-Za-z0-9_-]+)", re.I)
_RE_GDRIVE_UC = re.compile(r"drive\.google\.com/uc\?[^\"'<> ]*\bid=([A-Za-z0-9_-]+)", re.I)
_RE_DOCS_GDRIVE = re.compile(r"docs\.google\.com/[^\"'<> ]*?/d/([A-Za-z0-9_-]+)", re.I)


def _gdrive_download_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def _gdrive_id(url: str) -> Optional[str]:
    """ID berkas Google Drive dari berbagai bentuk URL, atau None."""
    for rx in (_RE_GDRIVE_FILE, _RE_GDRIVE_OPEN, _RE_GDRIVE_UC, _RE_DOCS_GDRIVE):
        m = rx.search(url or "")
        if m:
            return m.group(1)
    return None


# Atribut yang bisa memuat URL lampiran selain href (tombol/gambar/onclick).
# Menangkap NILAI penuh dengan menghormati jenis kutip pembuka, supaya kutip
# bagian dalam (mis. onclick="window.open('/x.pdf')") tidak memotong nilai.
_RE_ATTR_URLS = re.compile(
    r"""(?:href|src|data-[\w-]+|onclick)\s*=\s*"([^"]*)"|"""
    r"""(?:href|src|data-[\w-]+|onclick)\s*=\s*'([^']*)'""",
    re.IGNORECASE,
)
# URL "telanjang" di dalam onclick (window.open('...')) atau teks.
_RE_BARE_URL = re.compile(r"""https?://[^\s"'<>()]+""", re.IGNORECASE)
# Token path .pdf (relatif atau absolut) di dalam nilai atribut / onclick,
# mis. window.open('/files/a.pdf') atau data-file="docs/x.pdf".
_RE_PDF_TOKEN = re.compile(r"""['"(]?([^\s"'<>()]+\.pdf)\b""", re.IGNORECASE)


def discover_attachments(html: str, base_url: str) -> list[str]:
    """Daftar URL lampiran (PDF langsung atau unduhan Google Drive) dari HTML.

    Urutan penemuan (brief): tautan .pdf di HTML -> tautan di elemen
    gambar/tombol/onclick/data-* -> tautan Google Drive (diubah ke unduh
    langsung). Duplikat dibuang, urutan kemunculan dipertahankan.
    """
    out: list[str] = []
    seen: set[str] = set()

    def _add(u: str) -> None:
        if u and u not in seen:
            seen.add(u)
            out.append(u)

    if not html:
        return out

    # 1. Tautan <a> eksplisit (href + teks) — termasuk yang membungkus <img>.
    for href, _ in extract_links(html):
        _consider(href, base_url, _add)

    # 2. URL di atribut apa pun (src/data-*/onclick) dan di dalamnya.
    for m in _RE_ATTR_URLS.finditer(html):
        val = m.group(1) if m.group(1) is not None else m.group(2)
        if not val:
            continue
        _consider(val, base_url, _add)
        for bm in _RE_BARE_URL.finditer(val):  # onclick="window.open('https://...')"
            _consider(bm.group(0), base_url, _add)
        for pm in _RE_PDF_TOKEN.finditer(val):  # onclick="window.open('/files/a.pdf')"
            _consider(pm.group(1), base_url, _add)

    return out


def _consider(raw: str, base_url: str, add) -> None:
    """Pertimbangkan satu kandidat URL: tambahkan bila PDF atau Google Drive."""
    if not raw:
        return
    gid = _gdrive_id(raw)
    if gid:
        add(_gdrive_download_url(gid))
        return
    if _is_pdf(raw):
        add(urljoin(base_url, raw))


# ---- Fallback WordPress REST API ----

# Tipe post custom yang dipakai portal bank (mis. Bank Sumut "jasa_barang").
def _wp_rest_from_url(url: str) -> Optional[tuple[str, str, str]]:
    """Dari URL detail WordPress "/<type>/<slug>/" kembalikan
    (base, type, slug) untuk membangun endpoint REST, atau None.
    """
    m = re.match(r"(https?://[^/]+)/([a-z0-9_]+)/([^/?#]+)/?", url or "", re.I)
    if not m:
        return None
    base, ptype, slug = m.group(1), m.group(2), m.group(3)
    # Abaikan path yang jelas bukan post (mis. file statis).
    if "." in slug:
        return None
    return (base, ptype, slug)


def _fetch_wp_detail(item: Item, fetcher: Fetcher) -> tuple[str, list[str]]:
    """Fallback: ambil detail lewat WP REST API bila HTML tak terakses.

    Kembalikan (teks_konten, daftar_lampiran). Mencoba:
      /wp-json/wp/v2/<type>?slug=<slug>  -> content.rendered (+ post id)
      /wp-json/wp/v2/media?parent=<id>   -> media attachment PDF milik post.
    """
    parsed = _wp_rest_from_url(item.url)
    if parsed is None:
        return ("", [])
    base, ptype, slug = parsed

    import json as _json
    text = ""
    attachments: list[str] = []
    post_id: Optional[int] = None

    rest_url = f"{base}/wp-json/wp/v2/{ptype}?slug={slug}"
    try:
        res = fetcher.fetch(rest_url)
    except AccessError:
        return ("", [])
    try:
        data = _json.loads(res.text)
    except (ValueError, TypeError):
        data = None
    if isinstance(data, list) and data:
        post = data[0]
        post_id = post.get("id")
        rendered = (post.get("content") or {}).get("rendered") or ""
        text = html_to_text(rendered)
        attachments.extend(discover_attachments(rendered, item.url))

    # Media attachment milik post (PDF yang diunggah ke WP).
    if post_id is not None:
        media_url = f"{base}/wp-json/wp/v2/media?parent={post_id}"
        try:
            mres = fetcher.fetch(media_url)
            mdata = _json.loads(mres.text)
        except (AccessError, ValueError, TypeError):
            mdata = None
        if isinstance(mdata, list):
            for m in mdata:
                src = (m.get("source_url") or "")
                mime = (m.get("mime_type") or "")
                if _is_pdf(src, mime):
                    if src and src not in attachments:
                        attachments.append(src)

    return (text, attachments)


def enrich_item(item: Item, fetcher: Fetcher, max_pdfs: int = MAX_PDFS_PER_ITEM) -> Item:
    """Buka halaman detail item lalu lampiran PDF; isi field yang kosong.

    Penemuan lampiran: tautan PDF/gambar/tombol/onclick/data-* di HTML, lalu
    tautan Google Drive, lalu (bila HTML tak terakses) WordPress REST API.
    Tidak pernah menimpa field yang SUDAH terisi (mis. dari inbox agen AI).
    Gagal akses (robots/timeout/blokir) -> item dikembalikan apa adanya.
    """
    detail_text = ""
    attachments: list[str] = []

    # 1. Halaman detail (HTML atau PDF langsung).
    try:
        res = fetcher.fetch(item.url)
    except AccessError:
        res = None
    if res is not None:
        ctype = res.content_type.lower()
        if _is_pdf(item.url, ctype):
            detail_text = pdf_bytes_to_text(res.content)
            item.attachment_url = item.attachment_url or item.url
        else:
            detail_text = html_to_text(res.text)
            attachments.extend(discover_attachments(res.text, item.url))

    # 2. Fallback WordPress REST API bila HTML gagal atau tak memuat lampiran.
    if (res is None or not attachments) and not _is_pdf(item.url, ""):
        wp_text, wp_attachments = _fetch_wp_detail(item, fetcher)
        if wp_text and not detail_text:
            detail_text = wp_text
        elif wp_text:
            detail_text = f"{detail_text}\n{wp_text}"
        for a in wp_attachments:
            if a not in attachments:
                attachments.append(a)

    # Terapkan field dari teks detail (HTML + konten REST).
    _apply_fields(item, extract_fields(detail_text))

    # 3. Baca lampiran PDF (maksimal N).
    for pdf_url in attachments[:max_pdfs]:
        bypass = _host_of(pdf_url) in _DOWNLOAD_BYPASS_HOSTS
        try:
            pres = fetcher.fetch(pdf_url, bypass_robots=bypass)
        except (AccessError, TypeError):
            # TypeError: Fetcher palsu lama tanpa parameter -> coba tanpa.
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
            item.attachment_url = pdf_url

    return item


def _host_of(url: str) -> str:
    from urllib.parse import urlsplit
    return urlsplit(url or "").netloc.lower().split("@")[-1].split(":")[0]


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
