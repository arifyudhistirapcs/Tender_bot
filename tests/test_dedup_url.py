"""Uji dedup url sama dan akhiran metode pengadaan."""

from datetime import date

from tenderbot.dedup import _strip_method_suffix, is_near_duplicate, is_same_url_duplicate
from tenderbot.models import Item

URL = ("https://www.banksumut.co.id/jasa_barang/pengadaan-jasa-sentralisasi-kas-"
       "bank-sumut-wilayah-nias-kepada-perusahaan-pihak-ketiga/")
JUDUL = "Pengadaan Jasa Sentralisasi Kas Bank Sumut Wilayah Nias Kepada Perusahaan Pihak Ketiga"


def test_bank_sumut_url_sama_dan_akhiran_metode_duplikat():
    live = Item(bank="Bank Sumut", title=JUDUL, url=URL, published="")
    assert is_same_url_duplicate(live, [("Bank Sumut", URL)])
    seen = [("Bank Sumut", JUDUL + " (Pelelangan Umum Pascakualifikasi)", "2026-11-19")]
    assert is_near_duplicate(live, seen, date(2026, 11, 23))


def test_url_halaman_daftar_bersama_bukan_duplikat():
    for url in ("https://www.btn.co.id/en/Procurement/Procurement-List",
                "https://www.bankpapua.com/berita/pengumuman-lelang-33"):
        it = Item(bank="BTN", title="Pengadaan B", url=url, published="")
        assert not is_same_url_duplicate(it, [("BTN", url)]), url


def test_bank_beda_url_sama_bukan_duplikat():
    it = Item(bank="Bank Lain", title=JUDUL, url=URL, published="")
    assert not is_same_url_duplicate(it, [("Bank Sumut", URL)])


def test_akhiran_metode_dibuang_tender_ulang_tidak():
    assert _strip_method_suffix("Pengadaan X (Tender Ulang)") == "Pengadaan X (Tender Ulang)"
    assert _strip_method_suffix("Pengadaan X (Seleksi Umum)") == "Pengadaan X"
