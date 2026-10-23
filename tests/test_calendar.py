"""Uji lewati akhir pekan dan hari libur."""

from datetime import date

from tenderbot.calendar_util import should_skip
from tenderbot.config import load_holidays

HOLIDAYS = load_holidays()


def test_skip_sabtu():
    skip, reason = should_skip(date(2026, 10, 24), HOLIDAYS)  # Sabtu
    assert skip and "akhir pekan" in reason


def test_skip_minggu():
    skip, _ = should_skip(date(2026, 10, 25), HOLIDAYS)  # Minggu
    assert skip


def test_skip_hari_libur_kemerdekaan():
    skip, reason = should_skip(date(2026, 8, 17), HOLIDAYS)  # libur nasional
    assert skip and "hari libur" in reason


def test_tidak_skip_hari_kerja_biasa():
    skip, _ = should_skip(date(2026, 10, 23), HOLIDAYS)  # Jumat biasa
    assert not skip


def test_holidays_memuat_2026_dan_2027():
    assert "2026-12-25" in HOLIDAYS
    assert "2027-08-17" in HOLIDAYS
