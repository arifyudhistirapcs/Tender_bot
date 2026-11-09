"""Regression tests for the 10 Nov date, status, and category contract."""

from datetime import date

from tenderbot.config import load_keywords
from tenderbot.dedup import is_near_duplicate
from tenderbot.enrich import extract_fields
from tenderbot.filters import evaluate
from tenderbot.gchat import build_message
from tenderbot.models import Item, normalize_text
from tenderbot.pipeline import RunReport, process_candidates
from tenderbot.state import State

TODAY = date(2026, 11, 10)
KW = load_keywords()

BSI_SCHEDULE = """
Pendaftaran Peserta Prakualifikasi Perusahaan yang memenuhi persyaratan point 1
atas dan berminat untuk mengikuti proses prakualifikasi ini agar memperhatikan
jadwal dan ketentuan sebagai berikut: a. Pengambilan Dokumen Prakualifikasi:
Hari/Tanggal: Jumat s.d Rabu, 30 Oktober 2026 s.d 4 November 2026 b. Pemasukan
Hardcopy dan Softcopy Dokumen Prakualifikasi: Hari/Tanggal: Rabu s.d Senin,
4 November 2026 s.d 6 November 2026 d. Tempat dan Waktu Pemasukan Dokumen
Prakualifikasi: Waktu : Pukul 09.00 s.d 15.00 WIB Tempat : Procurement & Fixed
Aset Group (PFA) - PT. Bank Syariah Indonesia
"""


def test_a_bsi_schedule_extracts_dates_and_real_place():
    fields = extract_fields(BSI_SCHEDULE)
    assert fields["reg_open"] == "2026-10-30"
    assert fields["reg_close"] == "2026-11-04"
    assert fields["submit_close"] == "2026-11-06"
    assert fields["reg_place"].startswith("Procurement & Fixed Aset Group")


def test_b_detail_text_enriches_only_after_title_filter_then_closes(tmp_path):
    item = Item(
        bank="BSI",
        title='Pengadaan "Penyedia Jasa Tenaga Alih Daya (PPJ TAD) Tahun 2027"',
        url="https://example.test/bsi-ppj",
        published="2026-10-30",
        source_type="portal",
        detail_text=BSI_SCHEDULE,
        attachment_url="https://example.test/ppj.pdf",
    )
    report = RunReport(run_date=TODAY.isoformat(), mode="light")
    process_candidates([item], KW, State.load(tmp_path), TODAY, TODAY.isoformat(), report, enrich=False)
    assert item.submit_close == "2026-11-06"
    assert ("BSI", item.title, "sudah tutup") in report.dropped


def test_c_result_announcement_closes_matching_tender_same_bank(tmp_path):
    tender = Item(
        bank="Bank Papua",
        title="Lelang Pekerjaan Pengadaan Outsourcing Jasa Cleaning Services Bank Papua KC Timika",
        url="https://example.test/tender",
        published="2026-10-19",
        source_type="portal",
    )
    result = Item(
        bank="Bank Papua",
        title="Hasil Koreksi Aritmatik Lelang Pengadaan Outsourcing Jasa Cleaning Services Bank Papua KC Timika",
        url="https://example.test/result",
        published="2026-11-01",
        source_type="portal",
    )
    report = RunReport(run_date=TODAY.isoformat(), mode="light")
    process_candidates([tender, result], KW, State.load(tmp_path), TODAY, TODAY.isoformat(), report, enrich=False)
    assert ("Bank Papua", tender.title, "sudah ada pengumuman hasil") in report.dropped


def test_d_near_duplicate_keeps_other_branches_and_packages_separate():
    waisai = Item(
        bank="Bank Papua",
        title="Lelang Pengadaan Outsourcing Jasa Keamanan Bank Papua KC Waisai",
        url="https://example.test/waisai",
        published="2026-11-03",
    )
    sorong = "Lelang Pengadaan Outsourcing Jasa Keamanan Bank Papua KCU Sorong"
    package_two = Item(
        bank="Bank Papua",
        title="Pengadaan Mesin EDC Paket 2 Tahun 2027",
        url="https://example.test/2",
        published="2026-11-03",
    )
    package_one = "Pengadaan Mesin EDC Paket 1 Tahun 2027"
    seen = [("Bank Papua", normalize_text(sorong), "2026-11-03")]
    assert not is_near_duplicate(waisai, seen, TODAY)
    seen = [("Bank Papua", normalize_text(package_one), "2026-11-03")]
    assert not is_near_duplicate(package_two, seen, TODAY)


def test_e_unknown_date_has_honest_card_label_and_opening():
    item = Item(
        bank="Bank Papua",
        title="Pengadaan Outsourcing Jasa Keamanan KC Waisai",
        url="https://example.test/waisai",
        category="alih_daya",
        status="tidak_diketahui",
    )
    payload = build_message([item], 1)
    assert payload["text"] == "Info tender: alih daya 0 berjalan, 0 akan dibuka, 1 tanggal belum diketahui."
    rows = payload["cardsV2"][0]["card"]["sections"][0]["widgets"]
    assert any(row.get("decoratedText", {}).get("text") == "Tanggal tutup belum diketahui" for row in rows)


def test_f_supplied_non_portal_alih_category_is_reassessed():
    item = Item(
        bank="Bank Contoh",
        title="Pengadaan Jasa Khusus",
        url="https://example.test/news",
        source_type="berita",
        category="alih_data",
    )
    verdict = evaluate(item, KW, TODAY)
    assert not verdict.passed
    assert item.category is None
