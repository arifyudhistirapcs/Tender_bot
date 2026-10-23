"""Uji status tender dan keputusan laporan (termasuk uji wajib brief)."""

from datetime import date

from tenderbot.models import Item
from tenderbot.status import (
    STATUS_CLOSED,
    STATUS_ONGOING,
    STATUS_UNKNOWN,
    STATUS_UPCOMING,
    compute_status,
    estimate_date_from_url,
    report_decision,
)


def _item(**kw):
    base = dict(bank="Bank X", title="T", url="https://x.example/1")
    base.update(kw)
    return Item(**base)


def test_akan_dibuka():
    it = _item(reg_open="2026-11-01", reg_close="2026-11-10")
    assert compute_status(it, date(2026, 10, 23)) == STATUS_UPCOMING


def test_berjalan():
    it = _item(reg_open="2026-10-13", reg_close="2026-10-23")
    assert compute_status(it, date(2026, 10, 20)) == STATUS_ONGOING


def test_tutup():
    it = _item(reg_open="2026-10-13", reg_close="2026-10-23")
    assert compute_status(it, date(2026, 10, 26)) == STATUS_CLOSED


def test_tidak_diketahui_tanpa_tutup():
    it = _item(reg_open=None, reg_close=None)
    assert compute_status(it, date(2026, 10, 23)) == STATUS_UNKNOWN


def test_tutup_terakhir_pakai_submit_close():
    # reg_close 23 Okt, submit_close 30 Okt -> tutup terakhir 30 Okt.
    it = _item(reg_open="2026-10-13", reg_close="2026-10-23", submit_close="2026-10-30")
    assert compute_status(it, date(2026, 10, 26)) == STATUS_ONGOING


# ---- Uji wajib brief: Smart EDC Bank Sumut ----

def _smart_edc():
    return _item(
        bank="Bank Sumut",
        title="Pengadaan Sewa Beli Mesin Smart EDC",
        reg_open="2026-10-13",
        reg_close="2026-10-23",  # tutup 23 Okt 2026 17.00
    )


def test_smart_edc_tutup_untuk_26_okt():
    it = _smart_edc()
    it.status = compute_status(it, date(2026, 10, 26))
    assert it.status == STATUS_CLOSED
    send_ok, reason = report_decision(it, date(2026, 10, 26))
    assert not send_ok
    assert reason == "sudah tutup"


def test_smart_edc_berjalan_untuk_23_okt():
    it = _smart_edc()
    it.status = compute_status(it, date(2026, 10, 23))
    assert it.status == STATUS_ONGOING
    send_ok, _ = report_decision(it, date(2026, 10, 23))
    assert send_ok


# ---- Uji wajib brief: Jatim market sounding (lampiran Mei 2026) ----

def test_jatim_market_sounding_dibuang_26_okt():
    it = _item(
        bank="Bank Jatim",
        title="Market Sounding Managed Service EDC Soundbox",
        url="https://www.bankjatim.co.id/.../market-sounding-edc",
        attachment_url="https://www.bankjatim.co.id/files/pengumuman/2026/mei/ms-edc.pdf",
        # tanpa tanggal tutup -> tidak_diketahui, perkiraan Mei 2026 (sudah lama).
    )
    it.status = compute_status(it, date(2026, 10, 26))
    assert it.status == STATUS_UNKNOWN
    send_ok, reason = report_decision(it, date(2026, 10, 26))
    assert not send_ok
    assert reason == "tanggal tidak diketahui dan sudah lama"


def test_estimate_date_from_url_pola_bulan():
    d = estimate_date_from_url("https://x.example/files/pengumuman/2026/mei/a.pdf")
    assert d == date(2026, 5, 1)
    assert estimate_date_from_url("https://x.example/tanpa-pola.pdf") is None


def test_tidak_diketahui_dikirim_bila_posting_baru():
    # Tidak ada tutup, tapi posting dalam 45 hari terakhir -> dikirim.
    it = _item(posted="2026-10-13")
    it.status = compute_status(it, date(2026, 10, 23))
    assert it.status == STATUS_UNKNOWN
    send_ok, _ = report_decision(it, date(2026, 10, 23))
    assert send_ok


def test_tidak_diketahui_dibuang_bila_posting_lama():
    it = _item(posted="2026-08-01")  # > 45 hari sebelum 23 Okt
    it.status = compute_status(it, date(2026, 10, 23))
    send_ok, reason = report_decision(it, date(2026, 10, 23))
    assert not send_ok
    assert reason == "tanggal tidak diketahui dan sudah lama"
