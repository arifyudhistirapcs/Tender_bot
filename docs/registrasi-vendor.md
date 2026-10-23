# Daftar registrasi vendor bank (untuk Arif)

Disusun 23 Oktober 2026 dari tiga riset di `kerja/riset/vendor/`. Kolom "Cek" berisi tanda ✓ bila koordinator sudah membuka halamannya sendiri: halaman menjawab HTTP 200 dan judulnya cocok. Bila tanpa ✓, data berasal dari riset agen, dan rinciannya ada di file per kelompok.

## 1. Bisa daftar online sekarang

| Bank | Halaman daftar | Cara & syarat ringkas | Kontak | Cek |
|---|---|---|---|---|
| Bank Jatim | https://eprocurement.bankjatim.co.id/main/index/registrasi | Isi NPWP dan email resmi perusahaan, lalu aktivasi lewat email. Tender diumumkan di portal ini. | vendormanagement@bankjatim.co.id | ✓ |
| Bank Sumsel Babel | https://eproc.banksumselbabel.com/index.php/homepage/register.shtml | Dokumen: NIB, NPWP, SPPKP, akta, SPT 1771, neraca, bukti pengalaman (kontrak), daftar peralatan. Keanggotaan gugur bila 2 tahun tidak ikut lelang. | e-Proc@banksumselbabel.com, 0711 5228080 | ✓ |
| Bank Sulselbar | https://eproc.banksulselbar.co.id/register | Wajib terdaftar sebelum ikut tender apa pun. Dokumen: akta, NIB, NPWP + PKP, laporan keuangan 2 tahun. Untuk jasa TI: patuh POJK 11/2022. | lihat file kelompok 3 | ✓ |
| Bank Sultra | https://e-tender.banksultra.co.id/auth/register | Daftar online. Akun baru aktif setelah direktur membawa dokumen asli (KTP, NPWP, akta, surat tidak masuk daftar hitam) ke kantor di Kendari. | barangjasa@banksultra.co.id | ✓ |
| SMBC Indonesia | https://eprocsmbci.pengadaan.com/index.php/registrasi | Login memakai akun vendor.pengadaan.com. Salah satu tautannya mengarah ke server uji, jadi konfirmasi dulu ke bank. | — | ✓ |
| Bank Sulteng | https://eproc.banksulteng.co.id/#/daftar | Satu kali daftar berlaku untuk semua tender. Kode halaman berlabel "UAT", jadi konfirmasi dulu ke bank. | — | ✓ (portal aktif) |

## 2. Portal ada, syarat belum terbaca: buka manual di Chrome

| Bank | Portal | Catatan |
|---|---|---|
| BRI | https://tdronline.bri.co.id/ (daftar akun) → https://eproc.bri.co.id/ (login) | Dilindungi penghalang bot Incapsula. Helpdesk HelpdeskIFS@corp.bri.co.id belum terverifikasi. |
| BTN | https://e2eprocreg.btn.co.id/ | Login Oracle EBS. Helpdesk WA +62 822 5888 2676, helpdesk.e2eproc@btn.co.id. |
| BSI | https://rekanan.bankbsi.co.id/ | Portal aktif. Fungsinya baru disimpulkan dari nama alamat. |
| BNI | https://e-proc.bni.co.id/ | Menjawab HTTP 503 ("tidak tersedia") saat dicek. |
| bank bjb | https://eproc.bankbjb.co.id/ | Judul halaman "e-Procurement Promise". Ada menu pendaftaran di kode aplikasi. |

## 3. Daftar per tender, tanpa database vendor tetap

| Bank | Cara | Kontak |
|---|---|---|
| Bank Sumut | Datang langsung ke kantor pusat Medan untuk setiap tender. | 061-4515100 / 061-4155100 ext. 1623 |
| BPD Bali | Lewat email atau datang langsung. Tender diumumkan di menu "Pengumuman", bukan "Info Lelang". | pgn.uma@bpdbali.co.id |
| Bank NTB Syariah | Email plus surat minat bermeterai. | lihat file kelompok 3 (alamat resmi memakai gmail) |
| Bankaltimtara | Kirim formulir keikutsertaan. | tender@bankaltimtara.co.id |
| Bank Papua | Datang langsung ke kantor pusat Jayapura. | — |

## 4. Portal tidak ditemukan: tanyakan ke bagian pengadaan

Bank Mandiri, BCA, CIMB Niaga, PermataBank, Maybank Indonesia, OCBC Indonesia, Panin, Bank Mega, UOB Indonesia, Danamon (procurement.danamon.co.id ternyata login internal staf).

BPD: Bank Aceh Syariah, Bank Bengkulu, Bank Lampung, Bank Jateng, Bank Banten, Bank Nagari, Bank Jambi, BPD DIY, Bank Kalsel, Bank Kalteng, Bank Maluku Malut. Bank Banten, Nagari, Jambi, DIY, Kalsel, dan Kalteng memasang pengumuman tender di situsnya, tetapi jalur daftarnya tidak ditemukan.

Belum bisa diperiksa: BRKS (situs gagal diakses), Bank Jakarta (HTTP 403), Bank NTT (situs sedang perbaikan), Bank SulutGo (tautan lelangnya hanya ke Instagram).

## Tender relevan yang ditemukan sambil riset

- **Bank Sumut, Smart EDC:**
  - Nomor 005/LPd-PP/SMRT-EDC-BS/L/2026, HPS Rp6.993.000.000, 500 unit, kontrak 36 bulan.
  - Pendaftaran 13–23 Oktober 2026 dan sudah ditutup.
  - Lampiran resmi: `kerja/riset/vendor/lampiran-banksumut-smart-edc-005-2026.pdf` (✓).
- **Bank Jatim:** Market Sounding Pengadaan Penyedia Jasa Managed Service Perangkat EDC Soundbox (✓ halaman aktif; PDF di folder Mei 2026).
- **Bank Kalteng:** penggantian 56 ATM + 3 CRM, dan "Tender Pengelolaan Mesin ATM/CRM oleh Vendor". Rinciannya ada di Google Drive bank dan belum dibuka.
- **Bank Kalbar:** pemenang outsourcing 14 unit CRM adalah PT Argenta Akhila Utama (diumumkan 25 September 2026).
