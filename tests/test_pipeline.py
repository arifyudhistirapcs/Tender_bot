"""Uji integrasi pipeline: item sama tidak terkirim dua kali lintas run."""

from datetime import date
from urllib.parse import quote_plus

from conftest import FakeFetcher, read_fixture
from tenderbot.config import Bank, Keywords, NewsFeed, load_keywords
from tenderbot.collectors.rss import (
    build_gdelt_query, GDELT_DOC_URL, GDELT_TIMESPAN, GDELT_MAX_RECORDS,
)
from tenderbot.pipeline import run_light
from tenderbot.state import State

TODAY = date(2026, 10, 23)
KW = load_keywords()
FEED = NewsFeed(name="detik Finance", url="https://finance.detik.com/rss",
                domain="detik.com")


def _bank_sumut():
    return Bank(
        name="Bank Sumut",
        aliases=["Bank Sumut"],
        group="bpd",
        access="public",
        sources=[],  # hanya berita untuk uji ini
    )


def _gdelt_url(banks):
    q = build_gdelt_query(banks, KW.edc)
    return (f"{GDELT_DOC_URL}?query={quote_plus(q)}"
            f"&mode=artlist&format=json&timespan={GDELT_TIMESPAN}"
            f"&maxrecords={GDELT_MAX_RECORDS}")


def _fetcher_for(banks):
    """Rute feed media + GDELT untuk daftar bank ini."""
    routes = {
        FEED.url: (200, read_fixture("media_detik_finance.xml")),
        _gdelt_url(banks): (200, read_fixture("gdelt_banks.json")),
    }
    return FakeFetcher(routes)


def _no_sleep(_):
    return None


def test_item_baru_lalu_tidak_terkirim_dua_kali(tmp_path):
    banks = [_bank_sumut()]
    state = State.load(tmp_path)

    r1 = run_light(_fetcher_for(banks), banks, KW, state, TODAY,
                   feeds=[FEED], gdelt_sleep=_no_sleep)
    assert len(r1.new_items) >= 1
    assert any("Smart EDC" in i.title for i in r1.new_items)

    state.record_run(TODAY.isoformat(), "light", r1.checked, len(r1.failed),
                     len(r1.new_items))
    state.save()

    state2 = State.load(tmp_path)
    r2 = run_light(_fetcher_for(banks), banks, KW, state2, TODAY,
                   feeds=[FEED], gdelt_sleep=_no_sleep)
    assert len(r2.new_items) == 0


def test_semua_bank_disentuh_dan_cakupan_berita(tmp_path):
    banks = [_bank_sumut(),
             Bank(name="PermataBank", aliases=["PermataBank"],
                  group="swasta", access="blocked")]
    ff = _fetcher_for(banks)
    state = State.load(tmp_path)
    report = run_light(ff, banks, KW, state, TODAY, feeds=[FEED],
                       gdelt_sleep=_no_sleep)
    assert report.checked == 2  # kedua bank disentuh
    # Feed berhasil -> semua bank tercakup lewat berita, 0 gagal robots.
    assert "Bank Sumut" in report.news_checked_banks
    assert "PermataBank" in report.news_checked_banks
    assert report.news_failed_banks == []


def test_semua_sumber_berita_gagal_dicatat_per_bank(tmp_path):
    banks = [_bank_sumut()]
    # Feed 403 + GDELT tanpa rute -> semua gagal.
    ff = FakeFetcher({FEED.url: (403, "")})
    state = State.load(tmp_path)
    report = run_light(ff, banks, KW, state, TODAY, feeds=[FEED],
                       gdelt_sleep=_no_sleep)
    assert report.news_failed_banks  # dicatat per bank
    assert any("Bank Sumut" == b for b, _ in report.news_failed_banks)
