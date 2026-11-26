"""Kontrak inbox browser untuk mode light dan portal publik baru."""

from dataclasses import replace
from datetime import date

import pytest

from conftest import FakeFetcher, read_fixture
from tenderbot.config import Bank, load_banks, load_keywords
from tenderbot.inbox import InboxLoadResult
from tenderbot.models import Item
from tenderbot.pipeline import run_light
from tenderbot.state import State

TODAY = date(2026, 11, 9)
KW = load_keywords()


def _btn() -> Bank:
    return Bank(
        name="BTN",
        aliases=["Bank Tabungan Negara", "BBTN"],
        group="bumn",
        access="public",
        sources=[],
        needs_js=True,
    )


def test_light_inbox_edc_diproses_dan_coverage_browser_dicatat(tmp_path):
    """Item browser light masuk jalur portal: filter, status, dan dedup."""
    inbox = InboxLoadResult(
        run_date=TODAY.isoformat(),
        mode="light",
        items=[],
        coverage_checked=["BTN"],
        coverage_failed=[{"bank": "Bank Lampung", "reason": "HTTP 403"}],
    )
    inbox.items.append(
        Item(
            bank="BTN",
            title="Pengadaan Mesin EDC Android untuk Kantor Cabang",
            url="https://www.btn.co.id/procurement/edc-2026",
            published="2026-11-09",
            source_type="portal",
            evidence="Pengadaan Mesin EDC Android",
        )
    )

    report = run_light(
        FakeFetcher({}), [_btn()], KW, State.load(tmp_path), TODAY,
        skip_news=True, inbox=inbox,
    )

    assert len(report.new_items) == 1
    assert report.new_items[0].source_type == "portal"
    assert report.checked == 1
    assert report.deferred_js == []
    assert ("Bank Lampung", "HTTP 403") in report.failed


def test_light_tanpa_inbox_tetap_sama(tmp_path):
    """Jalur lama light tidak berubah saat --inbox tidak dipakai."""
    first = run_light(
        FakeFetcher({}), [_btn()], KW, State.load(tmp_path / "first"), TODAY,
        skip_news=True,
    )
    explicit_none = run_light(
        FakeFetcher({}), [_btn()], KW, State.load(tmp_path / "second"), TODAY,
        skip_news=True, inbox=None,
    )

    assert first.checked == explicit_none.checked == 1
    assert first.candidates == explicit_none.candidates == 0
    assert first.failed == explicit_none.failed == []
    assert first.deferred_js == explicit_none.deferred_js


@pytest.mark.parametrize(
    ("bank_name", "url", "fixture"),
    [
        ("Bank Jatim", "https://eprocurement.bankjatim.co.id/", "bankjatim_eproc.html"),
        ("Bank Sultra", "https://e-tender.banksultra.co.id/", "banksultra_etender.html"),
    ],
)
def test_portal_baru_bank_jatim_dan_sultra_dikoleksi(
    tmp_path, bank_name, url, fixture
):
    """Kedua source baru dibaca kolektor HTML memakai fixture lokal kecil.

    Portal e-proc Bank Jatim dipindah ke kolektor browser laptop (needs_js)
    sejak 26 Nov 2026 karena selalu timeout dari runner GitHub. Parser HTML-nya
    tetap diuji di sini dengan needs_js dimatikan pada salinan source.
    """
    configured = {bank.name: bank for bank in load_banks()}[bank_name]
    source = next(item for item in configured.sources if item.url == url)
    if bank_name == "Bank Jatim":
        assert source.needs_js is True
        source = replace(source, needs_js=False)
    bank = Bank(
        name=configured.name,
        aliases=configured.aliases,
        group=configured.group,
        access=configured.access,
        sources=[source],
    )

    report = run_light(
        FakeFetcher({url: (200, read_fixture(fixture))}), [bank], KW,
        State.load(tmp_path), TODAY, skip_news=True,
    )

    assert report.source_candidates == [(f"{bank_name} (html)", 1)]
    assert report.passed_filter == 1
    assert len(report.dropped) == 1
    assert "EDC" in report.dropped[0][1]


def test_portal_eproc_bank_jatim_ditunda_ke_browser(tmp_path):
    """Mode light melewati portal e-proc Bank Jatim; halaman lelang utama tetap dibaca."""
    configured = {bank.name: bank for bank in load_banks()}["Bank Jatim"]
    main_url = "https://www.bankjatim.co.id/id/informasi/lelang-pengadaan"
    eproc_url = "https://eprocurement.bankjatim.co.id/"
    by_url = {s.url: s for s in configured.sources}
    assert by_url[main_url].needs_js is False
    assert by_url[eproc_url].needs_js is True

    report = run_light(
        FakeFetcher({main_url: (200, "<html><body></body></html>")}),
        [configured], KW, State.load(tmp_path), TODAY, skip_news=True,
    )

    assert any(eproc_url in note for note in report.deferred_js)
    assert all(eproc_url not in name for name, _ in report.failed)
