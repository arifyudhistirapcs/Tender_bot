"""Uji pembuangan judul terpotong yang menduplikasi judul utuh (BPD Bali)."""

from datetime import date

from tenderbot.config import load_keywords
from tenderbot.enrich import is_truncated_duplicate
from tenderbot.models import Item
from tenderbot.pipeline import RunReport, process_candidates
from tenderbot.state import State

MIMIX = ("Pengumuman Tender Dengan Pascakualifikasi Untuk Pengadaan License MIMIX "
         "Temporary dan Transfer License MIMIX Bank BPD Bali")
POTONG = ("Unit Pengadaan PT Bank Pembangunan Daerah Bali akan melaksanakan tender dengan "
          "pascakualifikasi untuk paket pekerjaan Pengadaan License MIMIX Temporary dan Tran...")
DB2 = ("Pengumuman Tender Dengan Pascakualifikasi Untuk Pengadaan Renewal License Maintenance "
       "Support Replikasi DB2 For 1 MIMIX Server IBM Power system 9 Bank BPD Bali")
POTONG_DB2 = ("Unit Pengadaan PT Bank Pembangunan Daerah Bali akan melaksanakan tender dengan "
              "pascakualifikasi untuk paket pekerjaan Pengadaan Renewal License Maintenance Support R...")
TANPA_PADANAN = ("Unit Pengadaan PT Bank Pembangunan Daerah Bali akan melaksanakan tender "
                 "pengadaan perangkat jaringan cabang baru wilayah timur dan ba...")


def test_cuplikan_bali_dibuang():
    assert is_truncated_duplicate(POTONG, [MIMIX, DB2])
    assert is_truncated_duplicate(POTONG_DB2, [MIMIX, DB2])


def test_awalan_murni_dibuang():
    assert is_truncated_duplicate("Pengadaan Renewal License Maintenance Support Repl\u2026",
                                  ["Pengadaan Renewal License Maintenance Support Replikasi DB2"])


def test_awalan_umum_bank_maluku_tidak_menyamakan_tender_berbeda():
    ppjt = ("PENGUMUMAN PELELANGAN PENGADAAN BARANG DAN/ATAU JASA PIHAK PENYEDIA JASA "
            "TEKNOLOGI INFORMASI (PPJT...")
    atm = "PENGUMUMAN PELELANGAN PENGADAAN BARANG DAN/ATAU JASA KARTU ATM/DEBIT TAHUN 2026 BANK MALUKU MALUT"
    assert not is_truncated_duplicate(ppjt, [atm])


def test_tanpa_padanan_atau_bukan_terpotong_tetap():
    assert not is_truncated_duplicate(TANPA_PADANAN, [MIMIX, DB2])
    assert not is_truncated_duplicate(MIMIX, [MIMIX, DB2])
    assert not is_truncated_duplicate(POTONG, [POTONG_DB2])  # padanan sendiri terpotong


def _it(title):
    return Item(bank="BPD Bali", title=title, url="https://www.bpdbali.co.id/pengumuman",
                published="2026-11-11", source_type="portal")


def test_pipeline_catat_dropped_dan_kirim_sisanya(tmp_path):
    report = RunReport(run_date="2026-11-26", mode="light")
    process_candidates([_it(MIMIX), _it(POTONG), _it(TANPA_PADANAN)],
                       load_keywords(), State.load(tmp_path), date(2026, 11, 26), "2026-11-26",
                       report, fetcher=None, enrich=False)
    assert (
        "BPD Bali", POTONG, "judul terpotong, duplikat item lain"
    ) in report.dropped
    titles = [i.title for i in report.new_items]
    assert MIMIX in titles and POTONG not in titles
    assert all(d[1] != TANPA_PADANAN for d in report.dropped if d[2].startswith("judul terpotong"))


def test_dua_tender_beda_di_halaman_daftar_sama_tetap_dikirim(tmp_path):
    """Bank Maluku Malut: dua tender IT berbeda memakai url /informasitender yang sama."""
    url = "https://www.bankmalukumalut.co.id/informasitender"
    software = ("PENGUMUMAN PEMILIHAN LANGSUNG/SELEKSI LANGSUNG PENGADAAN BARANG DAN/ATAU JASA "
                "PENGEMBANGAN SOFTWARE...")
    ppjt = ("PENGUMUMAN PELELANGAN PENGADAAN BARANG DAN/ATAU JASA PIHAK PENYEDIA JASA "
            "TEKNOLOGI INFORMASI (PPJT...")
    items = [
        Item(bank="Bank Maluku Malut", title=software, url=url, published="2026-10-23",
             source_type="portal"),
        # Tanggal dibuat baru: tender tanpa tanggal tutup yang sudah lama
        # sengaja dibuang oleh aturan status, bukan bagian uji ini.
        Item(bank="Bank Maluku Malut", title=ppjt, url=url, published="2026-11-20",
             source_type="portal"),
    ]
    report = RunReport(run_date="2026-11-26", mode="light")
    process_candidates(items, load_keywords(), State.load(tmp_path), date(2026, 11, 26),
                       "2026-11-26", report, fetcher=None, enrich=False)
    titles = [i.title for i in report.new_items]
    assert software in titles and ppjt in titles
