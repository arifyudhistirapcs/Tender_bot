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
