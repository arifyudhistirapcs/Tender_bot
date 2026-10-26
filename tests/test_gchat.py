"""Uji pembangunan pesan Google Chat VERSI BISNIS.

Keputusan Arif (2026-10-26): pesan Google Chat singkat & umum untuk tim bisnis.
Detail teknis (sumber gagal, HTTP, GDELT) TIDAK boleh muncul di pesan ini.
"""

from tenderbot.gchat import build_message, send
from tenderbot.models import Item, fingerprint


def _berjalan(**kw):
    base = dict(bank="Bank Sumut", title="Pengadaan Smart EDC",
                url="https://x.example/1", status="berjalan")
    base.update(kw)
    it = Item(**base)
    it.fingerprint = fingerprint(it.bank, it.title, it.url)
    return it


def test_pesan_tidak_ada_baru_satu_kalimat_dengan_jumlah():
    payload = build_message(new_items=[], checked_count=43, failed=[])
    text = payload["text"]
    assert text == "Tidak ada info tender EDC baru. (43 bank dipantau)"
    assert "cardsV2" not in payload


def test_pesan_tidak_ada_baru_tanpa_detail_teknis():
    # Walau ada daftar gagal/catatan, pesan bisnis TIDAK menampilkannya.
    payload = build_message(
        [], 43,
        failed=[("BRI (berita)", "HTTP 403"), ("GDELT", "HTTP 429")],
        note="Catatan: riset penuh tidak berjalan hari ini.",
    )
    text = payload["text"]
    for larang in ("HTTP", "GDELT", "403", "429", "gagal", "diakses", "robots"):
        assert larang not in text, f"kata teknis '{larang}' bocor ke pesan bisnis"
    assert text == "Tidak ada info tender EDC baru. (43 bank dipantau)"


def test_pembuka_menyebut_berjalan_dan_akan_dibuka():
    a = _berjalan()
    b = _berjalan(url="https://x.example/2", status="akan_dibuka",
                  reg_open="2026-11-01")
    payload = build_message([a, b], 43, [])
    assert payload["text"] == "Info tender EDC: 1 berjalan, 1 akan dibuka."
    assert len(payload["cardsV2"]) == 2


def test_kartu_memuat_bank_status_dengan_tanggal_dan_nilai():
    it = _berjalan(value_idr=6993000000, reg_close="2026-10-23")
    payload = build_message([it], 43, [])
    card_text = str(payload["cardsV2"])
    assert "Bank Sumut" in card_text
    assert "Berjalan, tutup 23 Okt 2026" in card_text
    assert "Rp6.993.000.000" in card_text


def test_kartu_status_akan_dibuka_dengan_tanggal():
    it = _berjalan(status="akan_dibuka", reg_open="2026-11-01")
    payload = build_message([it], 43, [])
    assert "Akan dibuka 1 Nov 2026" in str(payload["cardsV2"])


def test_kartu_tidak_memuat_field_teknis():
    # Volume/durasi/metode/tempat/kontak/media TIDAK boleh ada di kartu bisnis.
    it = _berjalan(
        volume="500 unit", duration="36 bulan",
        method="Pelelangan Umum", reg_place="Kantor Pusat",
        contact="panitia@banksumut.co.id", media_name="detikFinance",
        source_type="berita",
    )
    s = str(build_message([it], 43, [])["cardsV2"])
    for larang in ("500 unit", "36 bulan", "Pelelangan Umum", "Kantor Pusat",
                   "panitia@banksumut", "detikFinance", "Volume", "Metode",
                   "Kontak", "Media"):
        assert larang not in s, f"field teknis '{larang}' bocor ke kartu bisnis"


def _tombol_teks(card: dict) -> list[str]:
    labels: list[str] = []
    for section in card["card"]["sections"]:
        for w in section["widgets"]:
            for b in w.get("buttonList", {}).get("buttons", []):
                labels.append(b["text"])
    return labels


def test_tombol_lihat_pengumuman_selalu_ada():
    it = _berjalan()
    card = build_message([it], 43, [])["cardsV2"][0]
    assert "Lihat pengumuman" in _tombol_teks(card)


def test_tombol_lampiran_dan_daftar_vendor_hanya_bila_url_ada():
    it = _berjalan(
        attachment_url="https://x.example/lampiran.pdf",
        vendor_registration_url="https://eprocurement.bankjatim.co.id/reg",
    )
    labels = _tombol_teks(build_message([it], 43, [])["cardsV2"][0])
    assert "Lampiran" in labels
    assert "Daftar vendor" in labels

    # Tanpa URL -> tombolnya tidak muncul.
    it2 = _berjalan(url="https://x.example/9")
    labels2 = _tombol_teks(build_message([it2], 43, [])["cardsV2"][0])
    assert "Lampiran" not in labels2
    assert "Daftar vendor" not in labels2


def test_dry_run_tidak_mengirim(capsys):
    payload = build_message([], 43, [])
    outcome = send(payload, dry_run=True)
    assert outcome.dry_run and not outcome.sent
    out = capsys.readouterr().out
    assert "Tidak ada info tender EDC baru" in out
