"""Uji kategori EDC, alih daya, alih data, dan pengumuman hasil."""

from datetime import date

from tenderbot.config import load_keywords
from tenderbot.filters import evaluate
from tenderbot.models import Item
from tenderbot.status import STATUS_CLOSED, compute_status, report_decision


TODAY = date(2026, 11, 9)
KEYWORDS = load_keywords()


def _item(title: str, *, source_type: str = "portal", evidence: str = "") -> Item:
    return Item(
        bank="Bank Contoh",
        title=title,
        url="https://example.test/tender",
        published="2026-10-30",
        source_type=source_type,
        evidence=evidence,
    )


def test_bsi_ppj_tad_masuk_alih_daya():
    item = _item('Pengadaan "Penyedia Jasa Tenaga Alih Daya (PPJ TAD) Tahun 2027"')

    assert evaluate(item, KEYWORDS, TODAY).passed
    assert item.category == "alih_daya"


def test_lisensi_firewall_checkpoint_tidak_masuk_kategori():
    item = _item("Pengadaan Lisensi Firewall Checkpoint")

    result = evaluate(item, KEYWORDS, TODAY)
    assert not result.passed
    assert item.category is None
    assert result.reason == "tidak ada kata EDC/alih daya/alih data"


def test_pengumuman_pemenang_alih_daya_ditutup_dengan_alasan_hasil():
    item = _item("Pengumuman Pemenang Tender Penyedia Jasa Tenaga Kerja Alih Daya Cleaning Service")

    assert evaluate(item, KEYWORDS, TODAY).passed
    item.status = compute_status(item, TODAY)
    assert item.status == STATUS_CLOSED
    assert report_decision(item, TODAY) == (False, "pengumuman hasil")


def test_hasil_koreksi_outsourcing_ditutup_dengan_alasan_hasil():
    item = _item("Hasil Koreksi Aritmatik Lelang Pengadaan Outsourcing Jasa Driver")

    assert evaluate(item, KEYWORDS, TODAY).passed
    item.status = compute_status(item, TODAY)
    assert item.status == STATUS_CLOSED
    assert report_decision(item, TODAY) == (False, "pengumuman hasil")


def test_berita_rss_outsourcing_tidak_lolos():
    item = _item("Tender Pengadaan Outsourcing Call Center", source_type="berita")

    result = evaluate(item, KEYWORDS, TODAY)
    assert not result.passed
    assert item.category is None


def test_edc_tetap_prioritas_di_atas_kategori_baru_dan_memakai_evidence():
    item = _item("Pengadaan Alih Data", evidence="terminal EDC")

    assert evaluate(item, KEYWORDS, TODAY).passed
    assert item.category == "edc"