"""Uji deteksi blokir dan kolektor memakai fixture lokal (tanpa internet)."""

import pytest

from conftest import FakeFetcher, read_fixture
from tenderbot.config import Bank, Source
from tenderbot.collectors.html_list import collect_html_list
from tenderbot.collectors.rss import collect_rss, collect_news, build_news_query
from tenderbot.http_client import AccessError, detect_block


def test_detect_block_403():
    assert detect_block(403, "apa saja")


def test_detect_block_request_rejected():
    html = read_fixture("blocked_request_rejected.html")
    assert detect_block(200, html)


def test_detect_block_bersih():
    assert detect_block(200, "<html>daftar tender</html>") is None


def test_fake_fetcher_blokir_jadi_access_error():
    ff = FakeFetcher({"https://blocked.example/": (200, read_fixture("blocked_request_rejected.html"))})
    with pytest.raises(AccessError):
        ff.fetch("https://blocked.example/")


def test_html_list_tangkap_smart_edc_buang_navigasi():
    url = "https://www.banksumut.co.id/archive-jasa-barang/"
    ff = FakeFetcher({url: (200, read_fixture("banksumut_archive.html"))})
    bank = Bank(name="Bank Sumut", group="bpd", access="public")
    res = collect_html_list(ff, bank, url)
    assert res.ok
    titles = [i.title for i in res.items]
    assert any("Smart Electronic Data Capture" in t for t in titles)
    # Navigasi (Beranda/English/Berikutnya) dan /lelang/ tidak ikut.
    assert all("Beranda" not in t for t in titles)
    urls = [i.url for i in res.items]
    assert all("/lelang/" not in u for u in urls)


def test_html_list_sumber_blokir():
    url = "https://blocked.example/arsip"
    ff = FakeFetcher({url: (403, "")})
    bank = Bank(name="X", access="public")
    res = collect_html_list(ff, bank, url)
    assert not res.ok
    assert "403" in res.error


def test_news_query_pakai_aliases_dan_edc():
    bank = Bank(name="BNI", aliases=["Bank Negara Indonesia", "BBNI"])
    q = build_news_query(bank, ["Smart EDC", "mesin EDC"])
    assert "Bank Negara Indonesia" in q
    assert "Smart EDC" in q


def test_news_collect_parse_rss():
    bank = Bank(name="Bank Sumut", aliases=["Bank Sumut"])
    # URL Google News dibangun kolektor; kita petakan URL apa pun lewat prefix.
    from urllib.parse import quote
    from tenderbot.collectors.rss import GOOGLE_NEWS_RSS
    q = build_news_query(bank, ["Smart EDC"])
    url = GOOGLE_NEWS_RSS.format(query=quote(q))
    ff = FakeFetcher({url: (200, read_fixture("googlenews_banksumut.xml"))})
    res = collect_news(ff, bank, ["Smart EDC"])
    assert res.ok
    assert any("Smart EDC" in i.title for i in res.items)
