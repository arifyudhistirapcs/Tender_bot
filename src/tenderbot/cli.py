"""Antarmuka baris perintah Tender Bot.

  python -m tenderbot run --mode light|full [--inbox PATH] [--dry-run] [--today YYYY-MM-DD]

Hari libur dan akhir pekan: keluar tanpa kirim.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from . import config, gchat
from .calendar_util import should_skip
from .http_client import Fetcher
from .inbox import InboxError, load_inbox
from .pipeline import RunReport, run_full, run_light
from .report import ReportContext, write_report
from .state import State

# state/ di akar repo.
DEFAULT_STATE_DIR = config.REPO_ROOT / "state"

# Zona waktu operasional bot. Semua "hari ini" dihitung di WIB, bukan UTC,
# supaya cron Actions (UTC) tidak salah tanggal di sekitar tengah malam WIB.
WIB = timezone(timedelta(hours=7))

# Catatan cadangan bila riset penuh tidak berjalan (DESIGN.md mode full).
FALLBACK_NOTE = "Catatan: riset penuh tidak berjalan hari ini."


def _today_wib() -> date:
    """Tanggal hari ini di zona Asia/Jakarta (WIB)."""
    return datetime.now(WIB).date()


def _now_hour_wib() -> int:
    """Jam (0-23) saat ini di WIB, untuk menentukan slot pagi/sore."""
    return datetime.now(WIB).hour


def _slot_of_hour(hour_wib: int) -> str:
    """Slot: pagi (<12.00 WIB) / sore (>=12.00 WIB)."""
    return "pagi" if hour_wib < 12 else "sore"


def _parse_today(value: Optional[str]) -> date:
    if not value:
        return _today_wib()
    return date.fromisoformat(value)


def _print_report(report: RunReport) -> None:
    print(f"[tenderbot] run {report.run_date} mode={report.mode}", file=sys.stderr)
    print(
        f"  bank dicek: {report.checked} | gagal akses: {len(report.failed)} | "
        f"kandidat: {report.candidates} | lolos saringan: {report.passed_filter} | "
        f"baru: {len(report.new_items)} (berjalan {report.ongoing_count}, "
        f"akan dibuka {report.upcoming_count})",
        file=sys.stderr,
    )
    if report.dropped:
        print(f"  dibuang (status): {len(report.dropped)}", file=sys.stderr)
        for bank, title, reason in report.dropped:
            print(f"    - {bank}: {title[:60]} -> {reason}", file=sys.stderr)
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


def _emit_report(args: argparse.Namespace, report: RunReport, ctx: ReportContext) -> None:
    """Tulis report.json + report.md bila --report-out diberikan.

    Dipanggil di SETIAP jalur keluar (dilewati, slot terisi, dry-run, normal)
    supaya koordinator selalu punya jejak. Diam saja bila --report-out kosong.
    """
    if not getattr(args, "report_out", None):
        return
    try:
        json_path, md_path = write_report(report, ctx, Path(args.report_out))
        print(f"[tenderbot] laporan ditulis: {json_path} ; {md_path}", file=sys.stderr)
    except OSError as exc:
        # Kegagalan menulis laporan tidak boleh menggagalkan run utama.
        print(f"[tenderbot] gagal menulis laporan: {exc}", file=sys.stderr)


def cmd_run(args: argparse.Namespace) -> int:
    today = _parse_today(args.today)
    run_date = today.isoformat()
    hour_wib = _now_hour_wib()
    slot = _slot_of_hour(hour_wib)
    event = args.event or "run"

    banks = config.load_banks()
    keywords = config.load_keywords()
    holidays = config.load_holidays()
    feeds = config.load_news_feeds()

    # Penyaring cakupan untuk smoke/debug terarah (tetap jalur run_light nyata):
    # --only-bank membatasi ke bank yang namanya memuat substring (boleh berulang);
    # --skip-news mematikan kolektor berita (feed + GDELT) supaya deterministik.
    if args.only_bank:
        wanted = [s.lower() for s in args.only_bank]
        banks = [b for b in banks if any(w in b.name.lower() for w in wanted)]
        if not banks:
            print(f"[tenderbot] --only-bank {args.only_bank} tak cocok bank mana pun.",
                  file=sys.stderr)
            return 2
    if args.skip_news:
        feeds = []

    skip, reason = should_skip(today, holidays)
    if skip:
        print(f"[tenderbot] {run_date} dilewati: {reason}. Tidak mengirim.",
              file=sys.stderr)
        _emit_report(
            args,
            RunReport(run_date=run_date, mode=args.mode),
            ReportContext(event=event, dry_run=args.dry_run, sent=False,
                          skipped=reason),
        )
        return 0

    state_dir = Path(args.state_dir) if args.state_dir else DEFAULT_STATE_DIR
    state = State.load(state_dir)

    # Penjaga slot: bila sudah ada run NON-dry-run di tanggal + slot yang sama,
    # keluar tanpa kirim. Dry-run tidak pernah menandai slot, jadi aman diulang.
    if args.once_per_slot and not args.dry_run and state.has_run_on_slot(run_date, slot):
        msg = "slot sudah terisi"
        print(f"[tenderbot] {run_date} slot {slot} sudah terisi; tidak mengirim.",
              file=sys.stderr)
        _emit_report(
            args,
            RunReport(run_date=run_date, mode=args.mode),
            ReportContext(event=event, dry_run=args.dry_run, sent=False, skipped=msg),
        )
        return 0

    note: Optional[str] = None

    # Cadangan riset penuh (Senin/Rabu/Jumat pagi, DESIGN.md).
    # --fallback-full-check: bila state sudah mencatat run full hari ini (WIB),
    # berhenti tanpa kirim; bila belum, lanjut light dengan catatan cadangan.
    # Berlaku hanya untuk mode light.
    if args.fallback_full_check and args.mode == "light":
        if state.has_full_run_on(run_date):
            print(f"[tenderbot] run full sudah tercatat {run_date}; "
                  f"cadangan light tidak mengirim.", file=sys.stderr)
            _emit_report(
                args,
                RunReport(run_date=run_date, mode="light"),
                ReportContext(event=event, dry_run=args.dry_run, sent=False,
                              skipped="run full sudah tercatat hari ini"),
            )
            return 0
        note = FALLBACK_NOTE
        print(f"[tenderbot] cadangan: run full belum tercatat {run_date}; "
              f"jalan light dengan catatan.", file=sys.stderr)

    # Cadangan mode full: bila run full sudah tercatat hari ini, light berhenti.
    if args.mode == "light" and state.has_full_run_on(run_date):
        print(f"[tenderbot] run full sudah berjalan {run_date}; "
              f"light tidak mengirim.", file=sys.stderr)
        _emit_report(
            args,
            RunReport(run_date=run_date, mode="light"),
            ReportContext(event=event, dry_run=args.dry_run, sent=False,
                          skipped="run full sudah tercatat hari ini"),
        )
        return 0

    fetcher = Fetcher()

    if args.mode == "full":
        if not args.inbox:
            print("[tenderbot] mode full wajib --inbox PATH", file=sys.stderr)
            return 2
        try:
            inbox = load_inbox(Path(args.inbox))
        except InboxError as exc:
            # Inbox tidak sah / tidak ada: run GAGAL (exit bukan nol), pesan ke
            # stderr, dan state TIDAK disimpan (kita return sebelum record_run).
            # Kode 3 dibedakan dari 2 (salah pakai argumen) supaya CI bisa
            # membedakan "inbox rusak" dari "perintah salah".
            print(f"[tenderbot] inbox tidak sah: {exc}", file=sys.stderr)
            _emit_report(
                args,
                RunReport(run_date=run_date, mode="full"),
                ReportContext(event=event, dry_run=args.dry_run, sent=False,
                              skipped=f"inbox tidak sah: {exc}"),
            )
            return 3
        report = run_full(fetcher, banks, keywords, state, today, inbox, feeds=feeds)
    else:
        report = run_light(fetcher, banks, keywords, state, today, feeds=feeds,
                           skip_news=args.skip_news)

    _print_report(report)

    payload = gchat.build_message(
        report.new_items, report.checked, report.failed, note=note
    )
    outcome = gchat.send(payload, dry_run=args.dry_run)
    print(f"[tenderbot] {outcome.message}", file=sys.stderr)

    # Laporan detail: tulis SEBELUM/terlepas dari penyimpanan state.
    _emit_report(
        args,
        report,
        ReportContext(event=event, dry_run=args.dry_run, sent=outcome.sent,
                      skipped=None, fallback_note=bool(note)),
    )

    # State hanya disimpan bila run sukses dan (terkirim ATAU dry-run).
    # Pada dry-run kita TIDAK menandai seen supaya uji coba bisa diulang.
    if not args.dry_run and outcome.sent:
        state.record_run(
            run_date, report.mode, report.checked,
            len(report.failed), len(report.new_items), status="ok",
            hour_wib=hour_wib, slot=slot,
        )
        state.save()
    elif args.dry_run:
        print("[tenderbot] dry-run: state tidak disimpan, seen tidak ditandai.",
              file=sys.stderr)

    # Pengiriman gagal (bukan dry-run): keluar dengan kode bukan nol supaya
    # job Actions merah dan state TIDAK di-commit (seen tidak ditandai).
    if not args.dry_run and not outcome.sent:
        print("[tenderbot] pengiriman GAGAL; state tidak disimpan.", file=sys.stderr)
        return 1

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
    run_p.add_argument(
        "--fallback-full-check", action="store_true",
        help="cadangan Senin/Rabu: bila run full sudah tercatat hari ini (WIB) "
             "keluar tanpa kirim; bila belum, jalan light dengan catatan cadangan",
    )
    run_p.add_argument(
        "--only-bank", action="append", metavar="SUBSTRING",
        help="batasi ke bank yang namanya memuat SUBSTRING (boleh berulang; uji/debug)",
    )
    run_p.add_argument(
        "--skip-news", action="store_true",
        help="matikan kolektor berita (feed media + GDELT) untuk run deterministik",
    )
    run_p.add_argument(
        "--report-out", metavar="DIR",
        help="tulis laporan detail report.json + report.md ke DIR (untuk Telegram); "
             "ditulis juga saat run dilewati dan saat dry-run",
    )
    run_p.add_argument(
        "--once-per-slot", action="store_true",
        help="penjaga slot: bila sudah ada run non-dry-run di tanggal + slot "
             "(pagi <12.00 WIB / sore) yang sama, keluar tanpa kirim",
    )
    run_p.add_argument(
        "--event", metavar="NAME", default="",
        help="nama event pemicu untuk field 'event' di report.json "
             "(mis. schedule / workflow_dispatch); opsional",
    )
    run_p.set_defaults(func=cmd_run)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
