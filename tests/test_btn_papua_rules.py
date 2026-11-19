"""Uji aturan detail BTN (Denpasar/TAD) dan dedup Bank Papua.

Potongan teks diambil persis dari berkas kontrak (kontrak-btn-detail-papua.md).
"""

from tenderbot.enrich import extract_fields

PENGALAMAN_DENPASAR = (
    "Memiliki pengalaman renovasi/pembangunan gedung sejak Tahun 2021 s/d 2026 "
    "dengan masing-masing nilai kontrak minimal Rp6.800.000.000,-"
)


# ---- 1. nilai ----

def test_nilai_syarat_pengalaman_bukan_value_idr():
    assert "value_idr" not in extract_fields(PENGALAMAN_DENPASAR)
    assert "value_idr" not in extract_fields(PENGALAMAN_DENPASAR, value_fallback=False)


def test_label_hps_tetap_dibaca_walau_ada_syarat_pengalaman():
    text = PENGALAMAN_DENPASAR + " Harga Perkiraan Sendiri (HPS) Rp1.500.000.000,-"
    assert extract_fields(text)["value_idr"] == 1_500_000_000
    assert extract_fields("Pagu Rp2.000.000.000,-")["value_idr"] == 2_000_000_000


# ---- 2. durasi ----

def test_frasa_pengalaman_bukan_durasi():
    assert "duration" not in extract_fields(PENGALAMAN_DENPASAR)
    text = "Pengalaman 3 (Tiga) Tahun terakhir (Oktober 2023 – November 2026)"
    assert "duration" not in extract_fields(text)
    text = "dalam kurun waktu 3 (Tiga) Tahun terakhir"
    assert "duration" not in extract_fields(text)


def test_durasi_kontrak_asli_tetap_terbaca():
    text = PENGALAMAN_DENPASAR + " Jangka waktu pelaksanaan pekerjaan 36 (tiga puluh enam) Bulan."
    assert extract_fields(text)["duration"] == "36 bulan"
