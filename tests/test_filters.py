"""Uji saringan aturan."""

from datetime import date

from tenderbot.config import load_keywords
from tenderbot.filters import evaluate
from tenderbot.models import Item

KW = load_keywords()
TODAY = date(2026, 10, 23)


def _item(title, evidence="", published="2026-10-13"):
    return Item(bank="Bank Sumut", title=title, url="https://x.example/1",
                published=published, evidence=evidence)


def test_lolos_smart_edc():
    it = _item("Pengadaan Sewa Beli Mesin Smart EDC Bank Sumut")
    assert evaluate(it, KW, TODAY).passed


def test_buang_agunan():
    it = _item("Pelelangan Umum Agunan Yang Diambil Alih, mesin EDC pengadaan")
    res = evaluate(it, KW, TODAY)
    assert not res.passed
    assert "agunan" in res.reason


def test_buang_jaminan():
    it = _item("Lelang jaminan kredit, terminal EDC pengadaan")
    assert not evaluate(it, KW, TODAY).passed


def test_buang_export_development_canada():
    it = _item("Export Development Canada tender pengadaan terminal EDC")
    assert not evaluate(it, KW, TODAY).passed


def test_tanpa_kata_pengadaan_ditolak():
    it = _item("Profil mesin EDC Smart EDC terbaru di cabang")
    res = evaluate(it, KW, TODAY)
    assert not res.passed
    assert "pengadaan" in res.reason


def test_jasa_kebersihan_masuk_alih_daya():
    it = _item("Pengadaan jasa kebersihan kantor pusat")
    assert evaluate(it, KW, TODAY).passed
    assert it.category == "alih_daya"


def test_lebih_tua_dari_90_hari_ditolak():
    it = _item("Pengadaan sewa mesin EDC", published="2026-01-01")
    res = evaluate(it, KW, TODAY)
    assert not res.passed
    assert "90" in res.reason


def test_tanggal_masa_depan_ditolak():
    it = _item("Pengadaan sewa mesin EDC", published="2027-01-01")
    assert not evaluate(it, KW, TODAY).passed


def _portal(title, source_type="portal"):
    it = Item(bank="BTN", title=title, url="https://x.example/2",
              published="2026-10-13", evidence="", source_type=source_type)
    return it, evaluate(it, KW, TODAY)


def test_layanan_kas_atm_alih_daya():
    for judul in (
        "Pengadaan Jasa Sentralisasi Kas Bank Sumut Wilayah Nias Kepada Perusahaan Pihak Ketiga",
        "Pengadaan Jasa Cash Replenishment & First Line Maintenance (CR-FLM) ATM-CRM BTN Periode 2027-2028",
    ):
        it, res = _portal(judul)
        assert res.passed, judul
        assert it.category == "alih_daya"


def test_beli_sewa_mesin_atm_crm_tidak_lolos():
    for judul in ("Pengadaan Mesin ATM dan CRM", "Sewa Mesin CRM"):
        _, res = _portal(judul)
        assert not res.passed, judul


def test_berita_cash_replenishment_bukan_alih_daya():
    it, res = _portal("Pengadaan layanan cash replenishment bank", source_type="news")
    assert it.category != "alih_daya"
    assert not res.passed
