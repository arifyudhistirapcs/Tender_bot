"""Uji dedup: fingerprint persis dan judul mirip 60 hari."""

from datetime import date

from tenderbot.dedup import ensure_fingerprint, is_near_duplicate
from tenderbot.models import Item, canonical_url, fingerprint, normalize_text

TODAY = date(2026, 10, 23)


def test_fingerprint_stabil_dan_sama_untuk_item_identik():
    a = fingerprint("Bank Sumut", "Pengadaan Smart EDC", "https://x.example/a/")
    b = fingerprint("Bank Sumut", "Pengadaan Smart EDC", "https://x.example/a")
    assert a == b  # trailing slash dikanonikkan


def test_canonical_url_buang_utm():
    # Skema+host lowercase, path dipertahankan apa adanya, utm dibuang.
    assert canonical_url("https://X.example/A/?utm_source=news&id=5") == \
        "https://x.example/A?id=5"


def test_near_duplicate_judul_mirip_bank_sama():
    it = Item(bank="Bank Sumut", title="Pengadaan Sewa Beli Mesin Smart EDC",
              url="https://x.example/new", published="2026-10-13")
    seen = [("Bank Sumut", normalize_text("Pengadaan Sewa Beli Mesin Smart EDC."),
             "2026-10-01")]
    assert is_near_duplicate(it, seen, TODAY)


def test_bukan_near_duplicate_bank_beda():
    it = Item(bank="Bank Jatim", title="Pengadaan Sewa Beli Mesin Smart EDC",
              url="https://x.example/new", published="2026-10-13")
    seen = [("Bank Sumut", normalize_text("Pengadaan Sewa Beli Mesin Smart EDC"),
             "2026-10-01")]
    assert not is_near_duplicate(it, seen, TODAY)


def test_bukan_near_duplicate_di_luar_jendela_60_hari():
    it = Item(bank="Bank Sumut", title="Pengadaan Sewa Beli Mesin Smart EDC",
              url="https://x.example/new", published="2026-10-13")
    seen = [("Bank Sumut", normalize_text("Pengadaan Sewa Beli Mesin Smart EDC"),
             "2026-01-01")]
    assert not is_near_duplicate(it, seen, TODAY)


def test_ensure_fingerprint_mengisi_sekali():
    it = Item(bank="B", title="T", url="https://x.example/1")
    fp = ensure_fingerprint(it)
    assert fp and it.fingerprint == fp
