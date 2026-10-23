"""Uji tambahan kontrak koordinator: needs_js, credible_news_domains, label berita."""

from datetime import date
from urllib.parse import quote_plus

from conftest import FakeFetcher, read_fixture
from tenderbot.config import Bank, Source, NewsFeed, load_banks, load_keywords
from tenderbot.collectors.rss import (
    build_gdelt_query, parse_gdelt, GDELT_DOC_URL, GDELT_TIMESPAN, GDELT_MAX_RECORDS,
)
from tenderbot.models import is_credible_domain, host_of
from tenderbot.pipeline import run_light
from tenderbot.state import State

TODAY = date(2026, 10, 23)
KW = load_keywords()


def test_credible_domains_termuat():
    assert "kompas.com" in KW.credible_news_domains
    assert len(KW.credible_news_domains) >= 10


def test_is_credible_subdomain():
    assert is_credible_domain("https://www.kompas.com/x", KW.credible_news_domains)
    assert is_credible_domain("https://bisnis.com/y", KW.credible_news_domains)
    assert not is_credible_domain("https://blogspot.example/z", KW.credible_news_domains)
    assert not is_credible_domain("https://evilkompas.com/x", KW.credible_news_domains)


def test_host_of():
    assert host_of("https://www.Kompas.com:443/a") == "www.kompas.com"


def test_gdelt_item_unverified_dari_domain_luar():
    # Item berita GDELT dari domain di luar daftar kredibel -> unverified_source.
    items = parse_gdelt(read_fixture("gdelt_banks.json"), KW.credible_news_domains)
    by_domain = {i.media_name: i for i in items}
    assert by_domain["blogtender.example.com"].unverified_source is True


def test_gdelt_item_kredibel_tidak_unverified():
    items = parse_gdelt(read_fixture("gdelt_banks.json"), KW.credible_news_domains)
    by_domain = {i.media_name: i for i in items}
    assert by_domain["kontan.co.id"].unverified_source is False


def test_banks_yaml_memuat_needs_js_dan_vendor_url():
    banks = {b.name: b for b in load_banks()}
    assert banks["bank bjb"].needs_js is True
    assert banks["Bank Jateng"].needs_js is True
    assert banks["Bank Kalbar"].needs_js is True
    assert hasattr(banks["BRI"], "vendor_registration_url")


def test_needs_js_source_dilewati_dan_dicatat(tmp_path):
    # Bank public dengan satu source needs_js: harus dilewati, dicatat deferred.
    bank = Bank(
        name="Bank JS", aliases=["Bank JS"], group="bpd", access="public",
        sources=[Source(url="https://js.example/list", type="html", needs_js=True)],
    )
    feed = NewsFeed(name="detik", url="https://finance.detik.com/rss", domain="detik.com")
    q = build_gdelt_query([bank], KW.edc)
    gdelt_url = (f"{GDELT_DOC_URL}?query={quote_plus(q)}"
                 f"&mode=artlist&format=json&timespan={GDELT_TIMESPAN}"
                 f"&maxrecords={GDELT_MAX_RECORDS}")
    ff = FakeFetcher({
        feed.url: (200, "<rss><channel></channel></rss>"),
        gdelt_url: (200, '{"articles": []}'),
    })
    state = State.load(tmp_path)
    report = run_light(ff, [bank], KW, state, TODAY, feeds=[feed],
                       gdelt_sleep=lambda _: None)
    assert any("Bank JS" in d and "browser" in d for d in report.deferred_js)
    # URL source needs_js tidak pernah di-fetch.
    assert "https://js.example/list" not in ff.calls
