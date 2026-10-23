# Riset Tender Bot — Bagian 1: Bank BUMN

Status: SELESAI (batas waktu ±45 menit; data tidak lengkap, keterbatasan dicatat di bagian 4). Diperbarui dengan temuan koordinator untuk portal BTN.
Tanggal riset/akses: 2026-10-23
Cakupan: BRI, Bank Mandiri, BNI, BTN, BSI, plus anak usaha relevan EDC/acquiring.
Metode: web_search + web_fetch saja (tanpa browser/login/registrasi/isi formulir).

Legenda status bukti:
- [PORTAL] = terverifikasi langsung dari halaman/portal milik bank (di-fetch sendiri)
- [BERITA] = dari berita/sumber pihak ketiga yang di-fetch
- [SNIPPET] = hanya terlihat di cuplikan hasil pencarian; halaman aslinya tidak berhasil di-fetch
- [TIDAK DITEMUKAN] = tidak ditemukan dalam batas riset ini (bukan berarti pasti tidak ada)
- [INFERENSI] = kesimpulan peneliti dari bukti di atas, bukan fakta yang tertulis di sumber
- [KOORDINATOR] = diverifikasi langsung oleh koordinator di Chrome milik Arif, 2026-10-23 15:13 WIB; portalnya tidak dibuka ulang oleh peneliti

## 1. Tabel ringkas

