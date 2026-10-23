"""Orkestrasi satu run: kumpulkan, saring, dedup, state, bangun pesan."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from . import filters
from .collectors import html_list, pdf_list, rss
from .collectors.base import CollectResult
from .config import Bank, Keywords
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
    fetcher: Fetcher, bank: Bank, keywords: Keywords, state: State,
    run_date: str, report: RunReport,
) -> list[Item]:
    res = rss.collect_news(fetcher, bank, keywords.edc)
    news_url = f"news:{bank.name}"
    if res.ok:
        state.record_source_ok(news_url, run_date)
        return res.items
    state.record_source_failure(news_url, res.error or "gagal", run_date)
    report.failed.append((f"{bank.name} (berita)", res.error or "gagal"))
    return []


def collect_light(
    fetcher: Fetcher,
    banks: list[Bank],
    keywords: Keywords,
    state: State,
    run_date: str,
    report: RunReport,
) -> list[Item]:
    """Kolektor deterministik: tiap bank disentuh (public bila ada + berita)."""
    raw: list[Item] = []
    for bank in banks:
        report.checked += 1
        if bank.access == "public":
            raw.extend(_collect_public(fetcher, bank, state, run_date, report))
        # Berita dicoba untuk SEMUA bank, apa pun access-nya (menyentuh semua).
        raw.extend(_collect_news(fetcher, bank, keywords, state, run_date, report))
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
) -> RunReport:
    run_date = today.isoformat()
    report = RunReport(run_date=run_date, mode="light")
    candidates = collect_light(fetcher, banks, keywords, state, run_date, report)
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
) -> RunReport:
    """Mode full: gabung item inbox (hasil agen AI) dengan kolektor light."""
    run_date = today.isoformat()
    report = RunReport(run_date=run_date, mode="full")
    report.inbox_rejected = list(inbox.rejected)

    candidates = collect_light(fetcher, banks, keywords, state, run_date, report)
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
