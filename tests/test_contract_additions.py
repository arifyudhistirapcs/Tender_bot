"""Uji tambahan kontrak koordinator: needs_js dan credible_news_domains."""

from datetime import date

from conftest import FakeFetcher, read_fixture
from tenderbot.config import Bank, Source, load_banks, load_keywords
from tenderbot.collectors.rss import GOOGLE_NEWS_RSS, build_news_query
from tenderbot.models import is_credible_domain, host_of
from tenderbot.pipeline import run_light, _label_media
from tenderbot.state import State
from urllib.parse import quote

TODAY = date(2026, 10, 23)
KW = load_keywords()


def test_credible_domains_termuat():
    assert "kompas.com" in KW.credible_news_domains
    assert len(KW.credible_news_domains) >= 10


def test_is_credible_subdomain():
    assert is_credible_domain("https://www.kompas.com/x", KW.credible_news_domains)
    assert is_credible_domain("https://bisnis.com/y", KW.credible_news_domains)
    assert not is_credible_domain("https://blogspot.example/z", KW.credible_news_domains)
    # Tidak tertipu domain yang hanya berakhiran mirip.
    assert not is_credible_domain("https://evilkompas.com/x", KW.credible_news_domains)


def test_host_of():
    assert host_of("https://www.Kompas.com:443/a") == "www.kompas.com"


def test_label_media_unverified():
    from tenderbot.models import Item
    it = Item(bank="X", title="t", url="https://news.google.com/rss/articles/abc",
              media_name="Blog Tak Dikenal", media_url="https://blog.example/post")
    _label_media(it, KW)
    assert it.unverified_source
    assert it.media_name == "Blog Tak Dikenal"


def test_label_media_kredibel():
    from tenderbot.models import Item
    it = Item(bank="X", title="t", url="https://news.google.com/rss/articles/abc",
              media_name="Kompas", media_url="https://www.kompas.com/post")
    _label_media(it, KW)
    assert not it.unverified_source


def test_banks_yaml_memuat_needs_js_dan_vendor_url():
    banks = {b.name: b for b in load_banks()}
    assert banks["bank bjb"].needs_js is True
    assert banks["Bank Jateng"].needs_js is True
    assert banks["Bank Kalbar"].needs_js is True
    # Field vendor_registration_url ada (boleh kosong).
    assert hasattr(banks["BRI"], "vendor_registration_url")


def test_needs_js_source_dilewati_dan_dicatat(tmp_path):
    # Bank public dengan satu source needs_js: harus dilewati, dicatat deferred.
    bank = Bank(
        name="Bank JS", aliases=["Bank JS"], group="bpd", access="public",
        sources=[Source(url="https://js.example/list", type="html", needs_js=True)],
    )
    # Fetcher tanpa rute: bila source TIDAK dilewati, akan muncul di failed.
    q = build_news_query(bank, KW.edc)
    url_news = GOOGLE_NEWS_RSS.format(query=quote(q))
    ff = FakeFetcher({url_news: (200, "<rss><channel></channel></rss>")})
    state = State.load(tmp_path)
    report = run_light(ff, [bank], KW, state, TODAY)
    assert any("Bank JS" in d and "browser" in d for d in report.deferred_js)
    # URL source needs_js tidak pernah di-fetch.
    assert "https://js.example/list" not in ff.calls
