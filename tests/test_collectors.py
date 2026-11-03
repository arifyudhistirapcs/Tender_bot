"""Uji deteksi blokir dan kolektor memakai fixture lokal (tanpa internet)."""

from datetime import date

import pytest

from conftest import FakeFetcher, read_fixture
from tenderbot.config import Bank, Source, NewsFeed, load_banks, load_keywords
from tenderbot.collectors.html_list import collect_html_list
from tenderbot.gchat import build_message
from tenderbot.pipeline import run_light
from tenderbot.state import State
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
    raw, covered_query, err = collect_gdelt(ff, banks, EDC_TERMS, CREDIBLE, sleep=fake_sleep)
    assert err is None
    # Kueri kelompok berhasil -> kedua bank tercakup (sumber benar-benar dikueri).
    assert covered_query == {"Bank Sumut", "Bank Jatim"}
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
    raw, covered_query, err = collect_gdelt(ff, banks, EDC_TERMS, CREDIBLE, sleep=lambda _: None)
    assert raw == []
    assert covered_query == set()  # tidak ada kelompok yang berhasil
    assert err


# ---- GDELT 429: retry dengan backoff ----

class _FlakyGdeltFetcher(FakeFetcher):
    """Melayani 429 untuk beberapa percobaan pertama, lalu 200.

    `fail_times` = berapa kali pertama membalas 429 sebelum sukses.
    """

    def __init__(self, url, body, fail_times):
        super().__init__({})
        self._url = url
        self._body = body
        self._fail_times = fail_times
        self._n = 0
        from tenderbot.http_client import FetchResult
        self._FetchResult = FetchResult

    def fetch(self, url, bypass_robots=False):
        self.calls.append(url)
        self._n += 1
        if self._n <= self._fail_times:
            raise AccessError("HTTP 429 (rate limited)")
        return self._FetchResult(url=url, status=200, text=self._body,
                                 content=self._body.encode("utf-8"),
                                 content_type="application/json")


def _gdelt_url_for(banks):
    from urllib.parse import quote_plus
    from tenderbot.collectors.rss import (
        GDELT_DOC_URL, GDELT_TIMESPAN, GDELT_MAX_RECORDS,
    )
    q = build_gdelt_query(banks, EDC_TERMS)
    return (f"{GDELT_DOC_URL}?query={quote_plus(q)}"
            f"&mode=artlist&format=json&timespan={GDELT_TIMESPAN}"
            f"&maxrecords={GDELT_MAX_RECORDS}")


def test_gdelt_429_lalu_sukses_setelah_backoff():
    banks = [Bank(name="Bank Sumut", aliases=["Bank Sumut"])]
    url = _gdelt_url_for(banks)
    body = read_fixture("gdelt_banks.json")
    slept: list[float] = []
    # Gagal 429 sekali, lalu sukses pada percobaan kedua (backoff 10 detik).
    ff = _FlakyGdeltFetcher(url, body, fail_times=1)
    raw, covered, err = collect_gdelt(
        ff, banks, EDC_TERMS, CREDIBLE, sleep=lambda s: slept.append(s),
    )
    assert err is None
    assert covered == {"Bank Sumut"}
    assert len(raw) >= 1
    assert slept == [10.0]           # satu backoff 10 detik
    assert ff._n == 2                # satu gagal + satu sukses


def test_gdelt_429_menyerah_setelah_dua_retry():
    banks = [Bank(name="Bank Sumut", aliases=["Bank Sumut"])]
    url = _gdelt_url_for(banks)
    slept: list[float] = []
    # Selalu 429 -> 1 percobaan awal + 2 retry (10, 20 detik), lalu menyerah.
    ff = _FlakyGdeltFetcher(url, "{}", fail_times=99)
    raw, covered, err = collect_gdelt(
        ff, banks, EDC_TERMS, CREDIBLE, sleep=lambda s: slept.append(s),
    )
    assert raw == []
    assert covered == set()
    assert err and "429" in err
    assert slept == [10.0, 20.0]     # dua backoff, maksimal 2 retry
    assert ff._n == 3


