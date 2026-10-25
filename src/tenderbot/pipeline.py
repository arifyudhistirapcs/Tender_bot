"""Orkestrasi satu run: kumpulkan, saring, dedup, state, bangun pesan."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from . import filters
from .collectors import html_list, pdf_list, rss
from .collectors.base import CollectResult
from .config import Bank, Keywords, NewsFeed
from .dedup import ensure_fingerprint, is_near_duplicate
from .enrich import enrich_item
from .http_client import Fetcher
from .inbox import InboxLoadResult
from .models import Item
from .state import State
from .status import (
    STATUS_ONGOING,
    STATUS_UPCOMING,
    compute_status,
    report_decision,
)


@dataclass
class RunReport:
    run_date: str
    mode: str
    checked: int = 0
    failed: list[tuple[str, str]] = field(default_factory=list)  # (nama, alasan)
    candidates: int = 0
    passed_filter: int = 0
    new_items: list[Item] = field(default_factory=list)
    inbox_rejected: list[str] = field(default_factory=list)
    unhealthy_sources: list[tuple[str, int, Optional[str]]] = field(default_factory=list)
    deferred_js: list[str] = field(default_factory=list)  # sumber/bank butuh browser
    news_checked_banks: list[str] = field(default_factory=list)  # bank tercakup berita
    news_failed_banks: list[tuple[str, str]] = field(default_factory=list)  # (bank, alasan)
    news_feed_failures: list[tuple[str, str]] = field(default_factory=list)  # (nama feed, alasan)
    news_gdelt_failure: Optional[str] = None  # alasan GDELT gagal (None bila ok)
    dropped: list[tuple[str, str, str]] = field(default_factory=list)  # (bank, judul, alasan)
    ongoing_count: int = 0   # jumlah tender berjalan di laporan
    upcoming_count: int = 0  # jumlah tender akan dibuka di laporan


_COLLECTOR_BY_TYPE = {
    "rss": rss.collect_rss,
    "html": html_list.collect_html_list,
    "pdf_list": pdf_list.collect_pdf_list,
}


def _collect_public(
    fetcher: Fetcher, bank: Bank, state: State, run_date: str, report: RunReport
) -> list[Item]:
    """Kumpulkan dari sumber public bank + catat kesehatan sumber."""
    out: list[Item] = []
    for src in bank.sources:
        if src.needs_js:
            report.deferred_js.append(
                f"{bank.name} ({src.url}): butuh browser, dicek di mode full"
            )
            continue
        collector = _COLLECTOR_BY_TYPE.get(src.type)
        if collector is None:
            report.failed.append((f"{bank.name} ({src.url})", f"tipe tak dikenal: {src.type}"))
            continue
        res: CollectResult = collector(fetcher, bank, src.url)
        if res.ok:
            state.record_source_ok(src.url, run_date)
            out.extend(res.items)
        else:
            state.record_source_failure(src.url, res.error or "gagal", run_date)
            report.failed.append((f"{bank.name} ({src.type})", res.error or "gagal"))
    return out


def _collect_news(
    fetcher: Fetcher,
    banks: list[Bank],
    feeds: list[NewsFeed],
    keywords: Keywords,
    state: State,
    run_date: str,
    report: RunReport,
    gdelt_sleep=None,
) -> list[Item]:
    """Kumpulkan berita dari feed media + GDELT, SEKALI per sumber per run.

    Menautkan tiap bank ke status "dicek lewat berita":
      - bila >=1 feed berhasil DAN item berita bank itu muncul, atau GDELT
        kueri yang mencakupnya berhasil -> bank tercakup berita;
      - bila semua sumber berita gagal -> catat per bank dengan alasannya.
    """
    items: list[Item] = []

    # 1. Feed RSS media (sekali per feed).
    feed_items, feed_ok, feed_failures = rss.collect_media_feeds(
        fetcher, feeds, banks, keywords.edc, keywords.credible_news_domains
    )
    items.extend(feed_items)
    any_feed_ok = any(feed_ok.values())
    for feed in feeds:
        url = feed.url
        if feed_ok.get(url):
            state.record_source_ok(f"feed:{url}", run_date)
        else:
            state.record_source_failure(f"feed:{url}", "gagal", run_date)
    for name, reason in feed_failures:
        report.failed.append((f"feed {name}", reason))
    # Catat kegagalan feed untuk ringkasan jujur (nama feed + alasan).
    report.news_feed_failures.extend(feed_failures)

    # 2. GDELT DOC 2.0 (kueri per kelompok bank, dijeda >=5 detik, backoff 429).
    kwargs = {}
    if gdelt_sleep is not None:
        kwargs["sleep"] = gdelt_sleep
    gdelt_raw, gdelt_covered_query, gdelt_err = rss.collect_gdelt(
        fetcher, banks, keywords.edc, keywords.credible_news_domains, **kwargs
    )
    gdelt_items, _gdelt_article_covered = rss.map_gdelt_to_banks(gdelt_raw, banks)
    items.extend(gdelt_items)
    if not gdelt_err:
        state.record_source_ok("gdelt", run_date)
    else:
        state.record_source_failure("gdelt", gdelt_err, run_date)
        report.failed.append(("GDELT", gdelt_err))
        report.news_gdelt_failure = gdelt_err

    # 3. Peta cakupan berita per bank (JUJUR).
    # Sebuah bank "tercakup berita" hanya bila ADA sumber berita yang BERHASIL
    # mencakupnya:
    #   - GDELT kelompoknya berhasil diambil (bank ada di gdelt_covered_query), ATAU
    #   - setidaknya satu feed RSS berhasil (feed menyentuh semua bank lewat saring).
    # Bila keduanya gagal untuk bank itu -> masuk failed dengan alasan gabungan.
    for bank in banks:
        covered = (bank.name in gdelt_covered_query) or any_feed_ok
        if covered:
            report.news_checked_banks.append(bank.name)
        else:
            reason = _news_failure_reason(gdelt_err, feed_failures, any_feed_ok)
            report.news_failed_banks.append((bank.name, reason))
            report.failed.append((f"{bank.name} (berita)", reason))

    return items


def _news_failure_reason(
    gdelt_err: Optional[str],
    feed_failures: list[tuple[str, str]],
    any_feed_ok: bool,
) -> str:
    """Alasan ringkas kenapa sebuah bank tidak tercakup berita."""
    gdelt_part = f"GDELT {gdelt_err}" if gdelt_err else "GDELT tidak mencakup bank ini"
    if any_feed_ok:
        feed_part = "feed media ok tapi tidak mencakup bank ini"
    elif feed_failures:
        feed_part = "feed gagal"
    else:
        feed_part = "tidak ada feed media"
    return f"berita: {gdelt_part}, {feed_part}"


def collect_light(
    fetcher: Fetcher,
    banks: list[Bank],
    feeds: list[NewsFeed],
    keywords: Keywords,
    state: State,
    run_date: str,
    report: RunReport,
    gdelt_sleep=None,
    skip_news: bool = False,
) -> list[Item]:
    """Kolektor deterministik: tiap bank disentuh (public bila ada + berita)."""
    raw: list[Item] = []
    for bank in banks:
        report.checked += 1
        if bank.needs_js:
            report.deferred_js.append(
                f"{bank.name}: portal butuh browser, dicek di mode full"
            )
        if bank.access == "public":
            raw.extend(_collect_public(fetcher, bank, state, run_date, report))
    # Berita dikumpulkan SEKALI untuk semua bank (satu ambil per feed per run,
    # kueri GDELT per kelompok bank), bukan sekali per bank.
    if not skip_news:
        raw.extend(
            _collect_news(
                fetcher, banks, feeds, keywords, state, run_date, report,
                gdelt_sleep=gdelt_sleep,
            )
    )
    return raw


def process_candidates(
    candidates: list[Item],
    keywords: Keywords,
    state: State,
    today: date,
    run_date: str,
    report: RunReport,
    fetcher: Optional[Fetcher] = None,
    enrich: bool = True,
    banks: Optional[list[Bank]] = None,
) -> None:
    """Saring, dedup, pengayaan detail, hitung status, tandai seen.

    Alur per item baru-unik:
      1. pengayaan detail (buka halaman detail + lampiran PDF) bila fetcher ada;
      2. hitung status dengan tanggal hari ini;
      3. keputusan laporan: tutup dibuang (tetap seen); tidak_diketahui dibuang
         bila lama; akan_dibuka/berjalan dikirim.
    Item yang dibuang TETAP ditandai seen supaya tidak dicek lagi.
    """
    report.candidates = len(candidates)
    # Peta nama bank -> info daftar vendor (dari banks.yaml), untuk kartu.
    vendor_by_bank: dict[str, tuple[Optional[str], Optional[str]]] = {}
    for b in banks or []:
        vendor_by_bank[b.name] = (
            b.vendor_registration_url or None,
            b.vendor_registration_note or None,
        )
    # Judul yang sudah dilihat (untuk near-dup), ditambah yang lolos di run ini.
    seen_titles = state.seen_titles()

    for item in candidates:
        verdict = filters.evaluate(item, keywords, today)
        if not verdict.passed:
            continue
        report.passed_filter += 1
        ensure_fingerprint(item)

        if state.is_seen(item.fingerprint):
            continue
        if is_near_duplicate(item, seen_titles, today):
            continue

        # Item baru dan unik: tandai seen lebih dulu (apa pun keputusannya).
        state.mark_seen(item, run_date)
        from .models import normalize_text  # lokal untuk hindari siklus
        seen_titles.append((item.bank, normalize_text(item.title), item.published or run_date))

        # Pengayaan detail (opsional; butuh jaringan).
        if enrich and fetcher is not None:
            try:
                enrich_item(item, fetcher)
            except Exception:
                pass  # kegagalan pengayaan tidak boleh menggagalkan run

        # Status + keputusan laporan.
        item.status = compute_status(item, today)
        send_ok, reason = report_decision(item, today)
        if not send_ok:
            report.dropped.append((item.bank, item.title, reason))
            continue

        if item.status == STATUS_ONGOING:
            report.ongoing_count += 1
        elif item.status == STATUS_UPCOMING:
            report.upcoming_count += 1

        # Info daftar vendor bank (untuk tombol "Daftar vendor" di kartu).
        vinfo = vendor_by_bank.get(item.bank)
        if vinfo:
            if item.vendor_registration_url is None:
                item.vendor_registration_url = vinfo[0]
            if item.vendor_registration_note is None:
                item.vendor_registration_note = vinfo[1]

        report.new_items.append(item)


def run_light(
    fetcher: Fetcher,
    banks: list[Bank],
    keywords: Keywords,
    state: State,
    today: date,
    feeds: Optional[list[NewsFeed]] = None,
    gdelt_sleep=None,
    skip_news: bool = False,
) -> RunReport:
    run_date = today.isoformat()
    report = RunReport(run_date=run_date, mode="light")
    candidates = collect_light(
        fetcher, banks, feeds or [], keywords, state, run_date, report,
        gdelt_sleep=gdelt_sleep, skip_news=skip_news,
    )
    process_candidates(candidates, keywords, state, today, run_date, report,
                       fetcher=fetcher, banks=banks)
    report.unhealthy_sources = state.unhealthy_sources()
    return report


def run_full(
    fetcher: Fetcher,
    banks: list[Bank],
    keywords: Keywords,
    state: State,
    today: date,
    inbox: InboxLoadResult,
    feeds: Optional[list[NewsFeed]] = None,
    gdelt_sleep=None,
) -> RunReport:
    """Mode full: gabung item inbox (hasil agen AI) dengan kolektor light."""
    run_date = today.isoformat()
    report = RunReport(run_date=run_date, mode="full")
    report.inbox_rejected = list(inbox.rejected)

    candidates = collect_light(
        fetcher, banks, feeds or [], keywords, state, run_date, report,
        gdelt_sleep=gdelt_sleep,
    )
    # Item inbox sudah dinilai agen; tetap lewat saringan + dedup sebagai jaring.
    candidates.extend(inbox.items)

    # Cakupan inbox ikut dihitung untuk pelaporan.
    for name in inbox.coverage_checked:
        report.checked += 1
    for failed in inbox.coverage_failed:
        if isinstance(failed, dict):
            reason = str(failed.get("reason", "?"))
            # Potong alasan panjang agar pesan ringkas (maks ~120 karakter).
            if len(reason) > 120:
                reason = reason[:117].rstrip() + "..."
            report.failed.append((failed.get("bank", "?"), reason))

    process_candidates(candidates, keywords, state, today, run_date, report,
                       fetcher=fetcher, banks=banks)
    report.unhealthy_sources = state.unhealthy_sources()
    return report
