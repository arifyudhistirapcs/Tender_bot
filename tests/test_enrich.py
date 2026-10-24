"""Uji pengayaan detail: ekstraksi field dari teks, baca PDF, alur enrich."""

from pathlib import Path

from conftest import FakeFetcher, read_fixture
from tenderbot.enrich import extract_fields, enrich_item, pdf_bytes_to_text
from tenderbot.http_client import FetchResult
from tenderbot.models import Item

VENDOR_PDF = (
    Path(__file__).resolve().parents[1]
    / "kerja" / "riset" / "vendor" / "lampiran-banksumut-smart-edc-005-2026.pdf"
)


# ---- Ekstraksi field dari teks lampiran Bank Sumut (fixture lokal) ----

def test_extract_fields_banksumut_teks():
    text = read_fixture("banksumut_lampiran_005_2026.txt")
    f = extract_fields(text)
    assert f["value_idr"] == 6_993_000_000
    assert f["volume"] == "500 unit"
    assert f["duration"] == "36 bulan"
    assert f["reg_open"] == "2026-10-13"
    assert f["reg_close"] == "2026-10-23"
    assert f["posted"] == "2026-10-13"
    assert "Pelelangan Umum" in f["method"]
    assert "Pascakualifikasi" in f["method"]
    assert "Imam Bonjol" in f["reg_place"]
    assert "061-4515100" in f["contact"]


def test_extract_fields_kosong_untuk_teks_tanpa_field():
    assert extract_fields("halaman biasa tanpa data tender") == {}
    assert extract_fields("") == {}


# ---- Baca PDF asli dengan PyMuPDF ----

def test_pdf_asli_terbaca_dan_field_terekstrak():
    assert VENDOR_PDF.exists(), "PDF contoh lampiran hilang"
    data = VENDOR_PDF.read_bytes()
    text = pdf_bytes_to_text(data)
    assert "Smart" in text and "6.993.000.000" in text
    f = extract_fields(text)
    assert f["value_idr"] == 6_993_000_000
    assert f["volume"] == "500 unit"
    assert f["duration"] == "36 bulan"
    assert f["reg_open"] == "2026-10-13"
    assert f["reg_close"] == "2026-10-23"


def test_pdf_byte_rusak_kembalikan_kosong():
    assert pdf_bytes_to_text(b"bukan pdf") == ""
    assert pdf_bytes_to_text(b"") == ""


# ---- Alur enrich: halaman detail menaut PDF ----

class _PdfFetcher(FakeFetcher):
    """FakeFetcher yang bisa melayani byte PDF untuk URL tertentu."""

    def __init__(self, routes, pdf_routes):
        super().__init__(routes)
        self.pdf_routes = pdf_routes  # url -> bytes

    def fetch(self, url):
        if url in self.pdf_routes:
            self.calls.append(url)
            data = self.pdf_routes[url]
            return FetchResult(url=url, status=200, text="", content=data,
                               content_type="application/pdf")
        return super().fetch(url)


def test_enrich_item_buka_detail_lalu_pdf():
    detail_url = "https://www.banksumut.co.id/jasa_barang/smart-edc/"
    pdf_url = "https://www.banksumut.co.id/files/lampiran-005-2026.pdf"
    detail_html = (
        f'<html><body><h1>Pengumuman Pelelangan Smart EDC</h1>'
        f'<a href="{pdf_url}">Unduh lampiran pengumuman (PDF)</a>'
        f'</body></html>'
    )
    item = Item(bank="Bank Sumut",
                title="Pengadaan Sewa Beli Mesin Smart EDC",
                url=detail_url, source_type="portal")
    ff = _PdfFetcher(
        routes={detail_url: (200, detail_html)},
        pdf_routes={pdf_url: VENDOR_PDF.read_bytes()},
    )
    enrich_item(item, ff)
    assert item.value_idr == 6_993_000_000
    assert item.volume == "500 unit"
    assert item.duration == "36 bulan"
    assert item.reg_open == "2026-10-13"
    assert item.reg_close == "2026-10-23"
    assert item.posted == "2026-10-13"
    assert item.attachment_url == pdf_url


