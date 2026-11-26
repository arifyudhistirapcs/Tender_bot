"""Uji kategori aplikasi_it dan perluasan alih_daya."""

from datetime import date

import pytest

from tenderbot.config import load_keywords
from tenderbot.filters import evaluate
from tenderbot.gchat import build_message
from tenderbot.models import Item, fingerprint
from tenderbot.pipeline import RunReport
from tenderbot.report import ReportContext, build_report_md

KW = load_keywords()
TODAY = date(2026, 11, 26)


def _item(title, source_type="portal", category=None, evidence="", bank="Bank X"):
    return Item(bank=bank, title=title, url="https://x.example/1",
                published="2026-11-10", source_type=source_type,
                category=category, evidence=evidence)


@pytest.mark.parametrize("title", [
    "Pengadaan Aplikasi Jatim Inventory Management System",
    "Maintenance Local Support Mesin IBM Power E980 dan Hardware Pendukung",
    "Pengadaan Alternatif Layanan E-KYC Digital Verification",
    "Pengadaan Ulang Sertifikat Digital Secure Socket Layer (SSL)",
    "Pengadaan Maintenance Server Fisik Berbasis Prosesor Intel",
    "Pengadaan Perangkat PC & Laptop TKDN Kebutuhan SMBCI Project Alpa",
    "Pengadaan 1 (SATU) Unit Server Baremetal Data Warehouse",
])
def test_judul_nyata_lolos_aplikasi_it(title):
    it = _item(title)
    assert evaluate(it, KW, TODAY).passed
    assert it.category == "aplikasi_it"


@pytest.mark.parametrize("title", [
    "Pengadaan Jasa Kontraktor Pekerjaan Renovasi dan Relayout KC Medan menjadi Digital Branch",
    "Pemasangan Panel Active Filter Harmonic pada Sistem Kelistrikan",
    "Pengadaan Kontraktor Design & Build Renovasi Digital Store KC Jakarta Harmoni",
])
def test_judul_nyata_bukan_aplikasi_it(title):
    it = _item(title)
    assert not evaluate(it, KW, TODAY).passed or it.category is None


@pytest.mark.parametrize("title", [
    "Jasa Tenaga Kerja Bongkar Muat Barang Perkasan HCTS dan Arsip",
    "Pengadaan Perusahaan Penyedia Jasa Tenaga Alih Daya (TAD) Consumer Loan Marketing (CLM) dan Collection Kring Pensiunan",
    "Pengadaan Jasa Pemenuhan Tenaga Alih Daya (TAD) Superbuddy Tahun 2026-2027",
])
def test_alih_daya_diperluas(title):
    it = _item(title)
    assert evaluate(it, KW, TODAY).passed
    assert it.category == "alih_daya"


def test_edc_tetap_edc():
    it = _item("Pengadaan Sewa Beli Mesin Smart EDC", bank="Bank Sumut")
    assert evaluate(it, KW, TODAY).passed
    assert it.category == "edc"


def test_prioritas_alih_daya_atas_aplikasi_it():
    it = _item("Pengadaan Jasa Tenaga Alih Daya Help Desk Aplikasi")
    assert evaluate(it, KW, TODAY).passed
    assert it.category == "alih_daya"


def test_berita_aplikasi_bukan_aplikasi_it():
    it = _item("Pengadaan aplikasi baru bank digelar", source_type="berita")
    res = evaluate(it, KW, TODAY)
    assert not res.passed and it.category is None


def test_kategori_dari_inbox_berita_dinilai_ulang():
    it = _item("Pengadaan aplikasi baru", source_type="berita", category="aplikasi_it")
    assert not evaluate(it, KW, TODAY).passed


def _card_item():
    it = Item(bank="Bank Jatim", title="Pengadaan Aplikasi J-IMS", url="https://x.example/j",
              category="aplikasi_it", status="berjalan")
    it.fingerprint = fingerprint(it.bank, it.title, it.url)
    return it


def test_kartu_space_judul_aplikasi_it():
    payload = build_message([_card_item()], 5)
    assert payload["cardsV2"][0]["card"]["header"]["title"] == "Tender Aplikasi/IT"
    assert "aplikasi IT 1 berjalan" in payload["text"]


def test_teks_tidak_ada_tender_menyebut_aplikasi_it():
    assert "aplikasi/IT" in build_message([], 5)["text"]


def test_ringkasan_report_memuat_hitungan_aplikasi_it():
    report = RunReport(run_date="2026-11-26", mode="light", checked=3)
    report.new_items = [_card_item()]
    md = build_report_md(report, ReportContext(dry_run=True))
    assert "aplikasi IT 1" in md
    assert "Aplikasi/IT:" in md
