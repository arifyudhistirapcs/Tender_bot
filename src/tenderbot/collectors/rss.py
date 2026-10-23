"""Kolektor berita.

Dua sumber berita, keduanya satu kali ambil per sumber per run (BUKAN per bank):

1. Feed RSS resmi media kredibel (data/news_feeds.yaml). Tiap feed diambil
   sekali, lalu item disaring dengan (nama/alias bank) + (kata EDC).
2. GDELT DOC 2.0 API. Kueri digabung per kelompok bank supaya jumlah request
   kecil; antar-request dijeda agar patuh batas laju GDELT.

Google News RSS TIDAK dipakai (robots.txt news.google.com melarang
/rss/search). Lihat DESIGN.md dan data/news_feeds.yaml.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Callable, Optional
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

from ..config import Bank, NewsFeed
from ..http_client import AccessError, Fetcher
from ..models import Item, host_of, is_credible_domain, normalize_text
from .base import CollectResult

# ---- GDELT DOC 2.0 ----
# Dokumentasi: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
# Batas laju (diumumkan GDELT): API dibatasi untuk melindungi klaster; pesan
# penegakan nyata berbunyi "Please limit requests to one every 5 seconds".
# Karena itu kolektor menjeda >=5 detik antar-kueri dan menggabungkan kueri
# per kelompok bank agar jumlah request kecil.
GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_MIN_INTERVAL_SECONDS = 5.0
GDELT_MAX_RECORDS = 75  # <= 250 (batas API); dibuat kecil karena per-kelompok
GDELT_TIMESPAN = "7d"   # jendela 7 hari pada mode light
GDELT_BANKS_PER_QUERY = 8  # berapa bank digabung per satu request (OR)


def _text(elem: Optional[ET.Element]) -> str:
    return (elem.text or "").strip() if elem is not None else ""


def _parse_rss_date(raw: str) -> Optional[str]:
    """Parse tanggal RSS (RFC 822) -> "YYYY-MM-DD", atau None."""
    raw = (raw or "").strip()
    if not raw:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw[:19]).strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_rss(xml_text: str, source_type: str) -> list[dict]:
    """Ubah XML RSS/Atom menjadi daftar dict mentah {title,link,desc,pub}.

    Bank belum ditentukan di sini; feed media tidak per-bank, jadi penautan
    ke bank dilakukan oleh penyaring di collect_media_feeds.
    """
    out: list[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out

    for node in root.iter("item"):
        title = _text(node.find("title"))
        link = _text(node.find("link"))
        desc = _text(node.find("description"))
        pub = _parse_rss_date(_text(node.find("pubDate")))
        if title and link:
            out.append({"title": title, "link": link, "desc": desc, "pub": pub})

    atom_ns = "{http://www.w3.org/2005/Atom}"
    for node in root.iter(f"{atom_ns}entry"):
        title = _text(node.find(f"{atom_ns}title"))
        link_el = node.find(f"{atom_ns}link")
        link = link_el.get("href", "") if link_el is not None else ""
        summary = _text(node.find(f"{atom_ns}summary"))
        pub = _parse_rss_date(_text(node.find(f"{atom_ns}updated")))
        if title and link:
            out.append({"title": title, "link": link, "desc": summary, "pub": pub})
    return out


def collect_rss(fetcher: Fetcher, bank: Bank, url: str) -> CollectResult:
    """Ambil satu feed RSS sumber `public` milik satu bank (dipakai pipeline)."""
    try:
        res = fetcher.fetch(url)
    except AccessError as exc:
        return CollectResult(ok=False, error=exc.reason)
    items: list[Item] = []
    for raw in parse_rss(res.text, source_type="portal"):
        items.append(
            Item(
                bank=bank.name,
                title=raw["title"],
                url=raw["link"],
                published=raw["pub"],
                source_type="portal",
                evidence=raw["desc"][:500],
            )
        )
    return CollectResult(items=items, ok=True)


# ---- Feed media kredibel ----

def _bank_matches(text_norm: str, bank: Bank) -> bool:
    """True bila teks (sudah dinormalisasi) memuat salah satu nama/alias bank."""
    for term in bank.news_terms:
        t = normalize_text(term)
        if t and t in text_norm:
            return True
    return False


def _has_edc_term(text_norm: str, edc_terms: list[str]) -> bool:
    for term in edc_terms:
        t = normalize_text(term)
        if t and t in text_norm:
            return True
    return False


def collect_media_feeds(
    fetcher: Fetcher,
    feeds: list[NewsFeed],
    banks: list[Bank],
    edc_terms: list[str],
    credible_domains: list[str],
) -> tuple[list[Item], dict[str, bool], list[tuple[str, str]]]:
    """Ambil tiap feed SEKALI, saring per (bank + kata EDC).

    Return:
      items          -- Item berita yang cocok (dengan media_name + unverified_source),
      feed_ok        -- peta url_feed -> berhasil diambil?,
      failures       -- daftar (nama_feed, alasan) untuk feed yang gagal.

    Satu feed diambil sekali; menambah bank tidak menambah request.
    """
    items: list[Item] = []
    feed_ok: dict[str, bool] = {}
    failures: list[tuple[str, str]] = []

    for feed in feeds:
        try:
            res = fetcher.fetch(feed.url)
        except AccessError as exc:
            feed_ok[feed.url] = False
            failures.append((feed.name, exc.reason))
            continue
        feed_ok[feed.url] = True
        raws = parse_rss(res.text, source_type="berita")
        for raw in raws:
            text_norm = normalize_text(f"{raw['title']} {raw['desc']}")
            if not _has_edc_term(text_norm, edc_terms):
                continue
            for bank in banks:
                if not _bank_matches(text_norm, bank):
                    continue
                url = raw["link"]
                media_name = feed.domain or host_of(url) or "sumber tidak dikenal"
                items.append(
                    Item(
                        bank=bank.name,
                        title=raw["title"],
                        url=url,
                        published=raw["pub"],
                        source_type="berita",
                        evidence=raw["desc"][:500],
                        media_name=media_name,
                        unverified_source=not is_credible_domain(url, credible_domains),
                    )
                )
    return items, feed_ok, failures


# ---- GDELT DOC 2.0 ----

def build_gdelt_query(banks: list[Bank], edc_terms: list[str]) -> str:
    """Bangun kueri GDELT: (alias1 OR alias2 ...) "EDC" sourcecountry:ID.

    GDELT: tanda kurung HANYA untuk pernyataan OR. Jadi semua nama/alias bank
    dalam kelompok ini dirangkai OR dalam satu kurung, lalu di-AND dengan kata
    "EDC" dan pembatas negara Indonesia.
    """
    names: list[str] = []
    for bank in banks:
        for term in bank.news_terms:
            term = term.strip()
            if term and term not in names:
                names.append(f'"{term}"')
    or_group = " OR ".join(names)
    # Kata EDC telanjang dipakai sebagai AND-term; penyaringan ketat (procurement
    # + istilah EDC spesifik) tetap dilakukan oleh filters.evaluate setelahnya.
    return f"({or_group}) EDC sourcecountry:ID"


def parse_gdelt(json_text: str, credible_domains: list[str]) -> list[Item]:
    """Ubah JSON artlist GDELT menjadi daftar Item berita.

    Skema artlist (dari dokumentasi GDELT): articles[] dengan url, title,
    seendate (YYYYMMDDTHHMMSSZ), domain, language, sourcecountry.
    Item dari domain di luar daftar kredibel diberi label unverified_source.
    """
    items: list[Item] = []
    try:
        data = json.loads(json_text)
    except (json.JSONDecodeError, ValueError):
        return items
    for art in data.get("articles", []) or []:
        url = (art.get("url") or "").strip()
        title = (art.get("title") or "").strip()
        if not url or not title:
            continue
        published = _parse_gdelt_date(art.get("seendate", ""))
        domain = (art.get("domain") or host_of(url)).strip()
        items.append(
            Item(
                bank="",  # ditautkan ke bank oleh pemanggil (map_gdelt_to_banks)
                title=title,
                url=url,
                published=published,
                source_type="berita",
                evidence="",
                media_name=domain or "sumber tidak dikenal",
                unverified_source=not is_credible_domain(url, credible_domains),
            )
        )
    return items


def _parse_gdelt_date(raw: str) -> Optional[str]:
    """GDELT seendate "YYYYMMDDTHHMMSSZ" -> "YYYY-MM-DD", atau None."""
    raw = (raw or "").strip()
    if len(raw) >= 8 and raw[:8].isdigit():
        try:
            return datetime.strptime(raw[:8], "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            return None
    return None


def _chunks(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def collect_gdelt(
    fetcher: Fetcher,
    banks: list[Bank],
    edc_terms: list[str],
    credible_domains: list[str],
    sleep: Callable[[float], None] = time.sleep,
    min_interval: float = GDELT_MIN_INTERVAL_SECONDS,
    banks_per_query: int = GDELT_BANKS_PER_QUERY,
) -> tuple[list[Item], bool, Optional[str]]:
    """Kueri GDELT per kelompok bank (jumlah request kecil, dijeda >=5 detik).

    Return (items_tanpa_bank, ok, error). Penautan item->bank dilakukan oleh
    map_gdelt_to_banks. `sleep` dapat disuntik di uji supaya tidak menunggu.
    """
    all_items: list[Item] = []
    ok_any = False
    last_error: Optional[str] = None
    groups = list(_chunks(banks, max(1, banks_per_query)))

    for idx, group in enumerate(groups):
        if idx > 0:
            sleep(min_interval)  # hormati batas laju antar-request
        query = build_gdelt_query(group, edc_terms)
        url = (
            f"{GDELT_DOC_URL}?query={quote_plus(query)}"
            f"&mode=artlist&format=json&timespan={GDELT_TIMESPAN}"
            f"&maxrecords={GDELT_MAX_RECORDS}"
        )
        try:
            res = fetcher.fetch(url)
        except AccessError as exc:
            last_error = exc.reason
            continue
        ok_any = True
        all_items.extend(parse_gdelt(res.text, credible_domains))

    return all_items, ok_any, (None if ok_any else (last_error or "gagal"))


def map_gdelt_to_banks(
    gdelt_items: list[Item], banks: list[Bank]
) -> tuple[list[Item], set[str]]:
    """Tautkan item GDELT ke bank berdasar nama/alias di judul.

    Satu artikel bisa menyebut >1 bank -> disalin per bank. Artikel yang tidak
    menyebut bank mana pun dibuang. Return (items_bertautan, set_nama_bank).
    """
    linked: list[Item] = []
    covered: set[str] = set()
    for item in gdelt_items:
        title_norm = normalize_text(item.title)
        for bank in banks:
            if _bank_matches(title_norm, bank):
                clone = Item(
                    bank=bank.name,
                    title=item.title,
                    url=item.url,
                    published=item.published,
                    source_type="berita",
                    evidence=item.evidence,
                    media_name=item.media_name,
                    unverified_source=item.unverified_source,
                )
                linked.append(clone)
                covered.add(bank.name)
    return linked, covered
