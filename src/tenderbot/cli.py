"""Antarmuka baris perintah Tender Bot.

  python -m tenderbot run --mode light|full [--inbox PATH] [--dry-run] [--today YYYY-MM-DD]

Hari libur dan akhir pekan: keluar tanpa kirim.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from . import config, gchat
from .calendar_util import should_skip
from .http_client import Fetcher
from .inbox import InboxError, load_inbox
from .pipeline import RunReport, run_full, run_light
from .state import State

# state/ di akar repo.
DEFAULT_STATE_DIR = config.REPO_ROOT / "state"


def _parse_today(value: Optional[str]) -> date:
    if not value:
        return date.today()
    return date.fromisoformat(value)


def _print_report(report: RunReport) -> None:
    print(f"[tenderbot] run {report.run_date} mode={report.mode}", file=sys.stderr)
    print(
        f"  bank dicek: {report.checked} | gagal akses: {len(report.failed)} | "
        f"kandidat: {report.candidates} | lolos saringan: {report.passed_filter} | "
        f"baru: {len(report.new_items)}",
        file=sys.stderr,
    )
    if report.inbox_rejected:
        print(f"  inbox ditolak: {len(report.inbox_rejected)}", file=sys.stderr)
        for r in report.inbox_rejected:
            print(f"    - {r}", file=sys.stderr)
    print(
        f"  berita: {len(report.news_checked_banks)} bank tercakup, "
        f"{len(report.news_failed_banks)} gagal lewat berita",
        file=sys.stderr,
    )
    if report.news_failed_banks:
        for name, reason in report.news_failed_banks:
            print(f"    gagal berita {name}: {reason}", file=sys.stderr)
    if report.failed:
        for name, reason in report.failed:
            print(f"    gagal {name}: {reason}", file=sys.stderr)
    if report.deferred_js:
        print(f"  butuh browser (ditunda ke mode full): {len(report.deferred_js)}",
              file=sys.stderr)
        for d in report.deferred_js:
            print(f"    - {d}", file=sys.stderr)
    if report.unhealthy_sources:
        print("  sumber bermasalah (>=3 gagal berturut-turut):", file=sys.stderr)
        for url, fails, last in report.unhealthy_sources:
            print(f"    - {url}: {fails}x; {last}", file=sys.stderr)


def cmd_run(args: argparse.Namespace) -> int:
    today = _parse_today(args.today)

    banks = config.load_banks()
    keywords = config.load_keywords()
    holidays = config.load_holidays()
    feeds = config.load_news_feeds()

    skip, reason = should_skip(today, holidays)
    if skip:
        print(f"[tenderbot] {today.isoformat()} dilewati: {reason}. Tidak mengirim.",
              file=sys.stderr)
        return 0

    state_dir = Path(args.state_dir) if args.state_dir else DEFAULT_STATE_DIR
    state = State.load(state_dir)

    # Cadangan mode full: bila run full sudah tercatat hari ini, light berhenti.
    if args.mode == "light" and state.has_full_run_on(today.isoformat()):
        print(f"[tenderbot] run full sudah berjalan {today.isoformat()}; "
              f"light tidak mengirim.", file=sys.stderr)
        return 0

    fetcher = Fetcher()

    if args.mode == "full":
        if not args.inbox:
            print("[tenderbot] mode full wajib --inbox PATH", file=sys.stderr)
            return 2
        try:
            inbox = load_inbox(Path(args.inbox))
        except InboxError as exc:
            print(f"[tenderbot] inbox tidak sah: {exc}", file=sys.stderr)
            return 2
        report = run_full(fetcher, banks, keywords, state, today, inbox, feeds=feeds)
    else:
        report = run_light(fetcher, banks, keywords, state, today, feeds=feeds)

    _print_report(report)

    payload = gchat.build_message(report.new_items, report.checked, report.failed)
    outcome = gchat.send(payload, dry_run=args.dry_run)
    print(f"[tenderbot] {outcome.message}", file=sys.stderr)

    # State hanya disimpan bila run sukses dan (terkirim ATAU dry-run).
    # Pada dry-run kita TIDAK menandai seen supaya uji coba bisa diulang.
    if not args.dry_run and outcome.sent:
        state.record_run(
            today.isoformat(), report.mode, report.checked,
            len(report.failed), len(report.new_items), status="ok",
        )
        state.save()
    elif args.dry_run:
        print("[tenderbot] dry-run: state tidak disimpan, seen tidak ditandai.",
              file=sys.stderr)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tenderbot", description="Pemantau tender EDC bank.")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="jalankan satu run")
    run_p.add_argument("--mode", choices=["light", "full"], required=True)
    run_p.add_argument("--inbox", help="path file inbox (mode full)")
    run_p.add_argument("--dry-run", action="store_true",
                       help="cetak JSON pesan, jangan kirim, jangan simpan state")
    run_p.add_argument("--today", help="override tanggal YYYY-MM-DD (uji)")
    run_p.add_argument("--state-dir", help="override folder state/ (uji)")
    run_p.set_defaults(func=cmd_run)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
