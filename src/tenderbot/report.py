"""Laporan detail untuk Telegram: tulis report.json + report.md ke sebuah DIR.

Keputusan Arif (2026-10-26): pesan Google Chat singkat untuk tim bisnis; SEMUA
detail teknis pindah ke laporan ini yang dikirim ke Telegram. Laporan ditulis
pada SETIAP run, termasuk saat run dilewati (akhir pekan/libur/slot terisi) dan
saat dry-run, supaya koordinator selalu punya jejak lengkap.

- report.json: data terstruktur (lihat build_report_json untuk skema).
- report.md: teks polos Bahasa Indonesia, TANPA tabel markdown, agar enak
  dibaca di Telegram.

Modul ini hanya MENULIS file; tidak menyentuh jaringan, state, atau webhook.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .dates_id import format_rupiah
from .models import Item
from .pipeline import RunReport

# Label status untuk laporan detail (lebih eksplisit dari pesan bisnis).
_STATUS_LABEL = {
    "akan_dibuka": "Akan dibuka",
    "berjalan": "Berjalan",
    "tutup": "Tutup",
    "tidak_diketahui": "Tanggal belum pasti",
}

# Field Item (ISO date) yang ditampilkan sebagai "DD Bulan YYYY".
_ITEM_DATE_FIELDS = ("posted", "reg_open", "reg_close", "submit_close",
                     "published", "deadline")


@dataclass
class ReportContext:
    """Metadata run yang tidak ada di RunReport sendiri."""

    event: str = "run"              # schedule | workflow_dispatch | run | ...
    dry_run: bool = False
    sent: bool = False
    skipped: Optional[str] = None   # None bila run jalan; alasan bila dilewati
    fallback_note: bool = False     # True bila riset penuh tidak berjalan hari ini


def _fmt_date_long(iso: Optional[str]) -> Optional[str]:
    """ISO "YYYY-MM-DD" -> "DD Bulan YYYY" (bulan Indonesia penuh); None -> None."""
    if not iso:
        return None
    try:
        from datetime import date as _date
        d = _date.fromisoformat(str(iso)[:10])
    except (ValueError, TypeError):
        return str(iso)
    bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
             "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    return f"{d.day} {bulan[d.month - 1]} {d.year}"


def _item_to_dict(item: Item) -> dict:
    """Semua field Item + status untuk report.json (apa adanya, None dipertahankan)."""
    data = item.to_dict()
    # fingerprint tidak selalu relevan untuk pembaca, tapi berguna untuk lacak.
    return data


def build_report_json(report: RunReport, ctx: ReportContext) -> dict:
    """Skema report.json (lihat brief bagian 2)."""
    return {
        "run_date": report.run_date,
        "mode": report.mode,
        "event": ctx.event,
        "dry_run": ctx.dry_run,
        "sent": ctx.sent,
        "skipped": ctx.skipped,
        "fallback_note": ctx.fallback_note,
        "counts": {
            "checked": report.checked,
            "failed": len(report.failed),
            "candidates": report.candidates,
            "passed": report.passed_filter,
            "new": len(report.new_items),
            "ongoing": report.ongoing_count,
            "upcoming": report.upcoming_count,
        },
        "items": [_item_to_dict(it) for it in report.new_items],
        "dropped": [
            {"bank": bank, "title": title, "reason": reason}
            for bank, title, reason in report.dropped
        ],
        "failures": [
            {"source": name, "reason": reason}
            for name, reason in report.failed
        ],
        "needs_browser": list(report.deferred_js),
    }


def _item_md_block(item: Item) -> list[str]:
    """Blok detail satu tender untuk report.md (teks polos, tanpa tabel)."""
    lines: list[str] = []
    status = _STATUS_LABEL.get(item.status or "", item.status or "-")
    lines.append(f"- {item.bank}: {item.title}")
    lines.append(f"  Status: {status}")

    nilai = format_rupiah(item.value_idr)
    if nilai:
        lines.append(f"  Nilai/HPS: {nilai}")

    # Tanggal-tanggal penting.
    for field_name, label in (
        ("posted", "Tanggal posting"),
        ("published", "Terbit"),
        ("reg_open", "Pendaftaran buka"),
        ("reg_close", "Pendaftaran tutup"),
        ("submit_close", "Batas penawaran"),
        ("deadline", "Batas"),
    ):
        val = _fmt_date_long(getattr(item, field_name, None))
        if val:
            lines.append(f"  {label}: {val}")

    # Field teks bebas.
    for field_name, label in (
        ("volume", "Volume"),
        ("duration", "Durasi"),
        ("method", "Metode"),
        ("reg_place", "Tempat daftar"),
        ("contact", "Kontak"),
        ("media_name", "Media"),
        ("source_type", "Jenis sumber"),
        ("evidence", "Kutipan"),
    ):
        val = getattr(item, field_name, None)
        if val:
            lines.append(f"  {label}: {val}")

    if item.unverified_source:
        lines.append("  Catatan: sumber belum terverifikasi")

    # URL.
    if item.url:
        lines.append(f"  URL pengumuman: {item.url}")
    if item.attachment_url:
        lines.append(f"  URL lampiran: {item.attachment_url}")
    if item.vendor_registration_url:
        lines.append(f"  URL daftar vendor: {item.vendor_registration_url}")
    if item.vendor_registration_note:
        lines.append(f"  Cara daftar vendor: {item.vendor_registration_note}")
    return lines


def _gchat_status_line(ctx: ReportContext) -> str:
    """Status pesan Google Chat untuk ringkasan report.md."""
    if ctx.skipped:
        return f"Pesan Google Chat: DILEWATI ({ctx.skipped}), tidak ada yang dikirim."
    if ctx.dry_run:
        return "Pesan Google Chat: DRY-RUN (tidak dikirim, hanya dicetak)."
    if ctx.sent:
        return "Pesan Google Chat: TERKIRIM."
    return "Pesan Google Chat: TIDAK terkirim (pengiriman gagal)."


def build_report_md(report: RunReport, ctx: ReportContext) -> str:
    """report.md: teks polos Bahasa Indonesia untuk Telegram, tanpa tabel."""
    lines: list[str] = []
    lines.append(f"Laporan Tender Bot - {report.run_date} (mode {report.mode})")
    lines.append("")

    # Ringkasan.
    if ctx.skipped:
        lines.append(f"Run DILEWATI: {ctx.skipped}.")
    else:
        c = report
        lines.append(
            f"Ringkasan: {c.checked} bank dicek, {len(c.failed)} sumber gagal, "
            f"{c.candidates} kandidat, {c.passed_filter} lolos saringan, "
            f"{len(c.new_items)} tender baru dilaporkan "
            f"(berjalan {c.ongoing_count}, akan dibuka {c.upcoming_count})."
        )
    lines.append(_gchat_status_line(ctx))
    if ctx.fallback_note:
        lines.append("Catatan: riset penuh tidak berjalan hari ini (jalan mode light cadangan).")
    lines.append("")

    # Detail tender.
    if report.new_items:
        lines.append(f"Detail tender ({len(report.new_items)}):")
        for it in report.new_items:
            lines.extend(_item_md_block(it))
            lines.append("")
    else:
        lines.append("Tidak ada tender baru yang dilaporkan.")
        lines.append("")

    # Item dibuang.
    if report.dropped:
        lines.append(f"Item dibuang ({len(report.dropped)}):")
        for bank, title, reason in report.dropped:
            lines.append(f"- {bank}: {title} -> {reason}")
        lines.append("")

    # Sumber gagal.
    if report.failed:
        lines.append(f"Sumber gagal ({len(report.failed)}):")
        for name, reason in report.failed:
            lines.append(f"- {name}: {reason}")
        lines.append("")

    # Bank butuh browser.
    if report.deferred_js:
        lines.append(f"Butuh browser (ditunda ke mode full) ({len(report.deferred_js)}):")
        for d in report.deferred_js:
            lines.append(f"- {d}")
        lines.append("")

    # Sumber bermasalah (kesehatan).
    if report.unhealthy_sources:
        lines.append("Sumber bermasalah (>=3 gagal berturut-turut):")
        for url, fails, last in report.unhealthy_sources:
            lines.append(f"- {url}: {fails}x; {last}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_report(report: RunReport, ctx: ReportContext, out_dir: Path) -> tuple[Path, Path]:
    """Tulis report.json + report.md ke out_dir. Kembalikan (path_json, path_md)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "report.json"
    md_path = out_dir / "report.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(build_report_json(report, ctx), fh,
                  ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    with md_path.open("w", encoding="utf-8") as fh:
        fh.write(build_report_md(report, ctx))
    return json_path, md_path
