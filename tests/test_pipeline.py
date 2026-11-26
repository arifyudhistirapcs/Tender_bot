"""Uji integrasi pipeline: item sama tidak terkirim dua kali lintas run."""

import pytest
from datetime import date
from urllib.parse import quote_plus

from conftest import FakeFetcher, read_fixture
from tenderbot.config import Bank, Keywords, NewsFeed, Source, load_keywords
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

    # Pesan Google Chat versi bisnis: satu kalimat, TANPA detail teknis.
    # (Kegagalan feed/GDELT ada di laporan Telegram, bukan di pesan ini.)
    payload = build_message(report.new_items, report.checked, report.failed)
    text = payload["text"]
    assert text == f"Tidak ada info tender EDC, alih daya, aplikasi/IT, atau alih data baru. ({report.checked} bank dipantau)"
    for larang in ("GDELT", "feed", "429", "Semua sumber"):
        assert larang not in text


def test_semua_sumber_ok_pesan_bisnis_singkat(tmp_path):
    """Bila tidak ada kegagalan, pesan bisnis tetap satu kalimat ringkas
    (status sumber TIDAK diumumkan di pesan Google Chat)."""
    from tenderbot.gchat import build_message
    banks = [_bank_sumut()]
    ff = _fetcher_for(banks)
    state = State.load(tmp_path)
    report = run_light(ff, banks, KW, state, TODAY, feeds=[FEED],
                       gdelt_sleep=_no_sleep)
    assert report.failed == []
    payload = build_message([], report.checked, report.failed)
    assert payload["text"] == (
        f"Tidak ada info tender EDC, alih daya, aplikasi/IT, atau alih data baru. ({report.checked} bank dipantau)"
    )


def _portal_bank(url: str) -> Bank:
    return Bank(
        name="Bank Contoh",
        aliases=["Bank Contoh"],
        group="bpd",
        access="public",
        sources=[Source(url=url, type="html")],
    )


@pytest.fixture(autouse=True)
def _no_retry_delay(monkeypatch):
    monkeypatch.setattr("tenderbot.pipeline.EMPTY_RETRY_DELAY_SECONDS", 0)


class _SeqFetcher(FakeFetcher):
    """Jawaban berurutan per url: tiap fetch mengambil jawaban berikutnya."""

    def __init__(self, url, bodies):
        super().__init__({})
        self._url, self._bodies = url, list(bodies)

    def fetch(self, url, bypass_robots=False):
        body = self._bodies.pop(0) if len(self._bodies) > 1 else self._bodies[0]
        self.routes = {url: (200, body)}
        return super().fetch(url)


_EMPTY = "<html><body>Belum ada pengumuman</body></html>"
_FULL = "<html><body>" + "".join(
    f'<a href="/pengadaan/{i}">Pengadaan Jasa Alih Daya {i}</a>' for i in range(12)
) + "</body></html>"


def test_portal_kosong_lalu_berisi_dipakai_tanpa_gagal(tmp_path):
    url = "https://contoh.bank/pengadaan"
    state = State.load(tmp_path)
    state.record_source_ok(url, "2026-11-03", item_count=374)
    ff = _SeqFetcher(url, [_EMPTY, _FULL])

    report = run_light(ff, [_portal_bank(url)], KW, state, TODAY, skip_news=True)

    assert report.failed == []
    assert ff.calls.count(url) == 2
    assert state.last_source_item_count(url) > 0
    assert state.source_health[url]["consecutive_failures"] == 0


def test_portal_kosong_dua_kali_gagal_dengan_alasan_dicoba_ulang(tmp_path):
    url = "https://contoh.bank/pengadaan"
    state = State.load(tmp_path)
    state.record_source_ok(url, "2026-11-03", item_count=374)
    ff = _SeqFetcher(url, [_EMPTY, _EMPTY, _FULL])

    report = run_light(ff, [_portal_bank(url)], KW, state, TODAY, skip_news=True)

    reason = "halaman terbuka tetapi 0 tautan (sebelumnya 374), dicoba ulang 1x"
    assert report.failed == [("Bank Contoh (html)", reason)]
    assert ff.calls.count(url) == 2  # hanya satu kali coba ulang


def test_portal_kosong_riwayat_kecil_tidak_dicoba_ulang(tmp_path):
    url = "https://contoh.bank/pengadaan"
    state = State.load(tmp_path)
    state.record_source_ok(url, "2026-11-03", item_count=9)
    ff = _SeqFetcher(url, [_EMPTY, _FULL])

    report = run_light(ff, [_portal_bank(url)], KW, state, TODAY, skip_news=True)

    assert report.failed == []
    assert ff.calls.count(url) == 1


def test_portal_kosong_dengan_riwayat_besar_dicatat_gagal(tmp_path):
    url = "https://contoh.bank/pengadaan"
    state = State.load(tmp_path)
    state.record_source_ok(url, "2026-11-03", item_count=374)

    report = run_light(
        FakeFetcher({url: (200, "<html><body>Belum ada pengumuman</body></html>")}),
        [_portal_bank(url)], KW, state, TODAY, skip_news=True,
    )

    reason = "halaman terbuka tetapi 0 tautan (sebelumnya 374), dicoba ulang 1x"
    assert report.failed == [("Bank Contoh (html)", reason)]
    assert report.source_candidates == [("Bank Contoh (html)", 0)]
    assert state.source_health[url]["consecutive_failures"] == 1
    assert state.source_health[url]["last_error"] == f"{TODAY}: {reason}"
    assert state.last_source_item_count(url) == 374


