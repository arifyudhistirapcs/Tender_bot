"""Uji laporan detail Telegram: report.json + report.md.

Mencakup: run normal dengan tender, run dilewati (skip), dan jaminan bahwa
detail teknis (sumber gagal, GDELT, metode, kontak) MASUK ke laporan ini,
berbeda dari pesan Google Chat versi bisnis yang menyembunyikannya.
"""

import json

from tenderbot.models import Item, fingerprint
from tenderbot.pipeline import RunReport
from tenderbot.report import (
    ReportContext,
    build_report_json,
    build_report_md,
    write_report,
)


def _item():
    it = Item(
        bank="Bank Sumut",
        title="Pengadaan Sewa Beli Mesin Smart EDC",
        url="https://banksumut.co.id/edc",
        value_idr=6993000000,
        status="berjalan",
        reg_close="2026-10-23",
        method="Pelelangan Umum Pascakualifikasi",
        contact="panitia@banksumut.co.id",
        attachment_url="https://banksumut.co.id/edc.pdf",
    )
    it.fingerprint = fingerprint(it.bank, it.title, it.url)
    return it


def _report_with_item():
    r = RunReport(run_date="2026-10-23", mode="light", checked=43, candidates=5,
                  passed_filter=2, ongoing_count=1, upcoming_count=0)
    r.new_items = [_item()]
    r.failed = [("GDELT", "HTTP 429"), ("BRI (berita)", "WAF Incapsula")]
    r.dropped = [("Bank Jatim", "Market Sounding EDC", "sudah tutup")]
    r.deferred_js = ["BRI: portal butuh browser, dicek di mode full"]
    return r


def test_report_json_skema_dan_counts():
    r = _report_with_item()
    ctx = ReportContext(event="schedule", dry_run=False, sent=True)
    j = build_report_json(r, ctx)
    assert j["run_date"] == "2026-10-23"
    assert j["mode"] == "light"
    assert j["event"] == "schedule"
    assert j["sent"] is True
    assert j["skipped"] is None
    assert j["counts"] == {
        "checked": 43, "failed": 2, "candidates": 5, "passed": 2,
        "new": 1, "ongoing": 1, "upcoming": 0,
    }
    # Item lengkap dengan semua field + status.
    assert j["items"][0]["bank"] == "Bank Sumut"
    assert j["items"][0]["method"] == "Pelelangan Umum Pascakualifikasi"
    assert j["items"][0]["status"] == "berjalan"
    # Dropped, failures, needs_browser.
    assert j["dropped"][0]["reason"] == "sudah tutup"
    assert {"source": "GDELT", "reason": "HTTP 429"} in j["failures"]
    assert j["needs_browser"] == ["BRI: portal butuh browser, dicek di mode full"]


def test_report_md_memuat_detail_teknis():
    r = _report_with_item()
    ctx = ReportContext(event="schedule", dry_run=False, sent=True)
    md = build_report_md(r, ctx)
    # Ringkasan + status pesan GChat.
    assert "Laporan Tender Bot - 2026-10-23" in md
    assert "Pesan Google Chat: TERKIRIM." in md
    # Detail tender: method, kontak, nilai, URL lampiran.
    assert "Pelelangan Umum Pascakualifikasi" in md
    assert "panitia@banksumut.co.id" in md
    assert "Rp6.993.000.000" in md
    assert "https://banksumut.co.id/edc.pdf" in md
    # Item dibuang + alasan, sumber gagal + alasan, butuh browser.
    assert "sudah tutup" in md
    assert "GDELT: HTTP 429" in md
    assert "WAF Incapsula" in md
    assert "butuh browser" in md
    # Tanpa tabel markdown.
    assert "|---" not in md and "| " not in md


def test_report_md_run_dilewati():
    r = RunReport(run_date="2026-10-24", mode="light")
    ctx = ReportContext(event="schedule", dry_run=False, sent=False,
                        skipped="akhir pekan (Saturday)")
    md = build_report_md(r, ctx)
    assert "Run DILEWATI: akhir pekan (Saturday)." in md
    assert "Pesan Google Chat: DILEWATI" in md


def test_report_json_skip_dan_dry_run_fields():
    r = RunReport(run_date="2026-10-26", mode="light")
    ctx = ReportContext(event="workflow_dispatch", dry_run=True, sent=False,
                        skipped="slot sudah terisi")
    j = build_report_json(r, ctx)
    assert j["dry_run"] is True
    assert j["skipped"] == "slot sudah terisi"
    assert j["counts"]["new"] == 0
    assert j["items"] == []


def test_write_report_menulis_dua_file(tmp_path):
    r = _report_with_item()
    ctx = ReportContext(event="schedule", dry_run=False, sent=True)
    jp, mp = write_report(r, ctx, tmp_path / "report")
    assert jp.exists() and mp.exists()
    # report.json valid dan bisa diparse ulang.
    data = json.loads(jp.read_text(encoding="utf-8"))
    assert data["counts"]["new"] == 1
    # report.md diakhiri newline tunggal.
    text = mp.read_text(encoding="utf-8")
    assert text.endswith("\n")
