"""Logika lewati akhir pekan dan hari libur."""

from __future__ import annotations

from datetime import date


def is_weekend(day: date) -> bool:
    # Monday=0 ... Saturday=5, Sunday=6
    return day.weekday() >= 5


def is_holiday(day: date, holidays: set[str]) -> bool:
    return day.isoformat() in holidays


def should_skip(day: date, holidays: set[str]) -> tuple[bool, str]:
    """Kembalikan (skip?, alasan)."""
    if is_weekend(day):
        return True, f"akhir pekan ({day.strftime('%A')})"
    if is_holiday(day, holidays):
        return True, f"hari libur ({day.isoformat()})"
    return False, ""