@pytest.mark.parametrize(
    ("bank_name", "url", "fixture", "expected_title", "expected_date"),
    [
        (
            "BPD Bali",
            "https://www.bpdbali.co.id/pengumuman",
            "bpdbali_pengumuman.html",
            "Pengumuman Pemenang Tender Pengadaan Mesin EDC Bank BPD Bali",
            "2026-10-28",
        ),
        (
            "Bankaltimtara",
            "https://www.bankaltimtara.co.id/id/info/lelang",
            "bankaltimtara_lelang.html",
            "Pengumuman Pemenang Tender Pengadaan Mesin EDC Bankaltimtara",
            "2026-10-29",
        ),
    ],
)
def test_html_list_bpd_baru_baca_judul_dan_tanggal(
    bank_name, url, fixture, expected_title, expected_date
):
    ff = FakeFetcher({url: (200, read_fixture(fixture))})
    result = collect_html_list(ff, Bank(name=bank_name, access="public"), url)

    assert result.ok
    assert len(result.items) == 1
    item = result.items[0]
    assert item.title == expected_title
    assert item.published == expected_date
    assert not item.title.startswith("29 Okt 26")


def test_html_list_bankaltimtara_buang_lelang_jaminan():
    url = "https://www.bankaltimtara.co.id/id/info/lelang"
    ff = FakeFetcher({url: (200, read_fixture("bankaltimtara_lelang.html"))})
    result = collect_html_list(ff, Bank(name="Bankaltimtara", access="public"), url)

    assert result.ok
    assert all("Jaminan" not in item.title for item in result.items)
    assert all("lelangagunan.bankaltimtara.co.id" not in item.url for item in result.items)


def test_item_edc_bpd_baru_lolos_dan_kartu_memuat_tanggal(tmp_path):
    url = "https://www.bpdbali.co.id/pengumuman"
    bank = Bank(
        name="BPD Bali", access="public",
        sources=[Source(url=url, type="html")],
    )
    report = run_light(
        FakeFetcher({url: (200, read_fixture("bpdbali_pengumuman.html"))}),
        [bank], load_keywords(), State.load(tmp_path), date(2026, 11, 3),
        skip_news=True,
    )

    assert len(report.new_items) == 1
    assert report.new_items[0].status == "tidak_diketahui"
    assert report.source_candidates == [("BPD Bali (html)", 1)]
    payload = build_message(report.new_items, report.checked, report.failed)
    widgets = payload["cardsV2"][0]["card"]["sections"][0]["widgets"]
    assert {w["decoratedText"]["topLabel"]: w["decoratedText"]["text"]
            for w in widgets if "decoratedText" in w}["Tanggal pengumuman"] == "28 Okt 2026"


def test_bank_lampung_dan_papua_ditunda_di_mode_light(tmp_path):
    configured = {bank.name: bank for bank in load_banks()}
    banks = [configured["Bank Lampung"], configured["Bank Papua"]]
    report = run_light(
        FakeFetcher({}), banks, load_keywords(), State.load(tmp_path),
        date(2026, 11, 3), skip_news=True,
    )

    assert report.candidates == 0
    assert report.failed == []
    assert report.deferred_js == [
        "Bank Lampung (https://www.banklampung.co.id/artikel/pengumuman): butuh browser, dicek di mode full",
        "Bank Papua (https://bankpapua.co.id/home/index/berita/pengumuman-lelang-33): butuh browser, dicek di mode full",
    ]


def test_html_list_tidak_memotong_angka_awal_yang_bukan_tanggal():
    """Awalan "10 Paket 2026" bukan tanggal, jadi judul harus utuh."""
    html = (
        '<ul><li><a href="/p/1">10 Paket 2026 Pengadaan Mesin EDC Android</a></li>'
        '<li><a href="/p/2">29 Okt 26 Pengumuman Tender Pengadaan Smart EDC</a></li></ul>'
    )
    fetcher = FakeFetcher({"https://contoh.bank/daftar": (200, html)})
    bank = Bank(name="Bank Contoh", aliases=["Bank Contoh"], group="bpd", access="public")
    res = collect_html_list(fetcher, bank, "https://contoh.bank/daftar")
    titles = {item.url: item.title for item in res.items}
    assert titles["https://contoh.bank/p/1"] == "10 Paket 2026 Pengadaan Mesin EDC Android"
    assert titles["https://contoh.bank/p/2"] == "Pengumuman Tender Pengadaan Smart EDC"
