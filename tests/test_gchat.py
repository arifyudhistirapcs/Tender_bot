"""Uji pembangunan pesan Google Chat."""

from tenderbot.gchat import build_message, send
from tenderbot.models import Item, fingerprint


def test_pesan_tidak_ada_baru_memuat_jumlah_dan_gagal():
    payload = build_message(
        new_items=[],
        checked_count=42,
        failed=[("BRI (berita)", "HTTP 403"), ("PermataBank (berita)", "HTTP 403")],
    )
    text = payload["text"]
    assert "Tidak ada informasi tender baru" in text
    assert "42 bank" in text
    assert "2 tidak bisa diakses" in text or "2 tidak bisa diakses:" in text
    assert "BRI (berita): HTTP 403" in text


def test_pesan_tidak_ada_baru_tanpa_gagal():
    payload = build_message([], 42, [])
    assert "Semua sumber bisa diakses" in payload["text"]


def test_pesan_ada_item_pakai_cards():
    it = Item(bank="Bank Sumut", title="Pengadaan Smart EDC",
              url="https://x.example/1", value_idr=6993000000, published="2026-10-13",
              status="berjalan")
    it.fingerprint = fingerprint(it.bank, it.title, it.url)
    payload = build_message([it], 42, [])
    assert "1 tender berjalan" in payload["text"]
    assert payload["cardsV2"]
    card_text = str(payload["cardsV2"])
    assert "Rp6.993.000.000" in card_text


def test_dry_run_tidak_mengirim(capsys):
    payload = build_message([], 1, [])
    outcome = send(payload, dry_run=True)
    assert outcome.dry_run and not outcome.sent
    out = capsys.readouterr().out
    assert "Tidak ada informasi tender baru" in out


def _tombol_teks(card: dict) -> list[str]:
    """Ambil semua label tombol di satu kartu."""
    labels: list[str] = []
    for section in card["card"]["sections"]:
        for w in section["widgets"]:
            for b in w.get("buttonList", {}).get("buttons", []):
                labels.append(b["text"])
    return labels


def test_kartu_tampilkan_tombol_daftar_vendor_bila_ada_url():
    it = Item(bank="Bank Jatim", title="Pengadaan EDC",
              url="https://x.example/1", status="berjalan",
              vendor_registration_url="https://eprocurement.bankjatim.co.id/main/index/registrasi",
              vendor_registration_note="Isi NPWP dan email resmi.")
    it.fingerprint = fingerprint(it.bank, it.title, it.url)
    payload = build_message([it], 42, [])
    card = payload["cardsV2"][0]
    labels = _tombol_teks(card)
    assert "Daftar vendor" in labels
    assert "Buka sumber" in labels
    # URL vendor benar-benar tertaut di tombol.
    s = str(card)
    assert "eprocurement.bankjatim.co.id" in s
    # Catatan daftar vendor muncul sebagai baris.
    assert "Isi NPWP" in s


def test_kartu_tanpa_tombol_daftar_vendor_bila_tanpa_url():
    it = Item(bank="Bank Sumut", title="Pengadaan Smart EDC",
              url="https://x.example/2", status="berjalan")
    it.fingerprint = fingerprint(it.bank, it.title, it.url)
    payload = build_message([it], 42, [])
    labels = _tombol_teks(payload["cardsV2"][0])
    assert "Daftar vendor" not in labels
