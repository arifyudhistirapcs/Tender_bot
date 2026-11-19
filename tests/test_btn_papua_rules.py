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


# ---- 3. rentang tanggal pendaftaran ----

def test_rentang_bulan_hanya_di_tanggal_kedua():
    text = "Pendaftaran Hari/tanggal : Kamis s.d. Senin/19 s.d. 23 November 2026 Pukul : 08.00 WIB s.d 17.00 WIB"
    out = extract_fields(text)
    assert (out["reg_open"], out["reg_close"]) == ("2026-11-19", "2026-11-23")


def test_rentang_btn_kamis_senin_dua_tanggal_lengkap():
    text = (
        "Jadwal pendaftaran Hari/tanggal : Kamis – Senin (19 November 2026 – 23 November 2026) "
        "(Hari Kerja) Pukul : 08.00 WIB s.d 17.00 WIB"
    )
    out = extract_fields(text)
    assert (out["reg_open"], out["reg_close"]) == ("2026-11-19", "2026-11-23")
    out = extract_fields(text.replace("–", "-"))
    assert (out["reg_open"], out["reg_close"]) == ("2026-11-19", "2026-11-23")


# ---- 4. dedup dan status: tanggal di awal judul ----

from datetime import date  # noqa: E402

from tenderbot.config import load_keywords  # noqa: E402
from tenderbot.dedup import is_near_duplicate  # noqa: E402
from tenderbot.models import Item, fingerprint, strip_title_date  # noqa: E402
from tenderbot.pipeline import RunReport, process_candidates  # noqa: E402
from tenderbot.state import State  # noqa: E402
from tenderbot.status import has_matching_result_announcement, title_core_tokens  # noqa: E402

KW = load_keywords()
TODAY = date(2026, 11, 16)
LIST_URL = "https://bankpapua.co.id/home/index/berita/pengumuman-lelang-33"
DETAIL_URL = "https://bankpapua.co.id/home/index/detail/lelang-pengadaan-outsourcing-jasa-keamanan-security-bank-papua-kc-waisai-1969"
JUDUL_LAMA = "Lelang Pekerjaan Pengadaan Outsourcing Jasa Keamanan (Security) Bank Papua KC Waisai"
JUDUL_BARU = "03 November 2026 " + JUDUL_LAMA
JUDUL_TIMIKA = "Lelang Pekerjaan Pengadaan Outsourcing Jasa Driver Bank Papua KC TImika"


def test_strip_title_date_awal_dan_akhir():
    assert strip_title_date(JUDUL_BARU) == JUDUL_LAMA
    assert strip_title_date("06 Nov 2026 Hasil Koreksi Aritmatik Lelang X") == "Hasil Koreksi Aritmatik Lelang X"
    assert strip_title_date("Lelang X KC Waisai 03 November 2026") == "Lelang X KC Waisai"
    assert strip_title_date(JUDUL_LAMA) == JUDUL_LAMA


def test_near_duplicate_judul_berawalan_tanggal_cocok_entri_lama():
    item = Item(bank="Bank Papua", title=JUDUL_BARU, url=LIST_URL, published="2026-11-03")
    seen = [("Bank Papua", JUDUL_LAMA, "2026-11-10")]  # judul mentah seperti di seen.json
    assert is_near_duplicate(item, seen, TODAY)


def test_cabang_berbeda_tetap_terpisah_walau_ada_tanggal():
    item = Item(bank="Bank Papua", title="03 November 2026 " + JUDUL_LAMA.replace("Waisai", "Sorong"),
                url=LIST_URL, published="2026-11-03")
    seen = [("Bank Papua", JUDUL_LAMA, "2026-11-10")]
    assert not is_near_duplicate(item, seen, TODAY)


def test_pengumuman_hasil_tanggal_di_awal_cocok_dengan_tender():
    hasil = Item(bank="Bank Papua", url=LIST_URL,
                 title="06 November 2026 Hasil Koreksi Aritmatik " + JUDUL_TIMIKA)
    tender = Item(bank="Bank Papua", title="03 November 2026 " + JUDUL_TIMIKA, url=LIST_URL)
    assert has_matching_result_announcement(tender, {title_core_tokens(hasil.title)})


def _papua_state(tmp_path):
    state = State.load(tmp_path)
    lama = Item(bank="Bank Papua", title=JUDUL_LAMA, url=DETAIL_URL, published="2026-11-10")
    lama.fingerprint = fingerprint(lama.bank, lama.title, lama.url)
    state.mark_seen(lama, "2026-11-10")
    return state, lama.fingerprint


def test_pipeline_item_halaman_daftar_tidak_jadi_kartu_baru(tmp_path):
    state, fp_lama = _papua_state(tmp_path)
    baru = Item(bank="Bank Papua", title=JUDUL_BARU, url=LIST_URL, published="2026-11-03")
    report = RunReport(run_date="2026-11-16", mode="light")
    process_candidates([baru], KW, state, TODAY, "2026-11-16", report, enrich=False)
    assert report.passed_filter == 1  # lolos saringan, ditolak dedup
    assert report.new_items == []
    assert fp_lama in state.seen  # fingerprint lama tetap berlaku


def test_pipeline_driver_timika_tutup_oleh_pengumuman_hasil(tmp_path):
    state = State.load(tmp_path)
    tender = Item(bank="Bank Papua", title="03 November 2026 " + JUDUL_TIMIKA,
                  url=LIST_URL, published="2026-11-03")
    hasil = Item(bank="Bank Papua", url=LIST_URL, published="2026-11-06",
                 title="06 November 2026 Hasil Koreksi Aritmatik " + JUDUL_TIMIKA)
    report = RunReport(run_date="2026-11-16", mode="light")
    process_candidates([tender, hasil], KW, state, TODAY, "2026-11-16", report, enrich=False)
    assert report.new_items == []
    assert any(r == "sudah ada pengumuman hasil" for _, t, r in report.dropped if "Driver" in t)
