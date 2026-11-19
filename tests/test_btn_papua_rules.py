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
