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


def test_fingerprint_dari_judul_daftar_tidak_pecah_setelah_judul_diperpanjang():
    """Fix judul terpotong: fingerprint dihitung dari judul DAFTAR asli; setelah
    judul item diperpanjang ke versi utuh, fingerprint TETAP sama -- jadi
    seen.json yang sudah ada tetap mengenali item itu sebagai sama."""
    list_title = "Pekerjaan Pengadaan Sewa Beli Mesin Smart EDC PT Bank Sumut (Pers..."
    url = "https://www.banksumut.co.id/jasa_barang/smart-edc/"
    # Fingerprint seperti yang tersimpan di seen.json (dari judul daftar).
    stored_fp = fingerprint("Bank Sumut", list_title, url)

    it = Item(bank="Bank Sumut", title=list_title, url=url)
    # Pemanggil (pipeline) mengunci fingerprint SEBELUM enrich memperpanjang judul.
    ensure_fingerprint(it)
    assert it.fingerprint == stored_fp

    # Enrich memperpanjang judul ke versi utuh (tanpa menyentuh fingerprint).
    it.title = "Pekerjaan Pengadaan Sewa Beli Mesin Smart Electronic Data Capture (Smart EDC) PT Bank Sumut (Perseroda)"
    # Fingerprint tidak berubah -> item lama di seen tetap dianggap sama.
    assert it.fingerprint == stored_fp
