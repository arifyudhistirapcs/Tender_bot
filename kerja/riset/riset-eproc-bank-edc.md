# Peta portal e-procurement bank Indonesia dan tender EDC

Riset untuk Tender Bot, 23 Oktober 2026. Untuk Arif dan tim yang membangun bot: bank mana yang bisa dipantau bot, mana yang butuh akun vendor, dan mana yang cukup lewat berita atau email. Bahan: tiga berkas riset (bank BUMN, bank swasta, BPD dan portal agregat) ditambah pemeriksaan ulang oleh koordinator. Semua sumber diakses 23 Oktober 2026.

## Ringkasan

<!-- class: summary -->
1. Bank Sumut sedang menayangkan tender "Pekerjaan Pengadaan Sewa Beli Mesin Smart Electronic Data Capture (Smart EDC)" senilai Rp6.993.000.000, diposting Selasa, 13 Oktober 2026, dengan metode Pelelangan Umum sistem pascakualifikasi. Jadwal dan syaratnya ada di lampiran unduhan yang belum terbaca, jadi batas pendaftarannya belum diketahui. Lampiran itu perlu diunduh manual secepatnya. [KOORDINATOR]
2. Di antara bank BUMN, swasta, dan BPD yang diriset, hanya dua yang daftar tendernya bisa dibaca bot tanpa login: Bank Sumut dan Bank Jatim. Keduanya menayangkan pengumuman sebagai halaman HTML biasa di situs sendiri. Bank Sumut juga punya feed RSS, tetapi isinya belum dicek.
3. Di bank BUMN, hanya portal BRI dan BTN yang terverifikasi, dan keduanya wajib login vendor. Arif belum punya akun vendor BTN. Portal BRI menolak dengan blokir WAF (lapisan pelindung situs yang menyaring klien otomatis) saat dicek koordinator lewat HTTP biasa.
4. Dari 11 bank swasta, tidak satu pun yang ketahuan memasang daftar tender publik. Satu-satunya portal yang teridentifikasi milik SMBC Indonesia (iProc di domain pengadaan.com), dan isinya hanya halaman login.
5. Portal Bank Mandiri, BNI, BSI, dan sebagian besar bank swasta tidak ditemukan. Ini batas riset (tanpa browser, mesin pencari lemah untuk media nasional), bukan bukti portalnya tidak ada. Cara tercepat memastikannya adalah bertanya langsung ke bagian pengadaan bank.
6. Tender EDC bank besar bisa saja tidak pernah diumumkan terbuka. Pengadaan mesin EDC BRI 2020-2024, dengan nilai proyek sekitar Rp2,1 triliun, sedang disidik KPK [KOORDINATOR]. Cuplikan Tempo yang belum terverifikasi menulis bahwa perusahaan lain "were not invited" [SNIPPET]. Untuk bank seperti ini, jalurnya akun vendor, email undangan, dan berita.
7. Usulan untuk bot: tier 1 dipantau otomatis (Bank Sumut, Bank Jatim), tier 2 lewat akun vendor (BRI, BTN, SMBC Indonesia), tier 3 lewat berita, email, dan alert (bank lainnya). Kata "lelang" saja tidak boleh jadi penanda tender, karena beberapa bank memakainya untuk lelang agunan.
8. Syarat penggunaan (ToS) belum dicek di situs mana pun. Beberapa bank menolak klien otomatis: PermataBank, Panin, dan Bank Jakarta dengan HTTP 403, BRI dengan WAF. Bot harus menghormati blokir itu, bukan mengakalinya.

## Label sumber

Setiap klaim diberi label asal buktinya.

<!-- class: legend -->
- [KOORDINATOR] dicek ulang langsung oleh koordinator pada 23 Oktober 2026, lewat Chrome Arif atau dengan membuka halamannya.
- [PORTAL] halaman situs atau portal resmi bank yang dibuka langsung oleh peneliti.
- [BERITA] berita atau halaman pihak ketiga yang dibuka penuh.
- [SNIPPET] hanya terlihat di cuplikan hasil pencarian; halaman aslinya tidak terbuka.
- [INFERENSI] kesimpulan peneliti dari bukti yang ada, bukan yang tertulis di sumber.
- [TERBATAS] halamannya dicoba dibuka, tetapi isinya tidak terbaca karena dirender JavaScript, diblokir, atau butuh login.

"Tidak ditemukan" berarti tidak ketemu dalam batas riset, bukan bukti tidak ada.

## Peta portal per bank

Kolom "Tender EDC" hanya mencatat yang ditemukan dalam riset ini. Domain bertanda "tebakan" adalah alamat yang ditebak dari pola umum, bukan dari tautan resmi.

### Bank BUMN

