"""Uji integrasi pipeline: item sama tidak terkirim dua kali lintas run."""

from datetime import date

from conftest import FakeFetcher, read_fixture
from tenderbot.config import Bank, Keywords, load_keywords
from tenderbot.collectors.rss import GOOGLE_NEWS_RSS, build_news_query
from tenderbot.pipeline import run_light
from tenderbot.state import State
from urllib.parse import quote

TODAY = date(2026, 10, 23)
KW = load_keywords()


def _bank_sumut():
    return Bank(
        name="Bank Sumut",
        aliases=["Bank Sumut"],
        group="bpd",
        access="public",
        sources=[],  # hanya berita untuk uji ini
    )


def _fetcher_for(bank):
    q = build_news_query(bank, KW.edc)
    url = GOOGLE_NEWS_RSS.format(query=quote(q))
    return FakeFetcher({url: (200, read_fixture("googlenews_banksumut.xml"))})


def test_item_baru_lalu_tidak_terkirim_dua_kali(tmp_path):
    bank = _bank_sumut()
    state = State.load(tmp_path)

    # Run pertama: menemukan tender Smart EDC baru.
    r1 = run_light(_fetcher_for(bank), [bank], KW, state, TODAY)
    assert len(r1.new_items) == 1
    assert "Smart EDC" in r1.new_items[0].title

    # Simpan state seperti run sukses nyata.
    state.record_run(TODAY.isoformat(), "light", r1.checked, len(r1.failed), 1)
    state.save()

    # Run kedua (state dimuat ulang): item yang sama sudah seen -> tidak baru.
    state2 = State.load(tmp_path)
    r2 = run_light(_fetcher_for(bank), [bank], KW, state2, TODAY)
    assert len(r2.new_items) == 0


def test_semua_bank_disentuh_dan_gagal_dicatat(tmp_path):
    bank_ok = _bank_sumut()
    bank_blocked = Bank(name="PermataBank", aliases=["PermataBank"],
                        group="swasta", access="blocked")
    # Fetcher hanya tahu URL berita Bank Sumut; PermataBank -> gagal rute.
    q = build_news_query(bank_ok, KW.edc)
    url_ok = GOOGLE_NEWS_RSS.format(query=quote(q))
    ff = FakeFetcher({url_ok: (200, read_fixture("googlenews_banksumut.xml"))})

    state = State.load(tmp_path)
    report = run_light(ff, [bank_ok, bank_blocked], KW, state, TODAY)
    assert report.checked == 2  # kedua bank disentuh
    assert any("PermataBank" in name for name, _ in report.failed)
