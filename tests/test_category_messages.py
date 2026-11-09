"""Uji pesan bisnis dan laporan detail per kategori tender."""

from tenderbot.gchat import build_message
from tenderbot.models import Item, fingerprint
from tenderbot.pipeline import RunReport
from tenderbot.report import ReportContext, build_report_json, build_report_md


def _item(category: str, status: str = "berjalan") -> Item:
    item = Item(
        bank=f"Bank {category}",
        title=f"Pengadaan {category}",
        url=f"https://example.test/{category}",
        category=category,
        status=status,
    )
    item.fingerprint = fingerprint(item.bank, item.title, item.url)
    return item


def test_pembuka_campuran_dan_urutan_kartu_sesuai_kontrak():
    alih_data = _item("alih_data", "akan_dibuka")
    edc = _item("edc")
    alih_daya = _item("alih_daya")

    payload = build_message([alih_data, edc, alih_daya], 3)

    assert payload["text"] == (
        "Info tender: EDC 1 berjalan, 0 akan dibuka; "
        "alih daya 1 berjalan, 0 akan dibuka; "
        "alih data 0 berjalan, 1 akan dibuka."
    )
    titles = [card["card"]["header"]["title"] for card in payload["cardsV2"]]
    assert titles == ["Tender EDC", "Tender Alih Daya", "Tender Alih Data"]


def test_pesan_kosong_menyebut_semua_kategori():
    assert build_message([], 9)["text"] == (
        "Tidak ada info tender EDC, alih daya, atau alih data baru. (9 bank dipantau)"
    )


def test_laporan_dikelompokkan_dan_meringkas_per_kategori():
    report = RunReport(run_date="2026-11-09", mode="light", checked=3)
    report.new_items = [_item("alih_data"), _item("edc"), _item("alih_daya")]
    report.ongoing_count = 3
    context = ReportContext(dry_run=True)

    markdown = build_report_md(report, context)
    data = build_report_json(report, context)

    assert "EDC 1, alih daya 1, alih data 1" in markdown
    assert markdown.index("EDC:") < markdown.index("Alih daya:") < markdown.index("Alih data:")
    assert data["counts"]["categories"] == {"edc": 1, "alih_daya": 1, "alih_data": 1}