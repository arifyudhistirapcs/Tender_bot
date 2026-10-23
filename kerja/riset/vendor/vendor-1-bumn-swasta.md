# Registrasi vendor bank: Kelompok 1 (BUMN + swasta KBMI 3-4)

Riset untuk Arif, 23 Oktober 2026: di mana dan bagaimana perusahaan mendaftar sebagai vendor/rekanan agar bisa diundang tender EDC/managed service EDC. Hanya membaca; tidak ada login, registrasi, atau pengisian formulir. Melengkapi `O:\Work\Tender Bot\kerja\riset\riset-eproc-bank-edc.md`; temuan yang sudah pasti di sana tidak diulang, hanya dirujuk.

Status: SELESAI, dengan keterbatasan (lihat bagian akhir).

## Ringkasan

1. Hanya SMBC Indonesia yang punya halaman pendaftaran rekanan yang benar-benar terbaca: [eprocsmbci.pengadaan.com/index.php/registrasi](https://eprocsmbci.pengadaan.com/index.php/registrasi) di portal iProc Extranet. Login vendor memakai akun vendor.pengadaan.com. Portal yang sama punya halaman [Pengumuman Pelelangan](https://eprocsmbci.pengadaan.com/index.php/welcome/lelang) yang terbuka tanpa login, tetapi tabelnya kosong saat dibuka. [PORTAL]
2. BRI dan BTN punya jalur daftar online yang sudah dipastikan riset sebelumnya: akun BRI dibuat di tdronline.bri.co.id, BTN di e2eprocreg.btn.co.id. Hari ini keduanya hanya memberi halaman kosong ke alat riset dan halaman tantangan bot Imperva Incapsula ke HTTP biasa, jadi syarat dokumennya tetap belum terbaca. [RISET-LALU] [TERBATAS]
3. Portal baru yang ditemukan lewat uji DNS (alamatnya ada, isinya belum terbaca): BSI [rekanan.bankbsi.co.id](https://rekanan.bankbsi.co.id/) (Incapsula) dan BNI [e-proc.bni.co.id](https://e-proc.bni.co.id/) (HTTP 503, Incapsula), ditambah eprocurement.bni.co.id dan eauction.bni.co.id yang tidak bisa dihubungi. Fungsinya disimpulkan dari nama subdomain. [TERBATAS] [INFERENSI]
4. Bank Mandiri dan sembilan bank swasta lain (BCA, CIMB Niaga, Danamon, PermataBank, Maybank Indonesia, OCBC Indonesia, Panin, Bank Mega, UOB Indonesia): portal registrasi vendor publik tidak ditemukan. Danamon punya procurement.danamon.co.id, tetapi alamat itu langsung dialihkan ke login Microsoft perusahaan, jadi kemungkinan aplikasi internal staf. [TIDAK DITEMUKAN] / [INFERENSI]
5. Langkah tercepat: Arif atau koordinator membuka lima portal Incapsula (tdronline BRI, eproc BRI, e2eprocreg BTN, rekanan BSI, e-proc BNI) dengan browser biasa untuk membaca syarat pendaftaran. Bank yang tidak punya portal ditanya langsung lewat bagian pengadaan atau relasi bisnisnya.

## Label bukti

- [PORTAL] halaman resmi bank/portal dibuka langsung dalam riset ini.
- [RISET-LALU] fakta dari `riset-eproc-bank-edc.md` (23 Okt 2026), termasuk yang di sana berlabel [KOORDINATOR]; tidak diulang.
- [DNS] nama host terbukti ada lewat resolusi DNS dari mesin Arif; isi belum tentu terbaca.
- [SNIPPET] hanya terlihat di cuplikan hasil pencarian.
- [INFERENSI] kesimpulan peneliti, bukan yang tertulis di sumber.
- [TERBATAS] dicoba dibuka, isi tidak terbaca (tantangan bot, 503, gagal koneksi, login).
- [TIDAK DITEMUKAN] tidak ketemu dalam batas riset; bukan bukti tidak ada.

## Daftar KBMI

Daftar resmi bank per KBMI tidak ditemukan di situs OJK lewat mesin pencari yang dipakai. Kueri "daftar bank KBMI 3/KBMI 4 OJK" hanya mengembalikan dokumen statistik dan jurnal. Ambang KBMI 3 (modal inti Rp14-70 triliun) dan KBMI 4 (di atas Rp70 triliun) tidak diverifikasi ulang di sini. Satu makalah 2023 di WJARR menyebut kelompok bank modal inti yang mencakup CIMB Niaga, Danamon, Panin, Permata, OCBC NISP, BTPN (kini SMBC Indonesia), Maybank Indonesia, BTN, Mega, dan BSI [SNIPPET]. Cakupan riset ini memakai daftar minimum dari tugas: 5 BUMN (BRI, Bank Mandiri, BNI, BTN, BSI) dan 10 swasta (BCA, CIMB Niaga, Danamon, PermataBank, Maybank Indonesia, OCBC Indonesia, Panin, Bank Mega, SMBC Indonesia, UOB Indonesia). Status KBMI UOB Indonesia belum terverifikasi.

## Tabel ringkas

| Bank | URL registrasi | Cara daftar | Syarat ringkas | Kontak | Tender publik? | Bukti |
|---|---|---|---|---|---|---|
| BRI | Akun: [tdronline.bri.co.id](https://tdronline.bri.co.id/) (tombol "Register as Partner"); login: [eproc.bri.co.id](https://eproc.bri.co.id/) | Online mandiri (buat akun, lalu login iProc Extranet) | Tidak terbaca | HelpdeskIFS@corp.bri.co.id ("iProc Information") [SNIPPET] | Tidak; portal di balik login [RISET-LALU] | [RISET-LALU]; hari ini [TERBATAS] Incapsula |
| Bank Mandiri | Tidak ditemukan | Tidak diketahui; kebijakan menyebut unit khusus yang menyeleksi calon rekanan [SNIPPET] | Tidak terbaca | Tidak tertera | Tidak ditemukan | [TIDAK DITEMUKAN] |
| BNI | Kandidat: [e-proc.bni.co.id](https://e-proc.bni.co.id/); juga eprocurement.bni.co.id, eauction.bni.co.id | Tidak diketahui | Tidak terbaca | Tidak tertera | Tidak diketahui | [DNS] [TERBATAS] (503 Incapsula; dua host lain gagal koneksi) |
| BTN | [e2eprocreg.btn.co.id](https://e2eprocreg.btn.co.id/) (login Oracle EBS "Aplikasi Integrated End to End Procurement") | Online lewat portal; Arif belum punya akun [RISET-LALU] | Tidak terbaca | WA +62 822 5888 2676; helpdesk.e2eproc@btn.co.id [RISET-LALU] | Tidak; portal di balik login | [RISET-LALU]; hari ini [TERBATAS] Incapsula |
| BSI | Kandidat: [rekanan.bankbsi.co.id](https://rekanan.bankbsi.co.id/) | Tidak diketahui | Tidak terbaca | Tidak tertera | Tidak diketahui | [DNS] [TERBATAS] (Incapsula "Request unsuccessful") |
| BCA | Tidak ditemukan | Tidak diketahui | - | Tidak tertera (beranda hanya memuat kontak umum Halo BCA) | Tidak ditemukan | [TIDAK DITEMUKAN] |
| CIMB Niaga | Tidak ditemukan | Tidak diketahui | - | Tidak tertera | Tidak ditemukan | [TIDAK DITEMUKAN] |
| Danamon | Tidak ada portal vendor publik; [procurement.danamon.co.id](https://procurement.danamon.co.id/) dialihkan ke login Microsoft | Tidak diketahui | - | Tidak tertera | Tidak ditemukan | [PORTAL] pengalihan; fungsi internal [INFERENSI] |
| PermataBank | Tidak ditemukan | Tidak diketahui | - | Tidak tertera | Tidak ditemukan | [TIDAK DITEMUKAN] (situs menolak alat otomatis, HTTP 403 [RISET-LALU]) |
| Maybank Indonesia | Tidak ditemukan | Tidak diketahui; grup Maybank memakai sistem eProcurement (data 2012) [SNIPPET] | - | Tidak tertera | Tidak ditemukan | [TIDAK DITEMUKAN] |
| OCBC Indonesia | Tidak ditemukan | Tidak diketahui | - | Tidak tertera | Tidak ditemukan | [TIDAK DITEMUKAN] |
| Panin | Tidak ditemukan | Tidak diketahui | - | Tidak tertera | Tidak ditemukan | [TIDAK DITEMUKAN] (HTTP 403 [RISET-LALU]) |
| Bank Mega | Tidak ditemukan; partners.bankmega.com ada tetapi HTTP 401, fungsinya tidak jelas | Tidak diketahui | - | Tidak tertera | Tidak ditemukan | [TIDAK DITEMUKAN] |
| SMBC Indonesia | [eprocsmbci.pengadaan.com/index.php/registrasi](https://eprocsmbci.pengadaan.com/index.php/registrasi) ("Daftar Rekanan di PT Bank SMBC Indonesia Tbk") | Online mandiri; login iProc Extranet dengan e-mail dan password akun vendor.pengadaan.com | Formulir tidak terbaca (hanya judul "Pendaftaran Rekanan") | Helpdesk platform iProc: +62 88298906093, cs@pengadaan.com (pengelola platform, bukan bank) | Ya, ada halaman [Pengumuman Pelelangan](https://eprocsmbci.pengadaan.com/index.php/welcome/lelang); tabel kosong saat dibuka | [PORTAL] |
| UOB Indonesia | Tidak ditemukan | Tidak diketahui | - | Tidak tertera | Tidak ditemukan | [TIDAK DITEMUKAN] |

## Catatan per bank

### BRI

- Jalur daftar dari riset sebelumnya: akun dibuat di tdronline.bri.co.id lewat tombol "Register as Partner", lalu dipakai untuk login di eproc.bri.co.id (iProc Extranet) [RISET-LALU]. Judul tdronline di indeks pencarian adalah "Brifamp" [SNIPPET]. "TDR" kemungkinan singkatan Tanda Daftar Rekanan, istilah umum pendaftaran vendor di BUMN [INFERENSI].
- Hasil pencarian untuk eproc.bri.co.id memuat baris "iProc Information: HelpdeskIFS@corp.bri.co.id" [SNIPPET]. Alamat ini belum dicocokkan dengan halaman yang terbuka penuh.
- Hari ini alat riset hanya mendapat halaman kosong dari kedua host, dan HTTP biasa dari mesin Arif mendapat halaman tantangan bot Imperva Incapsula (iframe `/_Incapsula_Resource`) [TERBATAS]. Blokir ini tidak diakali.
- Syarat dokumen tidak terbaca.

### Bank Mandiri

- Tidak ada portal vendor yang ditemukan. Uji DNS 32 nama host (antara lain eproc, eprocurement, e-procurement, procurement, vendor, vms, supplier, rekanan, mitra, tender, etender, extranet, partner, ariba) di bankmandiri.co.id: tidak satu pun yang ada.
- Kebijakan Pengadaan Barang dan Jasa (PDF, versi Inggris) menyebut pemisahan fungsi: ada unit yang melakukan seleksi calon mitra/vendor, unit proses pengadaan, unit penyusun HPS, dan unit kepatuhan; SPO pengadaan diperbarui 1 Maret 2017 [SNIPPET]. Teks itu tidak menyebut portal pendaftaran mandiri. Vendor kemungkinan masuk lewat seleksi atau undangan [INFERENSI].
- Riset sebelumnya: lelang.bankmandiri.co.id kemungkinan lelang agunan, bukan pengadaan [RISET-LALU].

### BNI

- Uji DNS menemukan tiga host yang ada [DNS]:
  - e-proc.bni.co.id, di belakang Imperva; menjawab HTTP 503 ke alat riset dan ke mesin Arif, dan isi yang diterima mesin Arif adalah tantangan Incapsula [TERBATAS].
  - eprocurement.bni.co.id dan eauction.bni.co.id, keduanya mengarah ke IP 175.106.21.17; port 443 dan 80 tidak bisa dihubungi dalam 6 detik dari mesin Arif [TERBATAS]. Kemungkinan dibatasi untuk jaringan tertentu [INFERENSI].
- URL e-proc.bni.co.id dan eprocurement.bni.co.id muncul di indeks pencarian tanpa judul atau isi [SNIPPET].
- Nama host mengarah ke e-procurement dan e-auction, tetapi isinya belum pernah terbaca. Perlu dibuka manual di browser biasa.

### BTN

- Portal [e2eprocreg.btn.co.id](https://e2eprocreg.btn.co.id/) dialihkan ke login Oracle E-Business Suite "Aplikasi Integrated End to End Procurement"; helpdesk WhatsApp +62 822 5888 2676 dan email helpdesk.e2eproc@btn.co.id [RISET-LALU]. Akhiran "reg" pada nama host kemungkinan berarti registrasi [INFERENSI].
- Hari ini alat riset mendapat halaman kosong dan HTTP biasa dari mesin Arif mendapat tantangan Incapsula [TERBATAS]. Kueri syarat registrasi e2eproc tidak menemukan apa pun.
- Cara tercepat mendapat syarat dokumen: tanya helpdesk di atas.

### BSI

- Uji DNS menemukan [rekanan.bankbsi.co.id](https://rekanan.bankbsi.co.id/) [DNS], di belakang Imperva. Alat riset mendapat "Request unsuccessful. Incapsula incident ID ..."; mesin Arif mendapat halaman tantangan Incapsula [TERBATAS]. URL ini juga ada di indeks pencarian tanpa isi [SNIPPET].
- "Rekanan" berarti mitra/vendor, jadi ini kandidat terkuat portal vendor BSI [INFERENSI]. Belum terbukti.
- Riset sebelumnya: eproc.bankbsi.co.id gagal koneksi; span.bankbsi.co.id kemungkinan layanan perbendaharaan negara, bukan pengadaan [RISET-LALU].

### BCA

- Beranda bca.co.id dibuka: tidak ada tautan pengadaan, vendor, atau supplier; yang tertera hanya kontak umum (Halo BCA 1500888, halobca@bca.co.id) [PORTAL]. Kontak itu tidak spesifik untuk vendor.
- Uji DNS 30 nama host di bca.co.id: tidak satu pun yang ada.

### CIMB Niaga

- Bagian beranda yang terbaca tidak memuat tautan pengadaan [PORTAL, sebagian]. Uji DNS 30 nama host: tidak satu pun yang ada.
- Riset sebelumnya hanya menemukan Vendor Code of Conduct grup CIMB [RISET-LALU]. Pencarian halaman supplier registration grup CIMB tidak menemukan apa pun.

### Danamon

- [procurement.danamon.co.id](https://procurement.danamon.co.id/) ada [DNS] dan dialihkan ke halaman "Sign in to your account" di login.microsoftonline.com, lewat Azure AD Application Proxy [PORTAL]. Pola ini lazim untuk aplikasi internal yang hanya bisa dipakai akun perusahaan, jadi kemungkinan bukan pintu pendaftaran vendor [INFERENSI].
- Bagian beranda yang terbaca tidak memuat tautan pengadaan [PORTAL, sebagian].

### PermataBank

- Uji DNS 30 nama host di permatabank.com: tidak satu pun yang ada. Pencarian hanya mengembalikan halaman pendaftaran merchant PermataQR, yang bukan pendaftaran vendor [SNIPPET]. Situs menolak alat otomatis (HTTP 403) [RISET-LALU].

### Maybank Indonesia

- Beranda dibuka: tidak ada tautan pengadaan [PORTAL]. Uji DNS 30 nama host di maybank.co.id: tidak satu pun yang ada.
- Grup Maybank memakai sistem eProcurement menurut studi kasus MyBiz (data 2012) dan punya Sustainable Procurement Principles [SNIPPET]. Tidak ada tautan pendaftaran untuk Indonesia.

### OCBC Indonesia

- Uji DNS 33 nama host di ocbc.id dan ocbcnisp.com: tidak satu pun yang ada. Pencarian tidak menemukan halaman vendor. Riset sebelumnya hanya menemukan Supplier Code of Conduct grup OCBC [RISET-LALU].

### Panin

- Uji DNS 30 nama host di panin.co.id: tidak satu pun yang ada. Situs menolak alat otomatis (HTTP 403) [RISET-LALU].

### Bank Mega

- Uji DNS menemukan partners.bankmega.com [DNS], yang menjawab HTTP 401 (butuh otentikasi) tanpa isi. Tidak ada bukti bahwa ini portal vendor; bisa juga layanan API mitra bisnis [INFERENSI]. Nama host lain di bankmega.com tidak ada.

### SMBC Indonesia (eks BTPN)

- Portal vendor (iProc Extranet): [eprocsmbci.pengadaan.com](https://eprocsmbci.pengadaan.com/), berjudul "Procurement PT Bank SMBC Indonesia Tbk" [PORTAL]. Isi yang terbaca:
  - tombol "Daftar Rekanan di PT Bank SMBC Indonesia Tbk", menuju `/index.php/registrasi`; halaman itu hanya menampilkan judul "Pendaftaran Rekanan" ke alat riset, formulirnya tidak terbaca;
  - "Gunakan e-mail dan password dari vendor.pengadaan.com", jadi login vendor memakai akun di platform pengadaan.com;
  - tautan "Daftar Rekanan di pengadaan.com" menuju `vmsextra-staging.pengadaan.com`. Kata "staging" biasanya berarti server uji, jadi tautan ini sebaiknya dikonfirmasi ke bank sebelum dipakai [INFERENSI];
  - CAPTCHA di form login;
  - footer: "Dikembangkan oleh ADW Consulting untuk PT Bank SMBC Indonesia Tbk", bertaut ke btpn.com.
- Halaman [Pengumuman Pelelangan](https://eprocsmbci.pengadaan.com/index.php/welcome/lelang) terbuka tanpa login, dengan kolom Nomor Pengadaan, Judul Pekerjaan, Pembukaan Pendaftaran, Penutupan Pendaftaran, dan Aksi, plus bagian "10 Lelang Terakhir". Kedua tabel kosong saat dibuka; datanya mungkin dimuat JavaScript, atau memang belum ada lelang [TERBATAS]. Bagi Tender Bot, ini calon sumber tier 1 yang perlu dicek ulang dengan browser.
- smbci.pengadaan.com dan iprocsmbci.pengadaan.com adalah "iProc Intranet" untuk staf, bukan pintu vendor [PORTAL]. Helpdesk yang tertera di sana (+62 88298906093, cs@pengadaan.com) milik platform iProc/pengadaan.com.
- vendor.pengadaan.com menjawab HTTP 400 ke alat riset [TERBATAS].
- Kepemilikan: dibuktikan klaim footer dan tautan ke btpn.com. Tautan dari smbci.com ke portal ini belum ditemukan.

### UOB Indonesia

- Uji DNS 30 nama host di uob.co.id: tidak satu pun yang ada. Pencarian tidak menemukan halaman vendor.

## Saran langkah

- Buka manual di browser biasa (bukan bot) dan catat syarat pendaftarannya, tanpa mendaftar dulu: tdronline.bri.co.id, eproc.bri.co.id, e2eprocreg.btn.co.id, rekanan.bankbsi.co.id, e-proc.bni.co.id.
- SMBC Indonesia: putuskan apakah mendaftar lewat `/index.php/registrasi`. Konfirmasi dulu ke bank soal tautan `vmsextra-staging`.
- BTN: minta daftar syarat dokumen ke helpdesk.e2eproc@btn.co.id.
- BRI: konfirmasi HelpdeskIFS@corp.bri.co.id sebagai kontak iProc sebelum dipakai, karena baru terlihat di cuplikan pencarian.
- Bank Mandiri, BCA, CIMB Niaga, Danamon, PermataBank, Maybank Indonesia, OCBC Indonesia, Panin, Bank Mega, UOB Indonesia: tanyakan prosedur pendaftaran rekanan ke bagian pengadaan atau lewat relationship manager bank. Portal publik tidak ditemukan.

## Keterbatasan

- Lima portal BUMN memakai tantangan bot Imperva Incapsula. Alat riset dan HTTP biasa tidak bisa melewatinya, dan blokir itu sengaja dihormati, jadi isi dan syarat pendaftaran BRI, BTN, BNI, dan BSI tidak terbaca.
- Browser otomatis (playwright-cli) tidak dipakai. Perintah `open` ke tdronline.bri.co.id menggantung sekitar 90 menit meski dibungkus batas waktu 60 detik, lalu sesi `vendor-k1` ditutup. Halaman yang dirender JavaScript (formulir registrasi SMBC Indonesia, tabel lelangnya) karena itu tidak terbaca.
- Uji DNS hanya menebak awalan nama host (eproc, eproc2, e-proc, eprocurement, e-procurement, procurement, procure, vendor, vendors, vendorportal, vms, vmsextra, supplier, suppliers, supplierportal, rekanan, mitra, pengadaan, tender, etender, e-tender, eauction, srm, scm, sourcing, extranet, partner, partners, ariba, tdr, spe, iproc), dan tidak semua awalan diuji di setiap domain. Portal di domain pihak ketiga (seperti SMBC Indonesia di pengadaan.com) atau dengan nama tak lazim tidak tertangkap. Domain kontrol acak tidak ada satu pun yang resolve, jadi tidak ada wildcard DNS yang memalsukan hasil.
- Mesin pencari lemah untuk sumber Indonesia dan tidak menemukan daftar KBMI resmi OJK. PDF kebijakan pengadaan hanya terbaca sebagai cuplikan.
- Beranda CIMB Niaga dan Danamon hanya terbaca sebagian (terpotong).
- "Tidak ditemukan" di sini berarti tidak ketemu dalam batas riset sekitar 50 menit, bukan bukti bank tidak menerima pendaftaran vendor.

## Daftar URL dan tanggal akses

Semua diakses 23 Oktober 2026.

- BRI tdronline: [tdronline.bri.co.id](https://tdronline.bri.co.id/). Tantangan Incapsula; judul "Brifamp" dari cuplikan pencarian.
- BRI eProc: [eproc.bri.co.id](https://eproc.bri.co.id/). Tantangan Incapsula; cuplikan pencarian "iProc Information: HelpdeskIFS@corp.bri.co.id".
- BTN e2eproc: [e2eprocreg.btn.co.id](https://e2eprocreg.btn.co.id/). Tantangan Incapsula.
- BNI e-proc: [e-proc.bni.co.id](https://e-proc.bni.co.id/). HTTP 503 (Incapsula).
- BNI eprocurement: [eprocurement.bni.co.id](https://eprocurement.bni.co.id/). DNS ada; koneksi gagal.
- BNI eauction: [eauction.bni.co.id](https://eauction.bni.co.id/). DNS ada; koneksi gagal.
- BSI rekanan: [rekanan.bankbsi.co.id](https://rekanan.bankbsi.co.id/). Incapsula "Request unsuccessful".
- Bank Mandiri, Kebijakan Pengadaan Barang dan Jasa (English), PDF: [bankmandiri.co.id](https://www.bankmandiri.co.id/documents/38268824/42739631/Kebijakan+Pengadaan+Barang+dan+Jasa+(english).pdf/063e2ffa-5931-226e-e965-2faed3dbe524). Cuplikan pencarian.
- BCA, beranda: [bca.co.id/id](https://www.bca.co.id/id). Dibuka.
- CIMB Niaga, beranda: [cimbniaga.co.id](https://www.cimbniaga.co.id/id/personal/index). Dibuka sebagian.
- Danamon, beranda: [danamon.co.id](https://www.danamon.co.id/). Dibuka sebagian.
- Danamon procurement: [procurement.danamon.co.id](https://procurement.danamon.co.id/). Dialihkan ke login Microsoft.
- PermataBank, bergabung menjadi merchant: [permatabank.com](https://www.permatabank.com/id/digital-channel/permataqr/bergabung-menjadi-merchant). Cuplikan pencarian.
- Maybank Indonesia, beranda: [maybank.co.id](https://www.maybank.co.id/). Dibuka.
- MyBiz, studi kasus eProcurement Maybank, PDF: [mybiz.net](https://www.mybiz.net/_files/ugd/c29f77_aa494836ecc64a39bda6d27ee782e421.pdf). Cuplikan pencarian.
- Maybank Group Sustainable Procurement Principles (salinan BankTrack): [banktrack.org](https://www.banktrack.org/download/sustainable_procurement_principles). Cuplikan pencarian.
- Bank Mega partners: [partners.bankmega.com](https://partners.bankmega.com/). HTTP 401.
- SMBC Indonesia, iProc Extranet: [eprocsmbci.pengadaan.com](https://eprocsmbci.pengadaan.com/). Dibuka.
- SMBC Indonesia, Pendaftaran Rekanan: [eprocsmbci.pengadaan.com/index.php/registrasi](https://eprocsmbci.pengadaan.com/index.php/registrasi). Dibuka; hanya judul.
- SMBC Indonesia, Pengumuman Lelang: [eprocsmbci.pengadaan.com/index.php/welcome/lelang](https://eprocsmbci.pengadaan.com/index.php/welcome/lelang). Dibuka; tabel kosong.
- SMBC Indonesia, iProc Intranet: [smbci.pengadaan.com](https://smbci.pengadaan.com/). Dibuka.
- SMBC Indonesia, iProc Intranet: [iprocsmbci.pengadaan.com](https://iprocsmbci.pengadaan.com/). Halaman login; judul lewat HTTP.
- pengadaan.com, akun vendor: [vendor.pengadaan.com](https://vendor.pengadaan.com/). HTTP 400.
- pengadaan.com, tautan "Daftar Rekanan di pengadaan.com": [vmsextra-staging.pengadaan.com](https://vmsextra-staging.pengadaan.com). Tidak dibuka.
- WJARR 2023, makalah kelompok bank modal inti, PDF: [wjarr.com](https://wjarr.com/sites/default/files/fulltext_pdf/WJARR-2023-0983.pdf). Cuplikan pencarian.
- Riset sebelumnya: `O:\Work\Tender Bot\kerja\riset\riset-eproc-bank-edc.md`.
