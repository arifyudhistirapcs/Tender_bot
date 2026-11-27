"""Anggaran waktu pengayaan detail: urutan prioritas, penghentian, tetap seen."""

from datetime import date

from conftest import FakeFetcher
from tenderbot import pipeline
from tenderbot.config import load_keywords
from tenderbot.models import Item
from tenderbot.pipeline import RunReport, enrich_priority_order, process_candidates
from tenderbot.state import State

KW = load_keywords()
TODAY = date(2026, 11, 26)

_TITLES = {
    "aplikasi_it": "Pengadaan Aplikasi Jatim Inventory Management System",
    "alih_daya": "Pengadaan Jasa Pemenuhan Tenaga Alih Daya (TAD) Superbuddy Tahun 2026-2027",
    "edc": "Pengadaan Mesin EDC Merchant",
}


def _item(n, category, published):
    return Item(bank=f"Bank {n}", title=_TITLES[category] + f" {n}",
                url=f"https://x{n}.example/detail", published=published,
                source_type="portal", category=category)


def _cats(items):
    return [it.category for it in items]


def test_urutan_prioritas_kategori_lalu_terbaru():
    items = [
        _item(1, "aplikasi_it", "2026-11-20"),
        _item(2, "alih_daya", "2026-11-01"),
        _item(3, "edc", "2026-11-02"),
        _item(4, "alih_daya", "2026-11-10"),
        _item(5, "aplikasi_it", "2026-11-25"),
    ]
    out = enrich_priority_order(items)
    assert [it.bank for it in out] == ["Bank 3", "Bank 4", "Bank 2", "Bank 5", "Bank 1"]


def test_anggaran_habis_item_sisa_tidak_diperkaya_tetap_seen(tmp_path, monkeypatch):
    items = [_item(1, "aplikasi_it", "2026-11-20"),
             _item(2, "edc", "2026-11-10"),
             _item(3, "alih_daya", "2026-11-15")]
    called = []
    clock = {"t": 0.0}

    def fake_enrich(item, fetcher, **kw):
        called.append(item.bank)
        clock["t"] += 100.0  # tiap pengayaan "memakan" 100 detik

    monkeypatch.setattr(pipeline, "enrich_item", fake_enrich)
    monkeypatch.setattr(pipeline.time, "monotonic", lambda: clock["t"])
    monkeypatch.setattr(pipeline, "ENRICH_BUDGET_SECONDS", 150.0)

    state = State.load(tmp_path)
    report = RunReport(run_date="2026-11-26", mode="light")
    process_candidates(items, KW, state, TODAY, "2026-11-26", report,
                       fetcher=FakeFetcher({}))

    # EDC dulu, lalu alih_daya (masih dalam anggaran 150 s setelah 100 s); aplikasi_it dilewati.
    assert called == ["Bank 2", "Bank 3"]
    assert report.notes == [
        "Catatan: pengayaan detail dihentikan setelah 150 detik; 1 item tidak diperkaya."
    ]
    # Item yang tidak diperkaya tetap dilaporkan dan ditandai seen.
    assert {it.bank for it in report.new_items} == {"Bank 1", "Bank 2", "Bank 3"}
    assert all(state.is_seen(it.fingerprint) for it in items)


def test_anggaran_cukup_tanpa_catatan(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(pipeline, "enrich_item",
                        lambda item, fetcher, **kw: called.append(item.bank))
    report = RunReport(run_date="2026-11-26", mode="light")
    process_candidates([_item(1, "edc", "2026-11-10")], KW, State.load(tmp_path), TODAY,
                       "2026-11-26", report, fetcher=FakeFetcher({}))
    assert called == ["Bank 1"]
    assert report.notes == []