def test_portal_kosong_tanpa_riwayat_tidak_dicatat_gagal(tmp_path):
    url = "https://contoh.bank/pengadaan"
    state = State.load(tmp_path)

    report = run_light(
        FakeFetcher({url: (200, "<html><body>Belum ada pengumuman</body></html>")}),
        [_portal_bank(url)], KW, state, TODAY, skip_news=True,
    )

    assert report.failed == []
    assert report.source_candidates == [("Bank Contoh (html)", 0)]
    assert state.source_health[url]["consecutive_failures"] == 0


def test_state_lama_tanpa_jumlah_item_terakhir_tetap_terbaca(tmp_path):
    (tmp_path / "source_health.json").write_text(
        '{"https://contoh.bank/pengadaan": {"consecutive_failures": 2, '
        '"last_ok": "2026-11-03", "last_error": null}}',
        encoding="utf-8",
    )

    state = State.load(tmp_path)

    assert state.last_source_item_count("https://contoh.bank/pengadaan") is None
    assert state.source_health["https://contoh.bank/pengadaan"]["consecutive_failures"] == 2



def test_pipeline_browser_detail_skips_ticker_but_keeps_bsi_schedule(tmp_path):
    from tenderbot.models import Item
    from tenderbot.pipeline import RunReport, process_candidates

    item = Item(
        bank="BSI",
        title="Pengadaan Penyedia Jasa Tenaga Alih Daya Tahun 2027",
        url="https://www.bankbsi.co.id/pengadaan/tad-2027",
        source_type="portal",
        published="2026-10-30",
        detail_text=(
            "AUD -12.532,16 CAD -12.959,21 "
            "Pengambilan Dokumen Prakualifikasi: Hari/Tanggal: Jumat s.d Rabu, "
            "30 Oktober 2026 s.d 4 November 2026. "
            "Pemasukan Hardcopy dan Softcopy Dokumen Prakualifikasi: Hari/Tanggal: "
            "Rabu s.d Senin, 4 November 2026 s.d 6 November 2026."
        ),
    )
    state = State.load(tmp_path)
    report = RunReport(run_date="2026-11-03", mode="light")

    process_candidates(
        [item], KW, state, date(2026, 11, 3), "2026-11-03", report,
        enrich=False,
    )

    assert item.value_idr is None
    assert item.reg_open == "2026-10-30"
    assert item.reg_close == "2026-11-04"
    assert item.submit_close == "2026-11-06"

# ---- Url sumber banks.yaml = halaman daftar, juga untuk item inbox ----

def _pdf_bytes(text: str) -> bytes:
    import fitz
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), text)
    return doc.tobytes()


class _PdfOrHtmlFetcher(FakeFetcher):
    def __init__(self, routes, pdf_routes):
        super().__init__(routes)
        self.pdf_routes = pdf_routes

    def fetch(self, url, bypass_robots=False):
        if url in self.pdf_routes:
            from tenderbot.http_client import FetchResult
            self.calls.append(url)
            return FetchResult(url=url, status=200, text="", content=self.pdf_routes[url],
                               content_type="application/pdf")
        return super().fetch(url)


def test_inbox_url_sumber_enrich_false_tidak_diperkaya(tmp_path):
    from tenderbot.models import Item
    from tenderbot.pipeline import RunReport, process_candidates
    url = "https://www.bi.go.id/id/layanan/lelang-jasa-barang/default.aspx"
    banks = [Bank(name="Bank Indonesia", sources=[Source(url=url, type="bi_tender", enrich=False)])]
    item = Item(bank="Bank Indonesia",
                title="Jasa Tenaga Kerja Alih Daya Bongkar Muat Arsip",
                url=url + "/#tabel", source_type="portal")
    ff = FakeFetcher({url: (200, "<html>jangka waktu 16 (enam belas) tahun</html>")})
    process_candidates([item], KW, State.load(tmp_path), date(2026, 11, 25), "2026-11-25",
                       RunReport(run_date="2026-11-25", mode="full"),
                       fetcher=ff, banks=banks)
    assert ff.calls == []
    assert item.duration is None


def test_inbox_url_sumber_btn_daftar_pdf_cocok_tetap_dipakai(tmp_path):
    from tenderbot.models import Item
    from tenderbot.pipeline import RunReport, process_candidates
    url = "https://www.btn.co.id/en/Procurement/Procurement-List"
    pdf_url = "https://www.btn.co.id/files/208.pdf"
    title = "Pengadaan Jasa Alih Daya Tenaga Kerja"
    banks = [Bank(name="BTN", sources=[Source(url=url, type="html")])]
    item = Item(bank="BTN", title=title, url=url, source_type="portal")
    html = f'<a href="{pdf_url}">Unduh lampiran pengadaan PDF</a> jangka waktu 99 bulan'
    ff = _PdfOrHtmlFetcher({url: (200, html)},
                           {pdf_url: _pdf_bytes(title + "\njangka waktu 12 bulan")})
    process_candidates([item], KW, State.load(tmp_path), date(2026, 11, 25), "2026-11-25",
                       RunReport(run_date="2026-11-25", mode="full"),
                       fetcher=ff, banks=banks)
    assert pdf_url in ff.calls
    assert item.duration == "12 bulan"  # dari PDF, bukan HTML (99 bulan)
