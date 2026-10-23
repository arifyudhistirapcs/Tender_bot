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


def test_tanpa_kata_edc_ditolak():
    it = _item("Pengadaan jasa kebersihan kantor pusat")
    res = evaluate(it, KW, TODAY)
    assert not res.passed
    assert "EDC" in res.reason


def test_lebih_tua_dari_90_hari_ditolak():
    it = _item("Pengadaan sewa mesin EDC", published="2026-01-01")
    res = evaluate(it, KW, TODAY)
    assert not res.passed
    assert "90" in res.reason


def test_tanggal_masa_depan_ditolak():
    it = _item("Pengadaan sewa mesin EDC", published="2027-01-01")
    assert not evaluate(it, KW, TODAY).passed