def test_enrich_tidak_menimpa_field_terisi():
    # Field yang sudah diisi (mis. dari inbox agen) tidak ditimpa.
    item = Item(bank="Bank Sumut", title="T",
                url="https://x.example/d", value_idr=123, volume="9 unit")
    pdf_url = "https://x.example/a.pdf"
    detail_html = f'<a href="{pdf_url}">lampiran pengadaan PDF</a>'
    ff = _PdfFetcher(
        routes={"https://x.example/d": (200, detail_html)},
        pdf_routes={pdf_url: VENDOR_PDF.read_bytes()},
    )
    enrich_item(item, ff)
    assert item.value_idr == 123       # tidak ditimpa
    assert item.volume == "9 unit"     # tidak ditimpa
    assert item.duration == "36 bulan"  # field kosong terisi


def test_enrich_maksimal_3_pdf():
    detail_url = "https://x.example/d"
    pdfs = [f"https://x.example/p{i}.pdf" for i in range(5)]
    links = "".join(f'<a href="{u}">lampiran dokumen pengadaan {u}</a>' for u in pdfs)
    item = Item(bank="X", title="T", url=detail_url)
    # Semua PDF rusak (kosong) supaya kita hanya mengukur jumlah fetch PDF.
    ff = _PdfFetcher(
        routes={detail_url: (200, f"<html>{links}</html>")},
        pdf_routes={u: b"" for u in pdfs},
    )
    enrich_item(item, ff)
    pdf_calls = [c for c in ff.calls if c.endswith(".pdf")]
    assert len(pdf_calls) == 3  # dibatasi 3


def test_enrich_gagal_akses_tidak_meledak():
    item = Item(bank="X", title="T", url="https://tak-ada-rute.example/x")
    ff = _PdfFetcher(routes={}, pdf_routes={})
    # URL tidak ada rute -> AccessError ditangani, item tetap utuh.
    enrich_item(item, ff)
    assert item.value_idr is None


# ---- Penemuan lampiran pada halaman NYATA Bank Sumut ----

from tenderbot.enrich import discover_attachments  # noqa: E402

GDRIVE_ID = "1hHkQtNjh_Kn1UFfvq_b2wII3kETda-px"
GDRIVE_DL = f"https://drive.google.com/uc?export=download&id={GDRIVE_ID}"


def test_discover_attachments_gdrive_di_tombol_gambar():
    # Link Google Drive membungkus <img> tombol, TIDAK ada ".pdf" di href.
    html = read_fixture("banksumut_detail_smart_edc.html")
    atts = discover_attachments(html, "https://www.banksumut.co.id/jasa_barang/x/")
    assert GDRIVE_DL in atts  # diubah ke unduhan langsung


def test_discover_attachments_pdf_di_onclick_dan_data_attr():
    html = (
        '<a onclick="window.open(\'/files/a.pdf\')">x</a>'
        '<button data-href="https://x.example/b.PDF">y</button>'
    )
    atts = discover_attachments(html, "https://x.example/post/")
    assert "https://x.example/files/a.pdf" in atts
    assert "https://x.example/b.PDF" in atts


class _RealFetcher(FakeFetcher):
    """Melayani HTML detail + byte PDF Google Drive (uji penemuan nyata)."""

    def __init__(self, routes, pdf_routes):
        super().__init__(routes)
        self.pdf_routes = pdf_routes
        self.bypass_calls: list[str] = []

    def fetch(self, url, bypass_robots=False):
        if bypass_robots:
            self.bypass_calls.append(url)
        if url in self.pdf_routes:
            self.calls.append(url)
            return FetchResult(url=url, status=200, text="",
                               content=self.pdf_routes[url],
                               content_type="application/pdf")
        return super().fetch(url)


def test_enrich_real_detail_html_baca_lampiran_gdrive():
    detail_url = "https://www.banksumut.co.id/jasa_barang/smart-edc/"
    html = read_fixture("banksumut_detail_smart_edc.html")
    item = Item(bank="Bank Sumut",
                title="Pengadaan Sewa Beli Mesin Smart EDC",
                url=detail_url, source_type="portal")
    ff = _RealFetcher(
        routes={detail_url: (200, html)},
        pdf_routes={GDRIVE_DL: VENDOR_PDF.read_bytes()},
    )
    enrich_item(item, ff)
    # Nilai + metode dari HTML; tanggal/volume/durasi dari PDF Google Drive.
    assert item.value_idr == 6_993_000_000
    assert item.reg_open == "2026-10-13"
    assert item.reg_close == "2026-10-23"
    assert item.volume == "500 unit"
    assert item.duration == "36 bulan"
    assert "Pelelangan Umum" in item.method
    assert item.attachment_url == GDRIVE_DL
    # Lampiran Google Drive diambil lewat jalur unduhan-langsung (bypass_robots).
    assert GDRIVE_DL in ff.bypass_calls


