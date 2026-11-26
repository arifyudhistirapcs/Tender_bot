"""Uji perbaikan: penanda status di judul, judul nama-bank, kata buang sosialisasi."""

from datetime import date

import pytest

from tenderbot.config import load_keywords
from tenderbot.enrich import choose_title, is_bank_name_only
from tenderbot.filters import evaluate
from tenderbot.models import Item
from tenderbot.status import STATUS_CLOSED, STATUS_ONGOING, STATUS_UNKNOWN, compute_status

TODAY = date(2026, 11, 26)
KW = load_keywords()


def _st(title):
    return compute_status(Item(bank="BNI", title=title, url="https://x.example/"), TODAY)


@pytest.mark.parametrize("title", [
    "IT Pengadaan Server Berbasis ARM pada Data Center BNI 24 November 2026 25 November 2026 CLOSED",
    "IT Pengadaan Konsolidasi Maintenance Storage BNI Cloud DC dan DRC BNI 12 Oktober 2026 13 Oktober 2026 CLOSED",
    "Pengadaan Server (CLOSED)",
    "Pengadaan Server (Ditutup)",
    "Pengadaan Server Selesai",
])
def test_penanda_tutup(title):
    assert _st(title) == STATUS_CLOSED


def test_penanda_open_berjalan():
    t = "IT Pengadaan Perangkat Network untuk Peningkatan Kapasitas Production, DMZ 23 November 2026 26 November 2026 OPEN"
    assert _st(t) == STATUS_ONGOING
    assert _st("Pengadaan Server (OPEN)") == STATUS_ONGOING


def test_penanda_open_kalah_oleh_tanggal_tutup_lampau():
    it = Item(bank="BNI", title="Pengadaan Server (OPEN)", url="https://x.example/",
              submit_close="2026-11-01")
    assert compute_status(it, TODAY) == STATUS_CLOSED


def test_kata_biasa_di_tengah_judul_tidak_terbaca():
    assert _st("Pengadaan Sistem Closed Loop Payment") == STATUS_UNKNOWN
    assert _st("Pengadaan Open Banking Platform Server") == STATUS_UNKNOWN


JUDUL_BALI = "PT Bank Pembangunan Daerah Bali"
NAMA_BALI = ["BPD Bali", "BPD Bali", "Bank Pembangunan Daerah Bali"]


def test_judul_nama_bank_dikenali():
    assert is_bank_name_only(JUDUL_BALI, NAMA_BALI)
    assert not is_bank_name_only(
        "Pengumuman Tender Pengadaan License MIMIX Bank BPD Bali", NAMA_BALI)


def test_choose_title_tolak_nama_bank():
    terpotong = "Unit Pengadaan PT Bank Pembangunan Daerah Bali akan melaksanakan tender..."
    assert choose_title(terpotong, JUDUL_BALI, NAMA_BALI) == terpotong
    # Perilaku lama tetap: judul detail sungguhan menggantikan judul terpotong.
    assert choose_title("Pengadaan Server ...", "Pengadaan Server Baru", NAMA_BALI) == "Pengadaan Server Baru"


def test_sosialisasi_ditolak_dan_contoh_kontrak_tidak_terkena():
    t = ("Pengumuman Undangan Sosialisasi Penerapan Master Data dan Bimbingan Teknis "
         "Penginputan Master Data Produk Kategori Perangkat Lunak (Software) pada Katalog Elektronik Versi 6")
    it = Item(bank="INAPROC", title=t, url="https://x.example/", published="2026-11-18",
              source_type="portal")
    res = evaluate(it, KW, TODAY)
    assert not res.passed and "sosialisasi" in res.reason
    ok = Item(bank="BTN", title="Pengadaan Maintenance Server Fisik Berbasis Prosesor Intel",
              url="https://x.example/2", published="2026-11-10", source_type="portal")
    assert evaluate(ok, KW, TODAY).passed