| Bank | URL portal | Akses publik? | Format pengumuman | Catatan teknis bot | Tender EDC ditemukan? |
|---|---|---|---|---|---|
| BRI | [eproc.bri.co.id](https://eproc.bri.co.id/) (iProc Extranet); akun/registrasi di [tdronline.bri.co.id](https://tdronline.bri.co.id/) [PORTAL] | Tidak. Halaman depan langsung form login; akun dari tdronline [PORTAL] | Tidak ada daftar/pengumuman publik terlihat; RSS/API tidak ditemukan | Form login terbaca lewat HTTP biasa; robots.txt 404; kemungkinan CAPTCHA (tombol "Refresh"); tdronline kosong saat di-fetch (JS); www.bri.co.id kena WAF "Request Rejected" | Ya, lewat berita: kasus KPK pengadaan mesin EDC 2020–2024, nilai ±Rp2,1 T [BERITA] |
| Bank Mandiri | Tidak ditemukan. `eproc.bankmandiri.co.id` gagal koneksi; [lelang.bankmandiri.co.id](https://lelang.bankmandiri.co.id/) kemungkinan lelang agunan [INFERENSI] | Tidak diketahui | Kebijakan pengadaan hanya berupa PDF | Dokumen PDF perlu parser; subdomain lelang kosong saat di-fetch (JS) | Tidak ditemukan |
| BNI | Tidak ditemukan. `eproc.bni.co.id` gagal koneksi | Tidak diketahui | Tidak ditemukan | Kueri "BNI" tercemar Business Network International | Tidak ditemukan |
| BTN | [e2eprocreg.btn.co.id](https://e2eprocreg.btn.co.id/) → login Oracle E-Business Suite "Aplikasi Integrated End to End Procurement" [KOORDINATOR] | Tidak. Wajib login sebagai vendor terdaftar [KOORDINATOR] | Halaman login hanya berisi form User Name/Password; tidak ada daftar tender publik; RSS/API tidak ditemukan | Oracle EBS (path `/OA_HTML/AppsLocalLogin.jsp`); run sebelumnya hang dengan browser otomatis, jadi wajib timeout keras; robots.txt tidak dicek (portal tidak boleh dibuka ulang); subdomain lain (b-gov, emitra) kena WAF "Request Rejected" | Tidak ditemukan |
| BSI | Tidak ditemukan. `eproc.bankbsi.co.id` gagal koneksi; [span.bankbsi.co.id](https://span.bankbsi.co.id/) fungsinya belum jelas | Tidak diketahui | Tidak ditemukan | Kueri "BSI" tercemar BSI Group; span kosong saat di-fetch (JS) | Tidak ditemukan |
| Anak usaha (Bank Mandiri Taspen, BRILink) | Tidak ditemukan | – | – | – | Tidak ditemukan |

Implikasi desain bot [INFERENSI dari temuan di atas]:
1. Di BRI dan BTN (dua portal yang terverifikasi), daftar tender ada di balik login vendor. Bot yang hanya membaca halaman publik tidak akan melihat tender EDC. Jalur realistis: daftar resmi sebagai vendor di tiap bank, lalu bot membaca email undangan/notifikasi portal. Membaca portal dari dalam sesi vendor perlu dicek dulu terhadap syarat penggunaan portal.
2. Tempo melaporkan perusahaan lain "were not invited" pada tender EDC BRI, jadi tender EDC bisa berbentuk undangan dan tidak pernah diumumkan terbuka. Sinyal publik yang tetap bisa dipantau: berita (pemenang, KPK), keterbukaan informasi emiten vendor, laporan tahunan bank.
3. Teknis: setiap request pakai timeout keras + retry (fetch pertama eproc BRI kosong, fetch kedua berhasil); deteksi halaman WAF "Request Rejected"; renderer JavaScript hanya dengan batas waktu (pelajaran dari portal BTN).
4. Kueri berita/alert: pakai nama lengkap bank ("Bank Negara Indonesia", "Bank Syariah Indonesia") + "mesin EDC", karena akronim BNI dan BSI bertabrakan dengan organisasi lain.

## 2. Rincian per bank

### 2.1 BRI — PT Bank Rakyat Indonesia (Persero) Tbk

1. Portal e-procurement
   - [eProc Vendor BRI — iProc Extranet Platform](https://eproc.bri.co.id/) [PORTAL]. Domain `bri.co.id` milik BRI. Halaman berjudul "Log in to iProc Extranet Platform — Electronic goods and services procurement modernization system", menampilkan logo Danantara, eproc, dan BRI. Helpdesk: HelpdeskIFS@corp.bri.co.id.
   - Registrasi/akun vendor ada di portal terpisah [tdronline.bri.co.id](https://tdronline.bri.co.id/): halaman login eProc menulis "Use e-mail and password from tdronline.bri.co.id" dan tombol "Register as Partner" mengarah ke sana [PORTAL]. Judul halaman tdronline di hasil pencarian: "Brifamp", kontak berawalan "manajemenvendor@bri.co…" (terpotong di cuplikan) [SNIPPET].
2. Akses publik
   - Halaman depan eProc langsung berupa form login (EMAIL, PASSWORD). Tidak terlihat daftar tender/pengumuman publik [PORTAL].
   - Syarat registrasi vendor tidak terbaca: tdronline.bri.co.id mengembalikan konten kosong saat di-fetch (kemungkinan aplikasi yang dirender JavaScript) [TIDAK DITEMUKAN].
3. Format pengumuman & RSS/API
   - Tidak ditemukan halaman pengumuman tender publik, RSS, atau API publik [TIDAK DITEMUKAN].
   - Situs utama [www.bri.co.id](https://www.bri.co.id/) tampil di hasil pencarian dengan judul "Request Rejected — Please consult with your administrator", tanda ada WAF yang menolak akses otomatis [SNIPPET]. Tidak di-fetch langsung.
4. Catatan teknis bot
   - [robots.txt eproc](https://eproc.bri.co.id/robots.txt) → HTTP 404 (tidak ada robots.txt) [PORTAL].
   - Form login memuat teks "Refresh" di antara kolom password dan tombol login; kemungkinan tombol muat-ulang CAPTCHA [INFERENSI]. Halaman menyarankan "minimum Chrome version 77 or Firefox version 70 or Safari version 12".
   - Fetch pertama (mode truncated) mengembalikan konten kosong, fetch kedua (mode full) berhasil menampilkan form login. Bot perlu retry [PORTAL].
   - ToS/larangan scraping: tidak ditemukan di halaman yang terbaca [TIDAK DITEMUKAN].
5. Tender EDC
   - Tender asli tidak publik. Bukti dari berita: kasus dugaan korupsi pengadaan mesin EDC BRI periode 2020–2024 yang disidik KPK. Nilai proyek pengadaan EDC sekitar Rp2,1 triliun; dugaan kerugian negara sekitar Rp700 miliar (±30%); KPK menyita Rp5,3 miliar tunai dan deposito Rp28 miliar; 13 orang dimintakan cegah ke luar negeri; penggeledahan di 7 lokasi termasuk 2 kantor vendor ([Noi English / Pikiran Rakyat, 6 Jul 2025](https://noi.pikiran-rakyat.com/news/pr-4049475114/kpk-seizes-idr-53-billion-in-cash-idr-28-billion-in-deposits-in-massive-bri-edc-corruption-scandal)) [BERITA].
   - Menurut Tempo, penyidik KPK menduga ada kolusi Wakil Dirut Catur Budi Harto dan Direktur Digital, TI & Operasi Indra Utoyo "to ensure that tenders were won by Pasifik Cipta Solusi and Bringin Inti Teknologi—two subsidiaries of BRI". Tersangka: keduanya, Dedi Sunardi (pejabat senior pengadaan BRI), Elvizar (eks pimpinan PT Pasifik Cipta Solusi), dan Rudy S. Kartadidjaja (CEO PT Bringin Inti Teknologi). Tempo juga menulis penyidik menduga spesifikasi produk disetel agar hanya produk vendor tertentu yang menang "while other companies with similar technologies were not invited to participate" ([Tempo English, 25 Jul 2025](https://en.tempo.co/read/2032287/the-procurement-rule-that-opened-the-door-to-corruption)) [SNIPPET — fetch ditolak HTTP 403]. Cuplikan [BrokerChooser](https://brokerchooser.com/news/indonesias-anti-corruption-agency-opens-inquiry-into-banking-notification-scheme-at-bri-and-telkom--82b73667) menyebut Catur Budi Harto, Indra Utoyo (kini CEO Allo Bank), dan Dedi Sunardi (SEVP Manajemen Aktiva dan Pengadaan BRI) sebagai tersangka [SNIPPET — fetch ditolak HTTP 403].
   - Sebutan "two subsidiaries of BRI" untuk kedua vendor berasal dari Tempo dan tidak diverifikasi silang [TIDAK DITEMUKAN sumber kedua].
   - Nomor tender, tanggal tender, skema (beli vs sewa/managed service), dan status hukum terbaru (sidang/vonis) tidak ditemukan [TIDAK DITEMUKAN].

### 2.2 Bank Mandiri — PT Bank Mandiri (Persero) Tbk (+ Bank Mandiri Taspen)

1. Portal e-procurement
   - Portal e-procurement/vendor resmi Bank Mandiri TIDAK DITEMUKAN. Pencarian dengan kata kunci e-procurement, registrasi rekanan, dan vendor portal hanya mengembalikan dokumen kebijakan pengadaan di domain `bankmandiri.co.id` [TIDAK DITEMUKAN].
   - Subdomain tebakan `eproc.bankmandiri.co.id` gagal koneksi saat di-fetch [PORTAL]. Subdomain `vendor.` dan `procurement.` hanya muncul sebagai gema kueri di hasil pencarian tanpa isi; tidak boleh dianggap ada.
   - Ditemukan [lelang.bankmandiri.co.id](https://lelang.bankmandiri.co.id/) (judul "Beranda") di hasil pencarian [SNIPPET]; saat di-fetch kontennya kosong (kemungkinan dirender JavaScript). Istilah "lelang" di perbankan umumnya berarti lelang aset/agunan, bukan pengadaan vendor; perlu dicek manual [INFERENSI].
   - Dokumen kebijakan publik: [Kebijakan Pengadaan Barang dan Jasa (English)](https://www.bankmandiri.co.id/documents/38268824/42739631/Kebijakan+Pengadaan+Barang+dan+Jasa+(english).pdf/063e2ffa-5931-226e-e965-2faed3dbe524) — cuplikan: SPO Pengadaan diperbarui dan disetujui 1 Maret 2017; ada pemisahan fungsi unit seleksi calon mitra/vendor, unit proses pengadaan, unit penyusun HPS, dan unit kepatuhan [SNIPPET]. [Overview Sustainable Procurement Policy](https://www.bankmandiri.co.id/documents/20143/505464457/Overview_Sustainable+Procurement+Policy_Rev+SG_Rev.AJ_Rev.Syafiq_Rev.Nnd.pdf/49410a9f-2a68-9c5f-f540-e3fb6333d72a?t=1768377963227) — cuplikan: SPO dan PTO Pengadaan berlaku untuk kantor pusat, wilayah, area, cabang, dan cabang luar negeri [SNIPPET; fetch gagal karena tipe konten PDF tidak didukung].
2. Akses publik: tidak dapat ditentukan karena portal tidak ditemukan [TIDAK DITEMUKAN].
3. Format pengumuman & RSS/API: tidak ditemukan. [Mandiri API](https://www.bankmandiri.co.id/en/mandiri-api) (developer.bankmandiri.co.id) adalah API layanan perbankan, BUKAN API pengadaan [SNIPPET].
4. Catatan teknis bot: belum ada URL target. Dokumen pengadaan Mandiri berbentuk PDF, perlu parser PDF [PORTAL — fetch PDF gagal].
5. Tender EDC: tidak ditemukan tender, pemenang, atau berita kontrak EDC Bank Mandiri [TIDAK DITEMUKAN]. Yang ada hanya halaman produk [Mandiri EDC](https://bankmandiri.co.id/en/edc) [SNIPPET].
6. Bank Mandiri Taspen (MANTAP): bank milik Bank Mandiri dan PT Taspen, berkantor pusat di Jl. Melati No. 65 Denpasar, Bali ([Mandiri Group](https://www.bankmandiri.co.id/en/mandiri-group)) [SNIPPET]. Portal pengadaan sendiri tidak ditemukan [TIDAK DITEMUKAN].

### 2.3 BNI — PT Bank Negara Indonesia (Persero) Tbk

1. Portal e-procurement
   - Portal e-procurement/vendor resmi BNI TIDAK DITEMUKAN [TIDAK DITEMUKAN]. Tiga kueri (e-procurement, pengumuman pengadaan, laporan tahunan + e-procurement) didominasi hasil tak relevan, termasuk Business Network International (bni.com).
   - Subdomain tebakan `eproc.bni.co.id` gagal koneksi saat di-fetch [PORTAL].
   - Fetch selektif [beranda bni.co.id](https://www.bni.co.id/id-id/) dengan kata kunci pengadaan/procurement/vendor/rekanan/lelang tidak mengembalikan teks yang cocok [PORTAL]. Kemungkinan menu dirender JavaScript atau tautan pengadaan tidak ada di beranda [INFERENSI].
2. Akses publik: tidak dapat ditentukan [TIDAK DITEMUKAN].
3. Format pengumuman & RSS/API: tidak ditemukan [TIDAK DITEMUKAN].
4. Catatan teknis bot: akronim "BNI" bertabrakan dengan Business Network International; kueri berita wajib memakai "Bank Negara Indonesia" atau "BBNI".
5. Tender EDC: tidak ditemukan [TIDAK DITEMUKAN].

### 2.4 BTN — PT Bank Tabungan Negara (Persero) Tbk

1. Portal e-procurement
   - [e2eprocreg.btn.co.id](https://e2eprocreg.btn.co.id/) [KOORDINATOR]. Domain `btn.co.id` milik BTN. Alamat ini me-redirect ke `https://e2eprocreg.btn.co.id/OA_HTML/AppsLocalLogin.jsp`, yaitu halaman login Oracle E-Business Suite berjudul "Aplikasi Integrated End to End Procurement".
   - Helpdesk yang tertera: WhatsApp +62 822 5888 2676, email helpdesk.e2eproc@btn.co.id [KOORDINATOR].
   - Portal ini TIDAK muncul dalam tiga kueri web_search peneliti, dan subdomain tebakan `eproc.btn.co.id` gagal koneksi [PORTAL]. Run sebelumnya menggantung saat membuka portal BTN dengan browser otomatis.
2. Akses publik
   - Tidak. Halaman hanya berisi form User Name/Password serta tautan Forgot Username/Password; tidak ada daftar tender publik. Daftar tender BTN wajib login sebagai vendor terdaftar [KOORDINATOR].
   - Syarat registrasi vendor tidak terlihat di halaman login [KOORDINATOR] dan tidak ditemukan di sumber lain [TIDAK DITEMUKAN]. Nama host "e2eprocreg" mengisyaratkan fungsi registrasi [INFERENSI].
3. Format pengumuman & RSS/API: tidak ada pengumuman publik di halaman login [KOORDINATOR]; RSS/API tidak ditemukan [TIDAK DITEMUKAN].
4. Catatan teknis bot
   - Platform: Oracle E-Business Suite (path `/OA_HTML/AppsLocalLogin.jsp`) [KOORDINATOR].
   - robots.txt dan ToS portal tidak dicek, karena koordinator menginstruksikan portal tidak dibuka ulang [TIDAK DITEMUKAN].
   - Fetch selektif [beranda btn.co.id](https://www.btn.co.id/) dengan kata kunci pengadaan/procurement/vendor/rekanan/eproc tidak mengembalikan teks yang cocok [PORTAL].
   - Subdomain [b-gov.btn.co.id](https://b-gov.btn.co.id/) dan [emitra.btn.co.id](https://emitra.btn.co.id/) tampil di hasil pencarian berjudul "Request Rejected — Please consult with your administrator" [SNIPPET]. Fungsi keduanya tidak terverifikasi; dicatat sebagai tanda ada WAF yang menolak akses otomatis.
   - Jangan arahkan browser otomatis ke portal BTN tanpa timeout keras; pakai HTTP request dengan batas waktu (mis. 15–30 detik) dan catat kegagalan sebagai "tidak tersedia" [INFERENSI].
5. Tender EDC
   - Tidak ditemukan pengumuman, pemenang, atau berita kontrak/tender EDC BTN setelah 5 kueri tambahan (mesin EDC BTN; e2eproc BTN; tender/sewa EDC BTN 2024–2026; acquiring/QRIS BTN; pengumuman pengadaan btn.co.id) [TIDAK DITEMUKAN].
   - Produk acquiring BTN yang terlihat publik: aplikasi [balé merchant](https://play.google.com/store/apps/details?gl=US&hl=en_ZA&id=com.btn.btnmerchant) untuk merchant BTN QRIS (daftar merchant mandiri, info transaksi real time, notifikasi, pantau tiap outlet, buat QRIS BTN) [SNIPPET]. Cuplikannya tidak menyebut EDC.

### 2.5 BSI — PT Bank Syariah Indonesia Tbk

1. Portal e-procurement
   - Portal e-procurement/vendor resmi BSI TIDAK DITEMUKAN [TIDAK DITEMUKAN].
   - Subdomain tebakan `eproc.bankbsi.co.id` gagal koneksi saat di-fetch [PORTAL].
   - Ditemukan [span.bankbsi.co.id](https://span.bankbsi.co.id/) berjudul "Bank Syariah Indonesia BSI Portal — Welcome to BSI Portal - SPAN" [SNIPPET]; saat di-fetch kontennya kosong (kemungkinan JavaScript). Fungsinya tidak terverifikasi. Di keuangan negara "SPAN" lazim berarti Sistem Perbendaharaan dan Anggaran Negara (Kemenkeu), jadi kemungkinan ini layanan perbendaharaan pemerintah, bukan pengadaan [INFERENSI — perlu dicek manual].
2. Akses publik: tidak dapat ditentukan [TIDAK DITEMUKAN].
3. Format pengumuman & RSS/API: tidak ditemukan [TIDAK DITEMUKAN].
4. Catatan teknis bot: akronim "BSI" bertabrakan dengan BSI Group (bsi-lifesciences.com) yang juga memakai istilah "Electronic Data Capture (EDC)" untuk uji klinis. Kueri berita wajib memakai "Bank Syariah Indonesia" atau "BRIS" + "mesin EDC".
5. Tender EDC: tidak ditemukan [TIDAK DITEMUKAN]. Produk acquiring yang terlihat publik: aplikasi [BYOND Merchant by BSI](https://play.google.com/store/apps/details?hl=en&id=co.id.bankbsi.qrismerchant) untuk QRIS (stiker QRIS, QRIS Nominal) [SNIPPET].

### 2.6 Anak usaha & catatan lintas-bank

- BRILink: tidak ditemukan sebagai entitas dengan portal pengadaan sendiri. BRILink adalah program agen BRI, jadi pengadaan EDC-nya diperkirakan lewat BRI [INFERENSI].
- Bank Mandiri Taspen: lihat 2.2 butir 6.
- Konteks pasar (bukan bank): Telkomsel menjual layanan [IoT Managed EDC](https://www.telkomsel.com/enterprise/product-list-iot/iot-managed-edc) untuk korporat — pengelolaan dan pemeliharaan mesin EDC, konektivitas, layanan terminal, integrasi, dan pemantauan dengan model biaya bulanan [SNIPPET]. Ini pesaing atau mitra potensial di segmen managed service EDC.
- Di luar cakupan (bukan bank BUMN), sebagai acuan skema data bot: Bank Indonesia mengumumkan pengadaan secara publik di bi.go.id dengan field terstruktur (Nomor Pengadaan, Nama Pengadaan, Tanggal Pengumuman, Satuan Kerja, Cara Pengadaan, Metode Evaluasi, Pagu, Status, Closing Date, Rekanan Pemenang, Lampiran). Contoh: [Pengadaan Infrastruktur Software Microsoft Azure Local … TA 2026](https://www.bi.go.id/id/layanan/lelang-jasa-barang/announcement/Pages/Pengadaan-Infrastruktur-Software-Microsoft-Azure-Local-untuk-Infra-Dev-Test-Bank-Indonesia-TA-2026.aspx), diumumkan 2/19/2026, status "Open for RFI", closing 2/26/2026 [SNIPPET].

## 3. Daftar tender/berita EDC

| Bank | Judul/peristiwa | Nomor | Tanggal | Status | Sumber |
|---|---|---|---|---|---|
| BRI | Pengadaan mesin EDC BRI periode 2020–2024, nilai ±Rp2,1 T, dugaan kerugian ±Rp700 M | tidak ditemukan | berita 6 Jul 2025 | Penyidikan KPK; sita Rp5,3 M tunai + deposito Rp28 M | [Noi English / Pikiran Rakyat](https://noi.pikiran-rakyat.com/news/pr-4049475114/kpk-seizes-idr-53-billion-in-cash-idr-28-billion-in-deposits-in-massive-bri-edc-corruption-scandal) [BERITA] |
| BRI | Tender EDC BRI dimenangkan PT Pasifik Cipta Solusi dan PT Bringin Inti Teknologi; 5 tersangka (Catur Budi Harto, Indra Utoyo, Dedi Sunardi, Elvizar, Rudy S. Kartadidjaja) | tidak ditemukan | berita 25 Jul 2025 | Tersangka ditetapkan; sidang/vonis tidak ditemukan | [Tempo English](https://en.tempo.co/read/2032287/the-procurement-rule-that-opened-the-door-to-corruption) [SNIPPET] |
| Mandiri, BNI, BTN, BSI | — | — | — | Tidak ditemukan (BTN: termasuk 5 kueri tambahan setelah portal diverifikasi koordinator) | — |

## 4. Keterbatasan

- Umum: mesin pencari alat riset ini hampir tidak menampilkan media nasional Indonesia (Kompas, Detik, CNBC Indonesia, Bisnis, Kontan) untuk kueri ini. "Tidak ditemukan" untuk Mandiri, BNI, BTN, BSI berarti riset terbatas, bukan bukti tidak ada.
- Umum: subdomain `eproc.*` untuk Mandiri, BNI, BTN, BSI adalah tebakan pola dan semuanya gagal koneksi. Karena eproc.bri.co.id berhasil dari jaringan yang sama, ini bukan blokir jaringan total; penyebab per host (tidak ada, geo-block, timeout) tidak bisa dibedakan.
- Umum: tanpa browser (sesuai aturan), halaman yang dirender JavaScript terbaca kosong (tdronline BRI, lelang Mandiri, span BSI). Tanpa login, isi portal vendor tidak bisa dilihat.
- Umum: nomor tender, tanggal tender, dan nilai kontrak per tender tidak ditemukan untuk semua bank.
- BRI: syarat registrasi vendor tidak terbaca; artikel Tempo dan BrokerChooser HTTP 403, hanya cuplikan pencarian yang dipakai; status hukum terbaru kasus EDC tidak ditemukan (berita terbaru yang terbaca: Juli 2025).
- Bank Mandiri: PDF kebijakan tidak bisa dibaca web_fetch; fungsi lelang.bankmandiri.co.id belum terverifikasi.
- BNI: hasil pencarian tercemar Business Network International.
- BTN: portal ditemukan dan diverifikasi oleh koordinator, bukan lewat web_search; robots.txt/ToS tidak dicek karena portal tidak boleh dibuka ulang; syarat registrasi tidak terlihat; tidak ada berita EDC BTN dalam 5 kueri tambahan. Ini juga menunjukkan nama portal tiap bank tidak mengikuti satu pola (BTN memakai `e2eprocreg.`, bukan `eproc.`), jadi tebakan subdomain tidak bisa diandalkan untuk Mandiri, BNI, dan BSI.
- BSI: fungsi span.bankbsi.co.id belum terverifikasi; hasil pencarian EDC tercemar BSI Group.
- Langkah lanjut yang disarankan: tanyakan langsung ke bagian pengadaan/manajemen vendor tiap bank alamat portal resminya, atau buka manual dengan browser biasa (bukan bot), untuk Mandiri, BNI, dan BSI. Untuk BTN, tanyakan syarat registrasi vendor ke helpdesk e2eproc (lihat 2.4).

## 5. Daftar URL sumber + tanggal akses

Semua diakses 2026-10-23.

BRI
- [eproc.bri.co.id](https://eproc.bri.co.id/) — [PORTAL] form login iProc (fetch ke-2 berhasil)
- [eproc.bri.co.id/robots.txt](https://eproc.bri.co.id/robots.txt) — [PORTAL] HTTP 404
- [tdronline.bri.co.id](https://tdronline.bri.co.id/) — fetch kosong; judul/kontak dari cuplikan pencarian
- [www.bri.co.id](https://www.bri.co.id/) — cuplikan pencarian ("Request Rejected")
- [Noi English / Pikiran Rakyat — KPK sita Rp33,3 M kasus EDC BRI](https://noi.pikiran-rakyat.com/news/pr-4049475114/kpk-seizes-idr-53-billion-in-cash-idr-28-billion-in-deposits-in-massive-bri-edc-corruption-scandal) — [BERITA] di-fetch
- [Tempo English — The Procurement Rule That Opened the Door to Corruption](https://en.tempo.co/read/2032287/the-procurement-rule-that-opened-the-door-to-corruption) — HTTP 403; cuplikan pencarian
- [BrokerChooser — KPK inquiry BRI & Telkom](https://brokerchooser.com/news/indonesias-anti-corruption-agency-opens-inquiry-into-banking-notification-scheme-at-bri-and-telkom--82b73667) — HTTP 403; cuplikan pencarian

Bank Mandiri
- [eproc.bankmandiri.co.id](https://eproc.bankmandiri.co.id/) — gagal koneksi
- [lelang.bankmandiri.co.id](https://lelang.bankmandiri.co.id/) — fetch kosong; judul dari cuplikan
- [Kebijakan Pengadaan Barang dan Jasa (English) PDF](https://www.bankmandiri.co.id/documents/38268824/42739631/Kebijakan+Pengadaan+Barang+dan+Jasa+(english).pdf/063e2ffa-5931-226e-e965-2faed3dbe524) — cuplikan pencarian
- [Overview Sustainable Procurement Policy PDF](https://www.bankmandiri.co.id/documents/20143/505464457/Overview_Sustainable+Procurement+Policy_Rev+SG_Rev.AJ_Rev.Syafiq_Rev.Nnd.pdf/49410a9f-2a68-9c5f-f540-e3fb6333d72a?t=1768377963227) — fetch gagal (PDF); cuplikan pencarian
- [Mandiri API](https://www.bankmandiri.co.id/en/mandiri-api) — cuplikan pencarian
- [Mandiri EDC](https://bankmandiri.co.id/en/edc) — cuplikan pencarian
- [Mandiri Group](https://www.bankmandiri.co.id/en/mandiri-group) — cuplikan pencarian

BNI
- [eproc.bni.co.id](https://eproc.bni.co.id/) — gagal koneksi
- [Beranda BNI](https://www.bni.co.id/id-id/) — fetch selektif, tak ada teks pengadaan

BTN
- [e2eprocreg.btn.co.id](https://e2eprocreg.btn.co.id/) → `/OA_HTML/AppsLocalLogin.jsp` — [KOORDINATOR] diverifikasi di Chrome Arif 2026-10-23 15:13 WIB; tidak dibuka peneliti
- [eproc.btn.co.id](https://eproc.btn.co.id/) — gagal koneksi
- [Beranda BTN](https://www.btn.co.id/) — fetch selektif, tak ada teks pengadaan
- [b-gov.btn.co.id](https://b-gov.btn.co.id/) — cuplikan pencarian ("Request Rejected")
- [emitra.btn.co.id](https://emitra.btn.co.id/) — cuplikan pencarian ("Request Rejected")
- [balé merchant (Google Play)](https://play.google.com/store/apps/details?gl=US&hl=en_ZA&id=com.btn.btnmerchant) — cuplikan pencarian

BSI
- [eproc.bankbsi.co.id](https://eproc.bankbsi.co.id/) — gagal koneksi
- [span.bankbsi.co.id](https://span.bankbsi.co.id/) — fetch kosong; judul dari cuplikan
- [BYOND Merchant by BSI (Google Play)](https://play.google.com/store/apps/details?hl=en&id=co.id.bankbsi.qrismerchant) — cuplikan pencarian

Lain-lain
- [Telkomsel IoT Managed EDC](https://www.telkomsel.com/enterprise/product-list-iot/iot-managed-edc) — cuplikan pencarian
- [Bank Indonesia — contoh pengumuman pengadaan TA 2026](https://www.bi.go.id/id/layanan/lelang-jasa-barang/announcement/Pages/Pengadaan-Infrastruktur-Software-Microsoft-Azure-Local-untuk-Infra-Dev-Test-Bank-Indonesia-TA-2026.aspx) — cuplikan pencarian
