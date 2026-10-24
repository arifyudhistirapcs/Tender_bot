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
from tenderbot.http_client import AccessError

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


class _FeedFail403Gdelt429(FakeFetcher):
    """Feed media -> 403; GDELT -> 429 (selalu). Menguji cakupan jujur."""

    def __init__(self, feed_url):
        super().__init__({})
        self._feed_url = feed_url
        from tenderbot.http_client import FetchResult
        self._FetchResult = FetchResult

    def fetch(self, url, bypass_robots=False):
        self.calls.append(url)
        if url == self._feed_url:
            raise AccessError("HTTP 403 (akses ditolak)")
        if "gdeltproject.org" in url:
            raise AccessError("HTTP 429 (rate limited)")
        raise AccessError("gagal: tidak ada rute")


def test_cakupan_jujur_feed_403_plus_gdelt_429(tmp_path):
    """Fix cakupan jujur: feed 403 + GDELT 429 -> TIDAK ada bank tercakup,
    bank masuk failed, dan pesan tidak mengaku 'semua sumber bisa diakses'."""
    from tenderbot.gchat import build_message
    from tenderbot.http_client import AccessError as _AE  # noqa: F401

    banks = [_bank_sumut()]
    ff = _FeedFail403Gdelt429(FEED.url)
    state = State.load(tmp_path)
    report = run_light(ff, banks, KW, state, TODAY, feeds=[FEED],
                       gdelt_sleep=_no_sleep)

    # Tidak ada bank yang jujur tercakup berita.
    assert report.news_checked_banks == []
    # Bank Sumut tercatat gagal, alasannya menyebut GDELT 429 dan feed gagal.
    assert report.news_failed_banks
    bank, reason = report.news_failed_banks[0]
    assert bank == "Bank Sumut"
    assert "429" in reason and "feed" in reason.lower()
    # GDELT + feed tercatat di daftar kegagalan sumber.
    assert report.news_gdelt_failure and "429" in report.news_gdelt_failure
    assert any(name == "detik Finance" for name, _ in report.news_feed_failures)
    assert any(n == "GDELT" for n, _ in report.failed)
    assert any(n.startswith("feed ") for n, _ in report.failed)

    # Pesan "tidak ada baru": TIDAK boleh mengaku semua bisa diakses, dan
    # harus mencantumkan kegagalan feed + GDELT.
    payload = build_message(report.new_items, report.checked, report.failed)
    text = payload["text"]
    assert "Semua sumber bisa diakses" not in text
    assert "GDELT" in text
    assert "feed detik Finance" in text


def test_semua_sumber_ok_pesan_semua_bisa_diakses(tmp_path):
    """Kebalikan: bila benar tidak ada kegagalan, barulah 'Semua sumber bisa
    diakses' boleh muncul."""
    from tenderbot.gchat import build_message
    banks = [_bank_sumut()]
    ff = _fetcher_for(banks)
    state = State.load(tmp_path)
    report = run_light(ff, banks, KW, state, TODAY, feeds=[FEED],
                       gdelt_sleep=_no_sleep)
    assert report.failed == []
    payload = build_message([], report.checked, report.failed)
    assert "Semua sumber bisa diakses" in payload["text"]
