"""Uji parser tanggal bahasa Indonesia dan nilai rupiah."""

from datetime import date

from tenderbot.dates_id import (
    format_rupiah,
    parse_date_range,
    parse_rupiah,
    parse_single_date,
)


def test_tanggal_sederhana():
    assert parse_single_date("13 Oktober 2026") == date(2026, 10, 13)


def test_tanggal_dengan_nama_hari():
    assert parse_single_date("Selasa, 13 Oktober 2026") == date(2026, 10, 13)


def test_tanggal_numerik_slash():
    assert parse_single_date("13/10/2026") == date(2026, 10, 13)


def test_tanggal_numerik_strip():
    assert parse_single_date("13-10-2026") == date(2026, 10, 13)


def test_tanggal_ejaan_lama_nopember():
    assert parse_single_date("21 Nopember 2023") == date(2023, 11, 21)


def test_tanggal_tidak_ada():
    assert parse_single_date("tidak ada tanggal di sini") is None
    assert parse_single_date("") is None


def test_tanggal_tidak_valid_dikembalikan_none():
    assert parse_single_date("32 Oktober 2026") is None


def test_rentang_tanggal():
    start, end = parse_date_range("13 Oktober 2026 s.d 23 Oktober 2026")
    assert start == date(2026, 10, 13)
    assert end == date(2026, 10, 23)


def test_rentang_dengan_nama_hari_di_depan():
    start, end = parse_date_range("Selasa s.d Jum'at / 13 Oktober 2026 s.d 23 Oktober 2026")
    assert start == date(2026, 10, 13)
    assert end == date(2026, 10, 23)


def test_satu_tanggal_bukan_rentang():
    start, end = parse_date_range("16 Oktober 2026")
    assert start == date(2026, 10, 16)
    assert end is None


def test_rupiah_dengan_prefiks_dan_akhiran():
    assert parse_rupiah("Rp6.993.000.000,-") == 6_993_000_000


def test_rupiah_tanpa_prefiks():
    assert parse_rupiah("6.993.000.000") == 6_993_000_000


def test_rupiah_dengan_spasi_dan_desimal():
    assert parse_rupiah("Rp 6.993.000.000,00") == 6_993_000_000


def test_rupiah_tidak_ada():
    assert parse_rupiah("tidak ada nilai") is None
    # Angka tanpa pemisah ribuan (mis. nomor dokumen) TIDAK ditangkap.
    assert parse_rupiah("Nomor 005 tahun 2026") is None


def test_format_rupiah():
    assert format_rupiah(6_993_000_000) == "Rp6.993.000.000"
    assert format_rupiah(None) is None