<!-- class: banks -->
| Bank | Portal | Akses publik | Format | Catatan teknis bot | Tender EDC |
|---|---|---|---|---|---|
| BRI | [eproc.bri.co.id](https://eproc.bri.co.id/) (iProc Extranet); akun dibuat di [tdronline.bri.co.id](https://tdronline.bri.co.id/) [PORTAL] | Tidak. Halaman depan langsung form login [PORTAL] | Tidak ada daftar tender publik; RSS/API tidak ditemukan | Dicek lewat HTTP, dijawab blokir WAF Incapsula ("Request unsuccessful") [KOORDINATOR]. Peneliti sempat membaca form login pada percobaan kedua. robots.txt 404 [PORTAL]. Ada tombol "Refresh" di form login, kemungkinan CAPTCHA [INFERENSI] | Ya, lewat berita: kasus KPK pengadaan mesin EDC 2020-2024 [KOORDINATOR] |
| Bank Mandiri | Tidak ditemukan. `eproc.bankmandiri.co.id` (tebakan) gagal koneksi [PORTAL]; [lelang.bankmandiri.co.id](https://lelang.bankmandiri.co.id/) kemungkinan lelang agunan [INFERENSI] | Tidak diketahui | Kebijakan pengadaan hanya berupa PDF [SNIPPET] | Perlu pembaca PDF. Subdomain lelang kosong saat dibuka karena dirender JavaScript | Tidak ditemukan |
| BNI | Tidak ditemukan. `eproc.bni.co.id` (tebakan) gagal koneksi [PORTAL] | Tidak diketahui | Tidak ditemukan | Beranda tidak memuat teks pengadaan [PORTAL]. Kata "BNI" tercampur Business Network International | Tidak ditemukan |
| BTN | [e2eprocreg.btn.co.id](https://e2eprocreg.btn.co.id/), dialihkan ke login Oracle E-Business Suite "Aplikasi Integrated End to End Procurement" [KOORDINATOR] | Tidak. Hanya form User Name/Password dan tautan lupa sandi. Arif belum punya akun vendor [KOORDINATOR] | Tidak ada daftar tender publik; RSS/API tidak ditemukan | Path `/OA_HTML/AppsLocalLogin.jsp`. Browser otomatis sempat menggantung, jadi wajib batas waktu keras. robots.txt belum dicek. Subdomain b-gov dan emitra berjudul "Request Rejected" [SNIPPET] | Tidak ditemukan, termasuk lewat 5 kueri tambahan |
| BSI | Tidak ditemukan. `eproc.bankbsi.co.id` (tebakan) gagal koneksi [PORTAL]; [span.bankbsi.co.id](https://span.bankbsi.co.id/) fungsinya belum jelas, kemungkinan layanan perbendaharaan negara, bukan pengadaan [INFERENSI] | Tidak diketahui | Tidak ditemukan | Kata "BSI" tercampur BSI Group, yang juga memakai istilah Electronic Data Capture untuk uji klinis | Tidak ditemukan |
| Anak usaha (Bank Mandiri Taspen, BRILink) | Tidak ditemukan. BRILink adalah program agen BRI, jadi pengadaan EDC-nya diperkirakan lewat BRI [INFERENSI] | Tidak diketahui | Tidak ditemukan | Belum ada target | Tidak ditemukan |

### Bank swasta

<!-- class: banks -->
| Bank | Portal | Akses publik | Format | Catatan teknis bot | Tender EDC |
|---|---|---|---|---|---|
| BCA | Tidak ditemukan. `eproc.bca.co.id` (tebakan) gagal koneksi [PORTAL] | Tidak diketahui | Tidak diketahui | robots.txt tidak memuat path pengadaan [PORTAL]; situs berbasis Sitecore [INFERENSI] | Tidak ditemukan |
| CIMB Niaga | Tidak ditemukan. Yang ada hanya Vendor Code of Conduct grup CIMB [SNIPPET] | Tidak diketahui | Tidak diketahui | robots.txt melarang path internal Adobe Experience Manager; halaman HTML bisa diambil [PORTAL] | Tidak ditemukan |
| Danamon | Tidak ditemukan | Tidak diketahui | Tidak diketahui | robots.txt "Allow: /" [PORTAL] | Tidak ditemukan |
| PermataBank | Tidak ditemukan | Tidak diketahui | Tidak diketahui | HTTP 403 untuk alat otomatis, termasuk robots.txt [PORTAL]. Blokir ini dihormati, tidak diakali | Tidak ditemukan |
| Maybank Indonesia | Tidak ditemukan. Grup Maybank punya sistem eProcurement menurut studi kasus vendor dengan data tahun 2012 [SNIPPET] | Tidak diketahui | Tidak diketahui | robots.txt hanya melarang `/sitecore` [PORTAL]; halaman NewsAndAnnouncement terindeks publik [SNIPPET] | Tidak ditemukan |
| OCBC Indonesia | Tidak ditemukan. Yang ada hanya Supplier Code of Conduct grup OCBC [SNIPPET] | Tidak diketahui | Tidak diketahui | robots.txt melarang semua URL ber-query (`Disallow: /*?`) [PORTAL] | Tidak ditemukan |
| Panin Bank | Tidak ditemukan | Tidak diketahui | Tidak diketahui | HTTP 403 untuk alat otomatis di seluruh situs [PORTAL] | Tidak ditemukan |
| Bank Mega | Tidak ditemukan. Menu "Catalog of AYDA" adalah katalog agunan, bukan tender [PORTAL] | Tidak diketahui | Tidak diketahui | robots.txt hanya melarang `/admin/`; halaman terbaca sebagai HTML biasa [PORTAL] | Tidak ditemukan |
| SMBC Indonesia (eks BTPN) | [iprocsmbci.pengadaan.com](https://iprocsmbci.pengadaan.com/) dan [smbci.pengadaan.com](https://smbci.pengadaan.com/), platform iProc di domain pihak ketiga [PORTAL] | Tidak. Hanya form login iProc Intranet, tampaknya untuk staf internal [PORTAL] | Tidak terlihat tanpa login | robots.txt 404. Kepemilikan hanya klaim di footer portal; belum ada tautan dari situs resmi bank | Tidak ditemukan |
| UOB Indonesia (riset singkat) | Tidak ditemukan | Tidak diketahui | Tidak diketahui | robots.txt 404 [PORTAL] | Tidak dicari mendalam |
| Bank Sinarmas (riset singkat) | Tidak ditemukan | Tidak diketahui | Tidak diketahui | Situs gagal koneksi dari alat riset [PORTAL] | Tidak dicari mendalam |

### Bank pembangunan daerah (BPD)

<!-- class: banks -->
| Bank | Portal | Akses publik | Format | Catatan teknis bot | Tender EDC |
|---|---|---|---|---|---|
| Bank Sumut | [Pengadaan Barang & Jasa](https://www.banksumut.co.id/pengadaan-barang-jasa/) dan [arsip](https://www.banksumut.co.id/archive-jasa-barang/) [PORTAL] | Ya, tanpa login | WordPress; tiap pengumuman adalah post `jasa_barang` berisi ringkasan HTML dan lampiran unduhan | `/feed/` menjawab sebagai RSS dan REST `/wp-json/wp/v2/jasa_barang` menjawab JSON; isi keduanya belum terbaca [TERBATAS]. HTML server-side, tanpa CAPTCHA saat dibuka. robots.txt dan ToS belum dicek | Ya. Sewa Beli Mesin Smart EDC, Rp6.993.000.000, diposting 13 Oktober 2026 [KOORDINATOR] |
| Bank Jatim | [Lelang Pengadaan](https://www.bankjatim.co.id/id/informasi/lelang-pengadaan) [PORTAL] | Ya untuk membaca. Pendaftaran peserta secara luring di kantor pusat Surabaya (contoh tender 2025) [SNIPPET] | Daftar HTML (tanggal dan judul); isi tiap item di PDF dengan pola `/files/pengumuman/<tahun>/<bulan>/` | Server-side, berhalaman, tanpa CAPTCHA; robots.txt tanpa Disallow [PORTAL]. Pola URL halaman detail belum tertangkap [TERBATAS] | Tidak ditemukan. Ada sewa mesin ATM dan CRM 2022 [SNIPPET] |
| BPD Bali | Menu "INFO LELANG"; URL belum tertangkap [TERBATAS] | Belum diketahui | Menu HTML server-side | Perlu pemetaan URL sekali secara manual; isinya bisa pengadaan atau lelang agunan | Tidak ditemukan |
| Bankaltimtara | Menu "Info Lelang", terpisah dari "Info Lelang Jaminan"; belum dibuka [PORTAL] | Belum diketahui | HTML | Perlu pemetaan URL manual. Bank ini mengoperasikan layanan EDC sendiri [PORTAL] | Tidak ditemukan |
| Bank Nagari | Menu "Informasi Lelang"; URL belum tertangkap [TERBATAS] | Belum diketahui | HTML server-side dengan parameter URL terenkripsi | URL tidak bisa ditebak. Aplikasi Nagari Portal Lelang terpisah, untuk agunan [SNIPPET] | Tidak ditemukan |
| bank bjb | Tidak ditemukan. `eproc.bankbjb.co.id` (tebakan) menampilkan "Please wait a while..." [TERBATAS] | Belum diketahui | Situs dirender JavaScript | Butuh browser headless, atau cukup lewat berita | Tidak ditemukan |
| Bank DKI, kini Bank Jakarta | Tidak ditemukan. Ada sistem pendaftaran calon vendor menurut dokumen pihak ketiga di Scribd [SNIPPET] | Belum diketahui | Tidak terbaca | Domain lama dan baru sama-sama HTTP 403 [TERBATAS]. Domain baru bankjakarta.co.id diumumkan 9 Agustus 2026 [BERITA] | Tidak ditemukan |
| Bank Jateng | Tidak ditemukan. [lelang.bankjateng.co.id](https://lelang.bankjateng.co.id/) adalah lelang agunan [PORTAL] | Belum diketahui | Isi berita dan pengumuman dimuat JavaScript | Beberapa subdomain berjudul "Request Rejected" [SNIPPET] | Tidak ditemukan |
| Bank Kalbar | Tidak ditemukan | Belum diketahui | Tidak terbaca | Subdomain cms berjudul "Request Rejected" [SNIPPET] | Tidak ditemukan |
| Bank Sultra (ditemukan sambil lalu) | [e-tender.banksultra.co.id](https://e-tender.banksultra.co.id/), "Tender Online" [SNIPPET] | Belum dibuka | Belum dibuka | Belum dicek | Tidak dicari |
| Bank Sulteng (ditemukan sambil lalu) | [eproc.banksulteng.co.id](https://eproc.banksulteng.co.id/) [SNIPPET] | Belum dibuka | Belum dibuka | Belum dicek | Tidak dicari |

### Portal agregat dan jalur lain

- SPSE/LPSE dan INAPROC tidak terlihat dipakai BPD. Bank Jatim merujuk keputusan direksinya sendiri dan Bank Sumut merujuk peraturan direksinya sendiri; keduanya mengumumkan di situs sendiri [PORTAL]. Dasar hukumnya belum dicek dari teks peraturan, jadi "BPD tidak wajib SPSE" masih dugaan. Bila suatu saat perlu data SPSE, ada pustaka open source pyproc [SNIPPET].
- TenderKita menampilkan daftar tender secara publik, dari LPSE dan beberapa e-procurement BUMD/BUMN, tetapi tidak ada satu pun bank di daftar instansinya [PORTAL].
- Tender Indonesia mengaku memuat informasi tender lengkap di Indonesia; model langganannya tidak terbaca [TERBATAS]. pengadaan.info, IndoTender, TenderTiger, tenderinfo.org, dan IndonesiaTenders hanya terlihat di hasil pencarian [SNIPPET]. Tidak ada agregator yang terlihat meliput tender bank secara sistematis.
- PaDi UMKM adalah katalog belanja BUMN untuk produk UMKM, bukan portal tender terbuka [SNIPPET]. Portal tender bersama untuk seluruh BUMN tidak ditemukan.
- Iklan tender EDC bank di koran tidak ditemukan. Biro iklan masih menjual slot iklan lelang di Bisnis Indonesia, tetapi itu tidak membuktikan bank memakainya [SNIPPET].
- Bank Indonesia (di luar cakupan, bukan bank umum) mengumumkan pengadaan secara publik dengan kolom Nomor Pengadaan, Nama Pengadaan, Tanggal Pengumuman, Satuan Kerja, Cara Pengadaan, Metode Evaluasi, Pagu, Status, Closing Date, Rekanan Pemenang, dan Lampiran [SNIPPET]. Kolom ini bisa jadi acuan skema data bot.

## Tender dan berita EDC yang ditemukan

### Tender EDC yang sedang terbuka

<!-- class: facts -->
| Butir | Isi |
|---|---|
| Bank | PT Bank Sumut (Perseroda) |
| Judul | Pekerjaan Pengadaan Sewa Beli Mesin Smart Electronic Data Capture (Smart EDC) PT Bank Sumut (Perseroda) |
| Diposting | Selasa, 13 Oktober 2026 |
| Metode | Pelelangan Umum, Sistem Pascakualifikasi |
| Acuan | Peraturan Direksi PT Bank Sumut 007/Dir/DUm-LPd/PBS/2023 tanggal 21 November 2023 |
| Nilai pekerjaan | Rp6.993.000.000 |
| Nomor tender | 005/LPd-PP/SMRT-EDC-BS/L/2026 menurut peneliti. Nomor ini tidak tampil di halaman saat dicek koordinator, jadi belum terverifikasi |
| Jadwal, syarat, HPS rinci | Ada di lampiran unduhan; belum terbaca |
| Status | Masih tayang saat dicek koordinator, 23 Oktober 2026 pukul 15.16 WIB |
| Halaman | [banksumut.co.id, detail tender Smart EDC](https://www.banksumut.co.id/jasa_barang/pekerjaan-pengadaan-sewa-beli-mesin-smart-electronic-data-capture-smart-edc-pt-bank-sumut-perseroda/) |

Semua butir di atas [KOORDINATOR], kecuali nomor tender. Halaman daftar pengadaan Bank Sumut menulis acuan yang sedikit berbeda, No. 007/Dir/Dum-ULP/PBS/2023 tanggal 22 November 2023 [PORTAL]. Selisih kode dan tanggal ini ada di teks bank sendiri.

### Berita EDC: kasus pengadaan mesin EDC BRI

Pengadaan mesin EDC BRI periode 2020-2024 sedang disidik KPK. Menurut Noi English (Pikiran Rakyat Media Network) edisi 6 Juli 2025, nilai proyeknya sekitar Rp2,1 triliun dan dugaan kerugiannya sekitar Rp700 miliar, kira-kira 30%. KPK menyita Rp5,3 miliar tunai dan deposito Rp28 miliar, serta mencekal 13 orang (status per Juli 2025). [KOORDINATOR]

Cuplikan pencarian artikel Tempo English 25 Juli 2025 menulis bahwa penyidik KPK menduga tender diatur agar dimenangkan PT Pasifik Cipta Solusi dan PT Bringin Inti Teknologi, menyebut lima tersangka, dan menulis bahwa perusahaan lain dengan teknologi serupa "were not invited". Halaman Tempo menolak dibuka (HTTP 403) dan artikel Noi tidak memuat hal-hal ini, jadi semuanya belum terverifikasi [SNIPPET]. Nomor tender, skema (beli atau sewa), dan status hukum terbaru juga tidak ditemukan.

Bagi Tender Bot, kasus ini menunjukkan dua hal. Tender EDC bank besar bisa berbentuk undangan yang tidak pernah diumumkan, dan berita penegakan hukum termasuk sedikit jejak publik yang tersisa dari tender semacam itu [INFERENSI].

### Tender sejenis: perangkat kanal, bukan EDC

<!-- class: similar -->
| Bank | Judul | Waktu | Nilai | Sumber |
|---|---|---|---|---|
| Bank Jatim | Procurement of ATM Machine Rental Service | Pendaftaran 29 Juni sampai 5 Juli 2022 | HPS Rp3.118.197 per unit per bulan, termasuk PPN | [PDF pengumuman](https://www.bankjatim.id/files/pengumuman/2022/juni/pengumuman_website_pengadaan_jasa_sewa_mesin_atm_2022_english.pdf) [SNIPPET] |
| Bank Jatim | Pengadaan Jasa Sewa Mesin CRM 2022 | Juli 2022 | Tidak terbaca | [PDF pengumuman](https://www.bankjatim.id/files/pengumuman/2022/juli/pengumuman_website_pengadaan_jasa_sewa_mesin_crm_2022_english.pdf) [SNIPPET] |

### Konteks pasar, bukan tender

- Banyak bank menjalankan aplikasi merchant atau QRIS: Merchant BCA dan info EDC BCA, OCTO Merchant (CIMB Niaga), Merchant QR Danamon, Permata QR Merchant, OCBC Merchant, balé merchant (BTN), dan BYOND Merchant (BSI) [SNIPPET]. Ini tanda bank mengelola armada merchant, bukan bukti tender.
- OCBC meluncurkan Tap Credit Card untuk pembayaran NFC di terminal EDC/POS contactless, menurut rilis PR Newswire 10 November 2025 [SNIPPET].
- Bankaltimtara mengoperasikan layanan EDC sendiri [PORTAL]. Contoh surat penarikan EDC di Scribd ditujukan ke Bank Mega sebagai PIC Merchant Relationship; dokumen pihak ketiga, belum terverifikasi [SNIPPET].
- PT Prima Vista Solusi (PVS) menyediakan layanan EDC, POS, dan payment gateway sejak 2002 menurut akun resminya; profil PitchBook menyebut managed service dan EDC berbasis Android [SNIPPET]. Abstrak kerja praktik mahasiswa UPJ menyebut PVS-WIDE menangani EDC dari Bank Artha Graha, Bank Mandiri, BTPN, PermataBank, dan BNI; tahunnya tidak tercantum [SNIPPET].
- PT Mitra Transaksi Indonesia (Yokke) adalah perusahaan patungan solusi pembayaran yang berdiri 2016 [SNIPPET]. Telkomsel menjual IoT Managed EDC dengan biaya bulanan [SNIPPET]. Ingenico memasarkan terminal Android AXIUM untuk bank dan acquirer di Asia Pasifik [SNIPPET].

### Yang tidak ditemukan

- Berita pemenang tender managed service, pengadaan, sewa, atau pemeliharaan EDC di bank mana pun dalam tiga tahun terakhir.
- Daftar vendor yang sering memenangi tender EDC.
- Tender EDC dari bank swasta mana pun, baik di portal maupun di berita.

## Rekomendasi untuk Tender Bot

Rekomendasi ini kesimpulan dari temuan di atas [INFERENSI]. Satu cara pemantauan tidak cukup untuk semua bank, jadi sumber dibagi tiga tier menurut cara datanya bisa diambil.

### Tier 1: dipantau otomatis

#### Bank Sumut

- Coba feed RSS lebih dulu. `/feed/` menjawab sebagai `application/rss+xml`, tetapi itu feed seluruh situs dan isinya belum dibaca. Feed khusus `/jasa_barang/feed/` belum diuji. REST WordPress `/wp-json/wp/v2/jasa_barang` menjawab JSON, isinya juga belum dibaca [TERBATAS]. Langkah pertama tim: buka ketiganya sekali dan lihat mana yang memuat pengumuman `jasa_barang`.
- Cadangannya, ambil halaman arsip `/archive-jasa-barang/` secara berkala. Pola URL pengumuman: `/jasa_barang/<slug-judul>/`.
- Rincian tender ada di lampiran unduhan. Bot harus mengikuti tautan lampiran itu, yang belum tertangkap oleh alat riset.
- robots.txt dan ToS Bank Sumut belum dicek.

#### Bank Jatim

- Pantau halaman "Lelang Pengadaan", bukan "Pengumuman". Halaman "Pengumuman" berisi promo dan informasi investor.
- Daftarnya HTML server-side dengan paginasi. Tiap item tertaut ke PDF berpola `/files/pengumuman/<tahun>/<bulan>/<nama>.pdf`, juga di domain cermin bankjatim.id, dan ada versi `_english.pdf`. Bot perlu pembaca PDF.
- Jenis item yang terlihat: Pengumuman Tender Pascakualifikasi, Market Sounding, Hasil Rekapitulasi Evaluasi Dokumen Penawaran, dan Pengumuman Pemenang. Bot bisa memilah menurut jenis ini.
- robots.txt tanpa Disallow; ToS belum dicek. Pendaftaran peserta pernah dilakukan luring di kantor pusat, jadi bot cukup memberi tahu dan pendaftaran tetap manual.

Calon tier 1 setelah pemetaan manual: BPD Bali, Bankaltimtara, dan Bank Nagari. Situsnya HTML server-side, tetapi URL menu lelangnya belum tertangkap dan isinya bisa pengadaan atau lelang agunan. Portal Bank Sultra (e-tender) dan Bank Sulteng (eproc) belum dibuka sama sekali.

### Tier 2: butuh akun vendor

- BRI. Akun dibuat di tdronline.bri.co.id lewat tombol "Register as Partner", lalu dipakai untuk login di eproc.bri.co.id. Syarat registrasinya belum terbaca. Portal ini diblokir WAF Incapsula saat dicek lewat HTTP [KOORDINATOR] dan kemungkinan memakai CAPTCHA [INFERENSI], jadi bot sebaiknya membaca email notifikasi, bukan masuk ke portal.
- BTN. Login Oracle E-Business Suite di e2eprocreg.btn.co.id. Arif belum punya akun. Syarat registrasi bisa ditanyakan ke helpdesk: WhatsApp +62 822 5888 2676, email helpdesk.e2eproc@btn.co.id [KOORDINATOR]. Browser otomatis sempat menggantung di portal ini, jadi akses apa pun wajib memakai batas waktu keras.
- SMBC Indonesia. Platform iProc di iprocsmbci.pengadaan.com dan smbci.pengadaan.com. Form yang terlihat berjudul iProc Intranet dan tampaknya untuk staf internal, jadi belum jelas apakah vendor bisa mendaftar di sana. Kepemilikan portal baru berupa klaim di footer; perlu konfirmasi ke bank.
- Registrasi vendor dilakukan manual oleh Arif. Setelah akun ada, bot membantu dengan membaca email undangan dan notifikasi portal. Membaca portal secara otomatis dari dalam sesi vendor harus dicek dulu terhadap syarat penggunaan portal.

### Tier 3: berita, email, dan alert

Tier ini untuk bank yang portalnya tidak ditemukan (Bank Mandiri, BNI, BSI, BCA, CIMB Niaga, Danamon, PermataBank, Maybank Indonesia, OCBC Indonesia, Panin, Bank Mega, UOB Indonesia, Bank Sinarmas) dan BPD yang situsnya dirender JavaScript atau menolak klien otomatis (bank bjb, Bank Jakarta, Bank Jateng, Bank Kalbar).

- Sumber yang bisa dipantau: halaman berita dan pengumuman bank yang terbuka (misalnya NewsAndAnnouncement Maybank Indonesia), rilis pers bank dan vendor EDC, media bisnis, keterbukaan informasi emiten vendor, dan laporan tahunan bank.
- Email undangan setelah terdaftar sebagai vendor.
- Tulis nama lengkap bank di kueri, karena akronimnya bertabrakan: "Bank Negara Indonesia" atau "BBNI", "Bank Syariah Indonesia" atau "BRIS", serta "Bank DKI" dan "Bank Jakarta" sekaligus.
- "EDC" saja tercampur Export Development Canada, Electric Daisy Carnival, dan "everyday carry". Pakai "mesin EDC", "Smart EDC", "EDC Android", "terminal EDC", atau "Electronic Data Capture" bersama nama bank. Untuk jenis pekerjaan: pengadaan, sewa, sewa beli, pemeliharaan, managed service, pengelolaan, dan jasa layanan EDC.
- Untuk Bank Mandiri, BNI, dan BSI, tanyakan alamat portal resmi ke bagian pengadaan, atau buka manual dengan browser biasa.

### Jebakan kata "lelang"

Di bank, "lelang" sering berarti penjualan agunan (jaminan kredit yang diambil alih), bukan pengadaan barang dan jasa. Contoh yang ditemukan:

- lelang.bankjateng.co.id adalah portal lelang agunan [PORTAL].
- lelang.bankmandiri.co.id kemungkinan lelang agunan [INFERENSI].
- Menu "Lelang PT Bank Sumut" (`/lelang/`) terpisah dari "Pengadaan Barang & Jasa". Menu ini belum dibuka dan kemungkinan berisi lelang agunan.
- Bankaltimtara memisahkan "Info Lelang" dari "Info Lelang Jaminan" [PORTAL]. Bank Nagari punya aplikasi Nagari Portal Lelang untuk agunan [SNIPPET]. "Catalog of AYDA" di situs Bank Mega adalah katalog agunan yang diambil alih [PORTAL].

Aturan untuk bot: buang item yang memuat "agunan" atau "jaminan", dan petakan menu pengadaan tiap bank secara eksplisit. Jangan mengandalkan kata "lelang".

### Risiko syarat penggunaan dan robots.txt

- ToS soal scraping belum dicek untuk satu situs pun. Bagian ini harus dibaca sebelum bot berjalan di produksi.
- robots.txt yang sudah dibaca: Bank Jatim tanpa Disallow; Danamon "Allow: /"; Bank Mega hanya melarang `/admin/`; Maybank Indonesia hanya `/sitecore`; BCA dan CIMB Niaga hanya path internal. OCBC Indonesia melarang semua URL ber-query (`/*?`), jadi URL seperti `?page=` atau `?q=` melanggar. eproc BRI, smbci.pengadaan.com, dan UOB Indonesia tidak punya robots.txt (404). robots.txt Bank Sumut dan BTN belum dicek.
- Penolakan klien otomatis: PermataBank dan Panin (HTTP 403 di seluruh situs), Bank Jakarta dan Bank DKI (HTTP 403), BRI (WAF Incapsula, dan "Request Rejected" di www.bri.co.id), beberapa subdomain BTN, Bank Jateng, dan Bank Kalbar ("Request Rejected"), serta eproc.bankbjb.co.id (halaman tantangan "Please wait a while..."). Bot yang patuh tidak mengakali blokir ini. Jalurnya izin resmi, akun vendor, atau berita.
- Untuk portal di balik login (BRI, BTN, SMBC Indonesia), akses otomatis dari dalam sesi vendor bisa melanggar syarat portal.

### Catatan teknis untuk semua sumber

- Pakai batas waktu keras dan retry di setiap request. Fetch pertama eproc BRI kosong lalu berhasil pada percobaan kedua, dan browser otomatis menggantung di portal BTN. Peneliti menyarankan batas 15 sampai 30 detik per request [INFERENSI].
- Kenali halaman blokir dan catat sebagai "tidak tersedia": "Request Rejected", "Request unsuccessful" (Incapsula), "Please wait a while...", dan HTTP 403.
- Pakai renderer JavaScript hanya bila perlu dan selalu dengan batas waktu.
- Siapkan pembaca PDF untuk pengumuman Bank Jatim dan dokumen kebijakan bank.
- Skema data bisa meniru kolom pengumuman Bank Indonesia.

### Keputusan untuk Arif

- Unduh dan baca lampiran tender Smart EDC Bank Sumut, lalu putuskan ikut atau tidak. Batas pendaftarannya belum diketahui.
- Putuskan apakah mendaftar sebagai vendor di BRI dan BTN. Tanpa akun, tender kedua bank ini tidak terlihat oleh bot.
- Tentukan siapa yang menanyakan alamat portal resmi ke Bank Mandiri, BNI, BSI, dan SMBC Indonesia.

## Keterbatasan riset

- Alat riset hanya pencarian web dan pengambilan halaman, tanpa browser, login, registrasi, atau pengisian formulir. Halaman yang dirender JavaScript terbaca kosong (tdronline BRI, lelang Bank Mandiri, span BSI, bank bjb, Bank Jateng), dan isi portal di balik login tidak terlihat.
- Mesin pencari yang dipakai lemah untuk media nasional Indonesia; Kompas, Detik, CNBC Indonesia, Bisnis, Kontan, dan Infobank tidak muncul. "Tidak ditemukan" untuk berita EDC bisa berarti belum terjangkau.
- Alat riset tidak bisa membaca PDF dan sitemap XML. Laporan tahunan, kebijakan pengadaan, dan lampiran tender, termasuk lampiran Bank Sumut, tidak terbaca. Sebagian fakta hanya berasal dari cuplikan pencarian.
- Subdomain `eproc.*` adalah tebakan pola dan gagal koneksi di Bank Mandiri, BNI, BTN, BSI, dan BCA. Portal BTN ternyata memakai `e2eprocreg.`, jadi tebakan pola tidak bisa diandalkan.
- Tiap bagian riset dibatasi sekitar 45 menit. UOB Indonesia dan Bank Sinarmas hanya diriset singkat; Bank Kalbar dan Bankaltimtara dangkal.
- ToS tidak dicek di situs mana pun, dan robots.txt hanya dicek di sebagian situs.
- Nomor tender Bank Sumut belum terverifikasi. Nama pemenang dan jumlah tersangka kasus EDC BRI hanya dari cuplikan Tempo yang belum terverifikasi; halaman Tempo dan BrokerChooser menolak dibuka (HTTP 403).
- Isi feed RSS dan REST JSON Bank Sumut belum dibaca.
- Syarat registrasi vendor BRI dan BTN belum diketahui.
- Dasar hukum pengadaan BUMD dan model harga agregator berbayar belum diverifikasi.

## Daftar sumber

Semua sumber diakses 23 Oktober 2026. Keterangan di akhir tiap baris menyebut cara sumber itu dibaca.

### Dicek ulang oleh koordinator

<!-- class: sources -->
- Bank Sumut, detail tender Smart EDC. <https://www.banksumut.co.id/jasa_barang/pekerjaan-pengadaan-sewa-beli-mesin-smart-electronic-data-capture-smart-edc-pt-bank-sumut-perseroda/> Dibaca penuh oleh koordinator, 15.16 WIB.
- BTN, portal e2eproc. <https://e2eprocreg.btn.co.id/> Dilihat koordinator di Chrome Arif, 15.13 WIB; dialihkan ke `/OA_HTML/AppsLocalLogin.jsp`.
- Noi English / Pikiran Rakyat Media Network, 6 Juli 2025, berita sitaan KPK dalam kasus EDC BRI. <https://noi.pikiran-rakyat.com/news/pr-4049475114/kpk-seizes-idr-53-billion-in-cash-idr-28-billion-in-deposits-in-massive-bri-edc-corruption-scandal> Dibaca penuh oleh koordinator.
- BRI, eProc Vendor (iProc Extranet). <https://eproc.bri.co.id/> Koordinator: diblokir WAF Incapsula. Peneliti: form login terbaca pada percobaan kedua.

### Bank BUMN

<!-- class: sources -->
- BRI, robots.txt eproc. <https://eproc.bri.co.id/robots.txt> Dibuka; HTTP 404.
- BRI, tdronline. <https://tdronline.bri.co.id/> Dibuka, isi kosong; judul dari cuplikan pencarian.
- BRI, situs utama. <https://www.bri.co.id/> Cuplikan pencarian ("Request Rejected").
- Tempo English, 25 Juli 2025, "The Procurement Rule That Opened the Door to Corruption". <https://en.tempo.co/read/2032287/the-procurement-rule-that-opened-the-door-to-corruption> HTTP 403; cuplikan pencarian.
- BrokerChooser, penyelidikan KPK di BRI dan Telkom. <https://brokerchooser.com/news/indonesias-anti-corruption-agency-opens-inquiry-into-banking-notification-scheme-at-bri-and-telkom--82b73667> HTTP 403; cuplikan pencarian.
- Bank Mandiri, eproc (tebakan). <https://eproc.bankmandiri.co.id/> Gagal koneksi.
- Bank Mandiri, lelang. <https://lelang.bankmandiri.co.id/> Dibuka, isi kosong; judul dari cuplikan pencarian.
- Bank Mandiri, Kebijakan Pengadaan Barang dan Jasa (English), PDF. <https://www.bankmandiri.co.id/documents/38268824/42739631/Kebijakan+Pengadaan+Barang+dan+Jasa+(english).pdf/063e2ffa-5931-226e-e965-2faed3dbe524> Cuplikan pencarian.
- Bank Mandiri, Overview Sustainable Procurement Policy, PDF. <https://www.bankmandiri.co.id/documents/20143/505464457/Overview_Sustainable+Procurement+Policy_Rev+SG_Rev.AJ_Rev.Syafiq_Rev.Nnd.pdf/49410a9f-2a68-9c5f-f540-e3fb6333d72a?t=1768377963227> PDF tidak terbaca; cuplikan pencarian.
- Bank Mandiri, Mandiri API. <https://www.bankmandiri.co.id/en/mandiri-api> Cuplikan pencarian.
- Bank Mandiri, Mandiri EDC. <https://bankmandiri.co.id/en/edc> Cuplikan pencarian.
- Bank Mandiri, Mandiri Group. <https://www.bankmandiri.co.id/en/mandiri-group> Cuplikan pencarian.
- BNI, eproc (tebakan). <https://eproc.bni.co.id/> Gagal koneksi.
- BNI, beranda. <https://www.bni.co.id/id-id/> Dibuka; tidak ada teks pengadaan.
- BTN, eproc (tebakan). <https://eproc.btn.co.id/> Gagal koneksi.
- BTN, beranda. <https://www.btn.co.id/> Dibuka; tidak ada teks pengadaan.
- BTN, b-gov. <https://b-gov.btn.co.id/> Cuplikan pencarian ("Request Rejected").
- BTN, emitra. <https://emitra.btn.co.id/> Cuplikan pencarian ("Request Rejected").
- BTN, balé merchant di Google Play. <https://play.google.com/store/apps/details?gl=US&hl=en_ZA&id=com.btn.btnmerchant> Cuplikan pencarian.
- BSI, eproc (tebakan). <https://eproc.bankbsi.co.id/> Gagal koneksi.
- BSI, span. <https://span.bankbsi.co.id/> Dibuka, isi kosong; judul dari cuplikan pencarian.
- BSI, BYOND Merchant di Google Play. <https://play.google.com/store/apps/details?hl=en&id=co.id.bankbsi.qrismerchant> Cuplikan pencarian.

### Bank swasta

<!-- class: sources -->
- BCA, robots.txt. <https://www.bca.co.id/robots.txt> Dibuka.
- BCA, eproc (tebakan). <https://eproc.bca.co.id/> Gagal koneksi.
- BCA, sitemap. <https://www.bca.co.id/sitemap.xml> Format XML tidak terbaca alat riset.
- BCA, Merchant BCA di Google Play. <https://play.google.com/store/apps/details?id=com.bca.msb> Cuplikan pencarian.
- BCA, info EDC BCA di Google Play. <https://play.google.com/store/apps/details?id=com.bca.info.edc> Cuplikan pencarian.
- CIMB Niaga, robots.txt. <https://www.cimbniaga.co.id/robots.txt> Dibuka.
- CIMB Group, Vendor Code of Conduct, PDF. <https://www.cimbbank.com.ph/content/dam/cimb/group/documents/sustainbility/vendor-code-of-conduct.pdf> Cuplikan pencarian.
- CIMB Niaga, OCTO Merchant di Google Play. <https://play.google.com/store/apps/details?hl=en&id=com.cimbedc> Cuplikan pencarian.
- Telkom University, makalah transaksi debit EDC studi kasus CIMB Niaga, PDF. <https://socj.telkomuniversity.ac.id/ojs/index.php/indojc/article/download/880/407> PDF tidak terbaca.
- Danamon, robots.txt. <https://www.danamon.co.id/robots.txt> Dibuka.
- Danamon, Laporan Tahunan 2024 Company Profile, PDF. <https://www.danamon.co.id/-/media/ALL-CONTENT-ABOUT-DANAMON/LAPORAN-KEUANGAN/LAPORAN-TAHUNAN/2024/en/5-Company-Profile-AR-Bank-Danamon-2024-ENG-25-Feb-Malam2web-Medium4.pdf> Cuplikan pencarian.
- Danamon, RIPLAY Layanan Merchant QR, PDF. <https://www.danamon.co.id/-/media/ALL-CONTENT-EBANKING/QRIS/QR-Merchant/18-06-2025/RIPLAY---Layanan-Merchant-QR-Danamon---Final_non-iOS-include-sameday---EN.pdf> Cuplikan pencarian.
- Danamon, TradeConnect. <https://tradeconnect.danamon.co.id/> Cuplikan pencarian.
- PermataBank, robots.txt. <https://www.permatabank.com/robots.txt> HTTP 403.
- PermataBank, bergabung menjadi merchant. <https://www.permatabank.com/id/digital-channel/permataqr/bergabung-menjadi-merchant> HTTP 403.
- PermataBank, Permata QR Merchant di Google Play. <https://play.google.com/store/apps/details?hl=en_GB&id=com.permatabank.qram> Cuplikan pencarian.
- Maybank Indonesia, robots.txt. <https://www.maybank.co.id/robots.txt> Dibuka.
- MyBiz Solutions, studi kasus eProcurement Maybank Group, PDF. <https://www.mybiz.net/_files/ugd/c29f77_aa494836ecc64a39bda6d27ee782e421.pdf> Cuplikan pencarian.
- Maybank Group, Sustainable Procurement Principles (salinan BankTrack). <https://www.banktrack.org/download/sustainable_procurement_principles> Cuplikan pencarian.
- Maybank, ESG Code of Conduct pemasok, PDF. <https://www.maybank2u.com.sg/iwov-resources/sg/pdf/esg-code-of-conduct.pdf> Cuplikan pencarian.
- Maybank Indonesia, pengumuman pemeliharaan sistem rekening joint, 17 April 2026. <https://www.maybank.co.id/en/NewsAndAnnouncement/NewsAndAnnouncements/2026/04/17/01/11/Informasi-Pemeliharaan-Sistem-Rekening-Joint> Cuplikan pencarian.
- OCBC Indonesia, robots.txt. <https://www.ocbc.id/robots.txt> Dibuka.
- OCBC Indonesia, Corporate Internet Banking. <https://business.ocbc.id/> Cuplikan pencarian.
- OCBC, Supplier Code of Conduct, PDF. <https://www.ocbc.com/iwov-resources/sg/ocbc/gbc/pdf/ocbc-supplier-code-of-conduct.pdf> Cuplikan pencarian.
- OCBC, Acting with integrity. <https://www.ocbc.com/group/sustainability/sustainability-framework/acting-with-integrity.page> Cuplikan pencarian.
- OCBC, OCBC Merchant di Google Play. <https://play.google.com/store/apps/details?id=id.ocbc.merchant> Cuplikan pencarian.
- PR Newswire, OCBC Tap Credit Card, 10 November 2025. <https://www.prnewswire.com/apac/news-releases/ocbc-launches-tap-credit-card-seamless-nfc-transactions-for-speed-and-convenience-302610100.html> Cuplikan pencarian.
- OCBC, rilis akuisisi HSBC International Wealth and Premier Banking Indonesia. <https://www.ocbc.com/group/media/release/2026/ocbc-acquires-hsbc-international-wealth-and-premier-banking-indonesia> Cuplikan pencarian.
- Panin Bank, robots.txt. <https://www.panin.co.id/robots.txt> HTTP 403.
- Panin Bank, kurs. <https://www.panin.co.id/id/kurs> HTTP 403.
- Bank Mega, robots.txt. <https://bankmega.com/robots.txt> Dibuka.
- Bank Mega, Corporate Governance. <https://bankmega.com/en/about-us/corporate-governance/> Dibuka.
- Bank Mega, Developer API. <https://developer.bankmega.com/> Cuplikan pencarian.
- Scribd, Surat Permohonan Penarikan EDC. <https://www.scribd.com/document/343502745/Surat-Permohonan-Penarikan> Cuplikan pencarian.
- SMBC Indonesia, iProc (iprocsmbci). <https://iprocsmbci.pengadaan.com/> Dibuka.
- SMBC Indonesia, iProc (smbci). <https://smbci.pengadaan.com/> Dibuka.
- SMBC Indonesia, robots.txt iProc. <https://smbci.pengadaan.com/robots.txt> HTTP 404.
- pengadaan.com. <https://pengadaan.com/> Dialihkan ke login SSO.
- SMBC Indonesia, Tentang Kami. <https://www.smbci.com/en/tentang-kami> Cuplikan pencarian.
- UOB Indonesia, robots.txt. <https://www.uob.co.id/robots.txt> HTTP 404.
- UOB Malaysia, UOB Procure-to-Pay. <https://uob.com.my/business/transact/cards/uob-procure-to-pay.page> Cuplikan pencarian.
- Bank Sinarmas, robots.txt. <https://www.banksinarmas.com/robots.txt> Gagal koneksi.
- Bank Sinarmas, promosi kartu kredit. <https://www.banksinarmas.com/id/promosi/kartukredit> Gagal koneksi.

### BPD

<!-- class: sources -->
- Bank Sumut, Pengadaan Barang & Jasa. <https://www.banksumut.co.id/pengadaan-barang-jasa/> Dibuka.
- Bank Sumut, arsip jasa barang. <https://www.banksumut.co.id/archive-jasa-barang/> Tautan dari halaman detail tender.
- Bank Sumut, Procurement of Goods and Services (English). <https://www.banksumut.co.id/en/procurement-of-goods-and-services/> Dibuka.
- Bank Sumut, feed RSS. <https://www.banksumut.co.id/feed/> Menjawab `application/rss+xml`; isi belum terbaca.
- Bank Sumut, REST WordPress jasa_barang. <https://www.banksumut.co.id/wp-json/wp/v2/jasa_barang?per_page=5> Menjawab `application/json`; isi belum terbaca.
- Bank Sumut, menu lelang. <https://www.banksumut.co.id/lelang/> Belum dibuka.
- Bank Jatim, Lelang Pengadaan. <https://www.bankjatim.co.id/id/informasi/lelang-pengadaan> Dibuka.
- Bank Jatim, Pengumuman (bukan tender). <https://www.bankjatim.co.id/id/informasi/pengumuman> Dibuka.
- Bank Jatim, robots.txt. <https://www.bankjatim.co.id/robots.txt> Dibuka.
- Bank Jatim, pengumuman Mobile App Security 2025, PDF. <https://www.bankjatim.co.id/files/pengumuman/2025/september/pengumuman_website_pengadaan_english.pdf> Cuplikan pencarian.
- Bank Jatim, ATM Machine Rental 2022, PDF. <https://www.bankjatim.id/files/pengumuman/2022/juni/pengumuman_website_pengadaan_jasa_sewa_mesin_atm_2022_english.pdf> Cuplikan pencarian.
- Bank Jatim, Sewa Mesin CRM 2022, PDF. <https://www.bankjatim.id/files/pengumuman/2022/juli/pengumuman_website_pengadaan_jasa_sewa_mesin_crm_2022_english.pdf> Cuplikan pencarian.
- bank bjb, beranda. <https://www.bankbjb.co.id/> Dibuka; hanya judul terbaca.
- bank bjb, eproc (tebakan). <https://eproc.bankbjb.co.id/> Halaman tantangan "Please wait a while...".
- VOI, KPK mendalami pengumpulan dana non-budgeter bjb. <https://voi.id/en/news/597746> Cuplikan pencarian.
- VOI, 9 Agustus 2026, domain baru Bank Jakarta. <https://voi.id/en/economy/588894> Dibuka.
- Bank Jakarta, beranda. <https://www.bankjakarta.co.id/> HTTP 403.
- Bank DKI, beranda. <https://www.bankdki.co.id/> HTTP 403.
- Scribd, Vendor Management Bank DKI. <https://www.scribd.com/document/775698019/Vendor-Management-Bank-DKI> Isi dari cuplikan pencarian.
- Bank Jateng, beranda. <https://www.bankjateng.co.id/> Dibuka; isi dimuat JavaScript.
- Bank Jateng, lelang agunan. <https://lelang.bankjateng.co.id/> Dibuka.
- Bank Nagari, beranda. <https://www.banknagari.co.id/> Dibuka.
- Nagari Portal Lelang (andro.io). <https://bn-webview.andro.io/> Cuplikan pencarian.
- BPD Bali, beranda. <https://www.bpdbali.co.id/> Dibuka.
- Bankaltimtara, beranda. <https://www.bankaltimtara.co.id/> Dibuka.
- Bank Kalbar, beranda. <https://www.bankkalbar.co.id/> Dibuka; tidak ada teks menu yang berguna.
- Bank Sultra, e-tender. <https://e-tender.banksultra.co.id/> Cuplikan pencarian.
- Bank Sulteng, eproc. <https://eproc.banksulteng.co.id/> Cuplikan pencarian.

### Portal agregat, media, dan acuan

<!-- class: sources -->
- TenderKita. <https://tenderkita.com/> Dibuka.
- Tender Indonesia, beranda. <https://tender-indonesia.com/> Dibuka; isi tidak terbaca.
- Tender Indonesia, daftar proyek. <https://tender-indonesia.com/tender_home/tender.php> Cuplikan pencarian.
- Blog tentang Tender Indonesia. <https://abouttenderindonesia.blogspot.com/> Cuplikan pencarian.
- pengadaan.info. <https://pengadaan.info/> Cuplikan pencarian.
- IndoTender. <http://indotender.com/> Cuplikan pencarian.
- TenderTiger Indonesia. <https://indonesia.tendertiger.com/> Cuplikan pencarian.
- tenderinfo.org Indonesia. <http://indonesia.tenderinfo.org/> Cuplikan pencarian.
- IndonesiaTenders. <https://www.indonesiatenders.com/> Cuplikan pencarian.
- pyproc di GitHub. <https://github.com/wakataw/pyproc> Cuplikan pencarian.
- Nusantara Procurement Data. <https://nusantara-platform.site/> Cuplikan pencarian.
- PaDi UMKM Seller di App Store. <https://apps.apple.com/it/app/padi-umkm-seller/id1588822356> Cuplikan pencarian.
- Bank Indonesia, contoh pengumuman pengadaan TA 2026. <https://www.bi.go.id/id/layanan/lelang-jasa-barang/announcement/Pages/Pengadaan-Infrastruktur-Software-Microsoft-Azure-Local-untuk-Infra-Dev-Test-Bank-Indonesia-TA-2026.aspx> Cuplikan pencarian.
- Biro iklan, Iklan Lelang Bisnis Indonesia. <https://pusatpemasanganiklan.com/koran/1-bisnis-indonesia> Cuplikan pencarian.

### Vendor dan pasar EDC

<!-- class: sources -->
- Telkomsel, IoT Managed EDC. <https://www.telkomsel.com/enterprise/product-list-iot/iot-managed-edc> Cuplikan pencarian.
- PitchBook, PT Prima Vista Solusi. <https://pitchbook.com/profiles/company/154346-14> Cuplikan pencarian.
- linktr.ee, PT Prima Vista Solusi. <https://linktr.ee/primavistasolusi> Cuplikan pencarian.
- PT Prima Vista Solusi, situs. <https://primavista-solusi.com/> Dibuka; tidak ada teks terbaca.
- eprints UPJ, abstrak kerja praktik mahasiswa tentang PVS-WIDE, PDF. <http://eprints.upj.ac.id/id/eprint/6216/3/abstract.pdf> Cuplikan pencarian.
- Preqin, PT Mitra Transaksi Indonesia. <https://www.preqin.com/data/profile/asset/pt-mitra-transaksi-indonesia/449977> Cuplikan pencarian.
- Ingenico APAC, blog infrastruktur pembayaran. <https://ingenico.com/apac/newsroom/blogs/beyond-payments-why-modern-infrastructure-becoming-strategic-across-apac> Cuplikan pencarian.