def test_enrich_fallback_wp_rest_saat_html_terblokir():
    # Halaman detail 403 (seperti situs nyata ke klien polos) -> fallback REST.
    detail_url = "https://www.banksumut.co.id/jasa_barang/pekerjaan-pengadaan-sewa-beli-mesin-smart-electronic-data-capture-smart-edc-pt-bank-sumut-perseroda/"
    rest_url = ("https://www.banksumut.co.id/wp-json/wp/v2/jasa_barang?slug="
                "pekerjaan-pengadaan-sewa-beli-mesin-smart-electronic-data-capture-smart-edc-pt-bank-sumut-perseroda")
    media_url = "https://www.banksumut.co.id/wp-json/wp/v2/media?parent=10580"
    item = Item(bank="Bank Sumut", title="Smart EDC", url=detail_url,
                source_type="portal")
    ff = _RealFetcher(
        routes={
            detail_url: (403, ""),                       # HTML terblokir
            rest_url: (200, read_fixture("banksumut_wp_jasa_barang.json")),
            media_url: (200, "[]"),                       # tak ada media WP
        },
        pdf_routes={GDRIVE_DL: VENDOR_PDF.read_bytes()},
    )
    enrich_item(item, ff)
    assert item.value_idr == 6_993_000_000           # dari content REST
    assert "Pelelangan Umum" in item.method          # dari content REST
    assert item.reg_open == "2026-10-13"             # dari PDF Google Drive
    assert item.reg_close == "2026-10-23"
    assert item.volume == "500 unit"
    assert item.duration == "36 bulan"
    assert item.attachment_url == GDRIVE_DL


# ---- Judul utuh dari halaman detail (fix judul terpotong) ----

from tenderbot.enrich import (  # noqa: E402
    choose_title, clean_title, extract_detail_title,
)
from tenderbot.models import fingerprint  # noqa: E402

FULL_TITLE = ("Pekerjaan Pengadaan Sewa Beli Mesin Smart Electronic Data "
              "Capture (Smart EDC) PT Bank Sumut (Perseroda)")


def test_clean_title_entity_dan_suffix_situs():
    assert clean_title("Market Sounding EDC | Bank Jatim") == "Market Sounding EDC"
    assert clean_title("Pengumuman &amp; Lelang EDC") == "Pengumuman & Lelang EDC"
    # Suffix tidak dibuang bila menyisakan judul terlalu pendek.
    assert clean_title("EDC - A") == "EDC - A"


def test_extract_detail_title_urutan_h1_og_title():
    assert extract_detail_title(f"<h1>{FULL_TITLE}</h1>") == FULL_TITLE
    og = f'<meta property="og:title" content="{FULL_TITLE} | Bank Sumut">'
    assert extract_detail_title(og) == FULL_TITLE


def test_choose_title_judul_daftar_terpotong_pakai_detail():
    lst = "Pekerjaan Pengadaan Sewa Beli Mesin Smart EDC PT Bank Sumut (Pers..."
    assert choose_title(lst, FULL_TITLE) == FULL_TITLE


def test_choose_title_detail_lebih_panjang_dan_prefiks():
    lst = "Pekerjaan Pengadaan Sewa Beli Mesin Smart"
    detail = "Pekerjaan Pengadaan Sewa Beli Mesin Smart EDC PT Bank Sumut"
    assert choose_title(lst, detail) == detail


def test_choose_title_pertahankan_daftar_bila_detail_beda():
    lst = "Pengadaan Smart EDC"
    detail = "Berita lain yang tidak terkait sama sekali"
    assert choose_title(lst, detail) == lst


def test_enrich_perpanjang_judul_terpotong_dari_h1():
    detail_url = "https://www.banksumut.co.id/jasa_barang/smart-edc/"
    truncated = "Pekerjaan Pengadaan Sewa Beli Mesin Smart EDC PT Bank Sumut (Pers..."
    html = f"<html><body><h1>{FULL_TITLE}</h1></body></html>"
    item = Item(bank="Bank Sumut", title=truncated, url=detail_url,
                source_type="portal")
    # Fingerprint dikunci dari judul DAFTAR (seperti pipeline), sebelum enrich.
    item.fingerprint = fingerprint(item.bank, item.title, item.url)
    fp_before = item.fingerprint
    ff = FakeFetcher({detail_url: (200, html)})
    enrich_item(item, ff)
    assert item.title == FULL_TITLE           # judul diperpanjang
    assert not item.title.endswith("...")     # tidak lagi terpotong
    assert item.fingerprint == fp_before      # fingerprint tidak berubah
