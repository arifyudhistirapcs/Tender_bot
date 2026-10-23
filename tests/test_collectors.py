"""Uji deteksi blokir dan kolektor memakai fixture lokal (tanpa internet)."""

import pytest

from conftest import FakeFetcher, read_fixture
from tenderbot.config import Bank, Source, NewsFeed
from tenderbot.collectors.html_list import collect_html_list
from tenderbot.collectors.rss import (
    collect_rss,
    collect_media_feeds,
    collect_gdelt,
    map_gdelt_to_banks,
    build_gdelt_query,
    parse_gdelt,
)
from tenderbot.http_client import AccessError, detect_block


EDC_TERMS = ["mesin edc", "smart edc", "edc android", "terminal edc",
             "electronic data capture"]
CREDIBLE = ["detik.com", "kontan.co.id", "kompas.com"]


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


# ---- Feed media kredibel ----

def _feed():
    return NewsFeed(name="detik Finance",
                    url="https://finance.detik.com/rss", domain="detik.com")


def test_media_feed_saring_bank_plus_edc():
    feed = _feed()
    ff = FakeFetcher({feed.url: (200, read_fixture("media_detik_finance.xml"))})
    banks = [
        Bank(name="Bank Sumut", aliases=["Bank Sumut"], group="bpd"),
        Bank(name="Bank Jatim", aliases=["Bank Jatim"], group="bpd"),
    ]
    items, feed_ok, failures = collect_media_feeds(
        ff, [feed], banks, EDC_TERMS, CREDIBLE
    )
    assert feed_ok[feed.url] is True
    assert failures == []
    titles = [i.title for i in items]
    # Dua item ber-EDC yang menyebut bank; item penghargaan + IHSG terbuang.
    assert any("Smart EDC" in t for t in titles)
    assert any("Bank Jatim" in t and "EDC" in t for t in titles)
    assert all("penghargaan" not in t for t in titles)
    assert all("IHSG" not in t for t in titles)
    # Feed diambil TEPAT sekali walau ada dua bank.
    assert ff.calls.count(feed.url) == 1
    # Domain detik kredibel -> tidak unverified.
    assert all(not i.unverified_source for i in items)


def test_media_feed_gagal_dicatat():
    feed = NewsFeed(name="Mati", url="https://mati.example/rss", domain="x")
    ff = FakeFetcher({feed.url: (403, "")})
    items, feed_ok, failures = collect_media_feeds(
        ff, [feed], [Bank(name="A", aliases=["A"])], EDC_TERMS, CREDIBLE
    )
    assert feed_ok[feed.url] is False
    assert items == []
    assert failures and "Mati" == failures[0][0]


# ---- GDELT ----

def test_gdelt_query_or_group_dan_sourcecountry():
    banks = [Bank(name="BNI", aliases=["Bank Negara Indonesia", "BBNI"]),
             Bank(name="Bank Jatim", aliases=["Bank Jatim"])]
    q = build_gdelt_query(banks, EDC_TERMS)
    assert q.startswith("(")
    assert "Bank Negara Indonesia" in q
    assert " OR " in q
    assert "EDC" in q
    assert "sourcecountry:ID" in q


def test_parse_gdelt_label_unverified():
    items = parse_gdelt(read_fixture("gdelt_banks.json"), CREDIBLE)
    by_domain = {i.media_name: i for i in items}
    # kontan kredibel, blog tak dikenal -> unverified.
    assert by_domain["kontan.co.id"].unverified_source is False
    assert by_domain["blogtender.example.com"].unverified_source is True
    # seendate -> tanggal ISO.
    assert by_domain["kontan.co.id"].published == "2026-10-13"


def test_gdelt_collect_dan_map_ke_bank():
    banks = [
        Bank(name="Bank Sumut", aliases=["Bank Sumut"], group="bpd"),
        Bank(name="Bank Jatim", aliases=["Bank Jatim"], group="bpd"),
    ]
    # Satu kelompok -> satu request; rute cocokkan via prefix.
    calls = {"n": 0}
    captured = {}

    def fake_sleep(_):
        calls["n"] += 1

    # Bangun URL yang sama seperti kolektor untuk dirutekan FakeFetcher.
    from urllib.parse import quote_plus
    from tenderbot.collectors.rss import (
        GDELT_DOC_URL, GDELT_TIMESPAN, GDELT_MAX_RECORDS,
    )
    q = build_gdelt_query(banks, EDC_TERMS)
    url = (f"{GDELT_DOC_URL}?query={quote_plus(q)}"
           f"&mode=artlist&format=json&timespan={GDELT_TIMESPAN}"
           f"&maxrecords={GDELT_MAX_RECORDS}")
    ff = FakeFetcher({url: (200, read_fixture("gdelt_banks.json"))})
    raw, ok, err = collect_gdelt(ff, banks, EDC_TERMS, CREDIBLE, sleep=fake_sleep)
    assert ok and err is None
    # Satu kelompok bank (<=8) -> tidak ada jeda antar-request.
    assert calls["n"] == 0
    linked, covered = map_gdelt_to_banks(raw, banks)
    assert "Bank Sumut" in covered
    assert "Bank Jatim" in covered
    # Artikel tanpa bank ("Ekonomi digital...") tidak tertaut.
    assert all(i.bank in ("Bank Sumut", "Bank Jatim") for i in linked)


def test_gdelt_semua_gagal():
    banks = [Bank(name="A", aliases=["A"])]
    ff = FakeFetcher({})  # tidak ada rute -> AccessError
    raw, ok, err = collect_gdelt(ff, banks, EDC_TERMS, CREDIBLE, sleep=lambda _: None)
    assert raw == []
    assert ok is False
    assert err
