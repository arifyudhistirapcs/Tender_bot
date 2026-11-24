from tenderbot.enrich import extract_fields

SYARAT = (
    "1.1. Memiliki pengalaman Cash Replenishment & First Line Maintenance dalam "
    "pengelolaan mesin ATM-CRM minimal 1000 unit per-tahun dalam periode 5 (lima) "
    "tahun terakhir (2021-2025)."
)

EMAILS = (
    "pfad@btn.co.id cc: nipdpfad.btn@gmail.com; hanif.muhammad@btn.co.id; "
    "rahmad.budi@btn.co.id; abdul.shohib@btn.co.id; bernardus_jawan@btn.co.id; "
    "arfan.ripani@btn.co.id; nabil.abdi@btn.co.id; satrio.wibowo@btn.co.id; "
    "faza.junaedy@btn.co.id; fauzan.henanda@btn.co.id; lamsihar.marbun@btn.co.id; "
    "benedictus.nugroho@btn.co.id"
)

JADWAL = (
    "2.2. Pendaftaran pengadaan disampaikan peserta melalui e-mail panitia ke alamat "
    + EMAILS
    + ", dengan jadwal sebagai berikut: Hari/Tanggal : Selasa s.d. Jumat/17 s.d. 20 "
    "November 2026 (hari kerja) Pukul : 08:00 WIB s.d. 16:00 WIB"
)


def test_syarat_pengalaman_bukan_volume():
    assert "volume" not in extract_fields(SYARAT)


def test_volume_lingkup_pekerjaan_tetap_terbaca():
    text = SYARAT + " Lingkup pekerjaan meliputi 500 (lima ratus) Unit mesin ATM."
    assert extract_fields(text)["volume"] == "500 unit"
