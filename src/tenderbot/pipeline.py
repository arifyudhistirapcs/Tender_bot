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
from .http_client import Fetcher
from .inbox import InboxLoadResult
from .models import Item
from .state import State


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

    # 2. GDELT DOC 2.0 (kueri per kelompok bank, dijeda >=5 detik).
    kwargs = {}
    if gdelt_sleep is not None:
        kwargs["sleep"] = gdelt_sleep
    gdelt_raw, gdelt_ok, gdelt_err = rss.collect_gdelt(
        fetcher, banks, keywords.edc, keywords.credible_news_domains, **kwargs
    )
    gdelt_items, gdelt_covered = rss.map_gdelt_to_banks(gdelt_raw, banks)
    items.extend(gdelt_items)
    if gdelt_ok:
        state.record_source_ok("gdelt", run_date)
    else:
        state.record_source_failure("gdelt", gdelt_err or "gagal", run_date)
        report.failed.append(("GDELT", gdelt_err or "gagal"))

    # 3. Peta cakupan berita per bank.
    # Sebuah bank "dicek lewat berita" bila ADA sumber berita yang berhasil
    # diambil dan mencakupnya. Feed yang berhasil mencakup SEMUA bank (satu feed
    # menyentuh semua bank lewat penyaringan), jadi feed sukses = bank tercakup.
    for bank in banks:
        covered = (bank.name in gdelt_covered) or any_feed_ok
        if covered:
            report.news_checked_banks.append(bank.name)
        else:
            if gdelt_err:
                reason = f"semua feed media + GDELT gagal ({gdelt_err})"
            else:
                reason = "semua feed media gagal; GDELT tidak mencakup bank ini"
            report.news_failed_banks.append((bank.name, reason))
            report.failed.append((f"{bank.name} (berita)", reason))

    return items


def collect_light(
    fetcher: Fetcher,
    banks: list[Bank],
    feeds: list[NewsFeed],
    keywords: Keywords,
    state: State,
    run_date: str,
    report: RunReport,
    gdelt_sleep=None,
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
) -> None:
    """Saring, dedup, tandai seen, isi report.new_items."""
    report.candidates = len(candidates)
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

        # Item baru dan unik.
        report.new_items.append(item)
        state.mark_seen(item, run_date)
        from .models import normalize_text  # lokal untuk hindari siklus
        seen_titles.append((item.bank, normalize_text(item.title), item.published or run_date))


def run_light(
    fetcher: Fetcher,
    banks: list[Bank],
    keywords: Keywords,
    state: State,
    today: date,
    feeds: Optional[list[NewsFeed]] = None,
    gdelt_sleep=None,
) -> RunReport:
    run_date = today.isoformat()
    report = RunReport(run_date=run_date, mode="light")
    candidates = collect_light(
        fetcher, banks, feeds or [], keywords, state, run_date, report,
        gdelt_sleep=gdelt_sleep,
    )
    process_candidates(candidates, keywords, state, today, run_date, report)
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
            report.failed.append((failed.get("bank", "?"), failed.get("reason", "?")))

    process_candidates(candidates, keywords, state, today, run_date, report)
    report.unhealthy_sources = state.unhealthy_sources()
    return report
