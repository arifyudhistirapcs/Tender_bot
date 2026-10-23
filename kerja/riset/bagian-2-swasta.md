# Riset Tender Bot — Bagian 2: Bank Swasta Besar

Status: SELESAI (2026-10-23). 9 bank inti + 2 bank tambahan (UOB Indonesia, Bank Sinarmas, riset singkat)
Tanggal riset: 2026-10-23 (WIB)
Peneliti: Yang ngeriset (subagent), metode DeerFlow ringkas
Alat: web_search + web_fetch saja (tanpa browser/playwright, tanpa login, tanpa registrasi)

## Pertanyaan inti
Untuk tiap bank swasta besar: di mana portal e-procurement/vendor resminya, apakah daftar tender bisa dilihat publik, dalam format apa pengumuman tender dirilis, apa hambatan teknis untuk bot pemantau, dan adakah tender/berita EDC (managed service, sewa, pemeliharaan, Android EDC/smart POS, field service, merchant acquiring).

## Rencana (Planner)
1. Cari URL portal pengadaan/vendor resmi per bank (domain milik bank).
2. Fetch halaman portal: publik vs login, syarat registrasi.
3. Format pengumuman + RSS/API.
4. Catatan teknis bot: HTML statis vs JS, CAPTCHA, pagination, robots.txt/ToS.
5. Tender/berita EDC per bank.

Legenda status bukti:
- [PORTAL] = terverifikasi langsung dari portal/situs resmi bank
- [BERITA] = dari berita/sumber pihak ketiga
- [TIDAK DITEMUKAN] = dicari tapi tidak ketemu dalam batas riset (BUKAN bukti bahwa portal/tender tidak ada)
- "cuplikan pencarian" = fakta dibaca dari cuplikan hasil web_search; halamannya tidak dibuka langsung (biasanya karena PDF tak bisa dibaca alat fetch)

## Jawaban singkat
Dari 11 bank swasta yang diriset, tidak ada satu pun yang ketahuan memasang daftar tender terbuka untuk publik di internet. Hanya SMBC Indonesia (eks BTPN) yang portal e-procurement-nya teridentifikasi, yaitu iProc di domain pihak ketiga pengadaan.com, dan isinya hanya halaman login intranet. Tender EDC (managed service, sewa, pemeliharaan, Android EDC, field service, merchant acquiring) dari bank-bank ini tidak ditemukan, baik di portal maupun di berita. Untuk bank swasta, bot scraping portal kemungkinan besar tidak cukup; jalur yang realistis adalah registrasi vendor (dilakukan manual oleh Arif), undangan lewat email, dan pemantauan berita/rilis pers.

## Tabel ringkas

| Bank | URL portal | Akses publik? | Format | Catatan teknis bot | Tender EDC ditemukan? |
|---|---|---|---|---|---|
| BCA | Tidak ditemukan | Tidak diketahui | Tidak diketahui | robots.txt longgar, tidak ada path pengadaan; Sitecore | Tidak |
| CIMB Niaga | Tidak ditemukan (hanya Vendor Code of Conduct grup CIMB) | Tidak diketahui | Tidak diketahui | robots.txt melarang path internal AEM; fetch HTML berhasil | Tidak |
| Danamon | Tidak ditemukan | Tidak diketahui | Tidak diketahui | robots.txt "Allow: /" | Tidak |
| PermataBank | Tidak ditemukan | Tidak diketahui | Tidak diketahui | 403 ke alat fetch (robots.txt dan halaman biasa) | Tidak |
| Maybank Indonesia | Tidak ditemukan (grup punya eProcurement, studi kasus 2012) | Tidak diketahui | Tidak diketahui | robots.txt hanya melarang /sitecore | Tidak |
| OCBC Indonesia | Tidak ditemukan (hanya Supplier Code of Conduct grup OCBC) | Tidak diketahui | Tidak diketahui | robots.txt melarang SEMUA URL ber-query (`/*?`) | Tidak |
| Panin | Tidak ditemukan | Tidak diketahui | Tidak diketahui | 403 ke alat fetch di seluruh situs; Drupal | Tidak |
| Bank Mega | Tidak ditemukan | Tidak diketahui | Tidak diketahui | robots.txt hanya melarang /admin/; HTML biasa, tanpa render JS | Tidak |
| SMBC Indonesia | [iprocsmbci.pengadaan.com](https://iprocsmbci.pengadaan.com/) / [smbci.pengadaan.com](https://smbci.pengadaan.com/) (iProc, domain pihak ketiga) | TIDAK, hanya login intranet | Tidak terlihat | Semua di balik login; robots.txt 404 | Tidak |
| UOB Indonesia (singkat) | Tidak ditemukan | Tidak diketahui | Tidak diketahui | robots.txt 404 | Tidak dicari mendalam |
| Bank Sinarmas (singkat) | Tidak ditemukan | Tidak diketahui | Tidak diketahui | Situs tidak terjangkau alat fetch | Tidak dicari mendalam |

Tidak ada RSS atau API tender yang ditemukan di bank mana pun. CAPTCHA dan pagination tidak bisa dinilai karena tidak ada halaman daftar tender yang terbuka.

## Implikasi untuk desain Tender Bot (saran, bukan temuan)
- Dalam batas riset ini, tidak ada portal tender publik bank swasta yang bisa di-scrape. Bot sebaiknya tidak mengandalkan scraping untuk segmen ini. (Sebagai pembanding: portal "eProc Vendor BRI" di [eproc.bri.co.id](https://eproc.bri.co.id/) muncul di hasil pencarian; bank BUMN dibahas di bagian riset lain.)
- Sumber yang masih bisa dipantau otomatis: halaman berita/pengumuman bank yang terbuka (mis. NewsAndAnnouncement Maybank Indonesia, rilis grup OCBC/CIMB), rilis pers vendor EDC, dan media bisnis. Hormati robots.txt: di OCBC Indonesia, URL ber-parameter `?` dilarang.
- Permata dan Panin memblokir klien non-browser (403). Bot yang patuh sebaiknya tidak mengakali blokir ini.
- Dugaan (belum terverifikasi): tender bank swasta baru terlihat setelah perusahaan terdaftar sebagai vendor atau diundang. Registrasi itu langkah manual oleh Arif sendiri, bukan bot. Setelah itu bot bisa membantu memantau email undangan.

## Rincian per bank

### 1. BCA (PT Bank Central Asia Tbk)
- (1) Portal e-procurement: [TIDAK DITEMUKAN]. Empat kueri pencarian (ID/EN, termasuk kueri laporan tahunan/kebijakan pengadaan) tidak memunculkan portal vendor/tender di domain bca.co.id; kueri `site:bca.co.id` tidak mengembalikan hasil sama sekali. Subdomain tebakan `eproc.bca.co.id` tidak bisa dihubungi (gagal koneksi, diakses 2026-10-23), jadi tidak bisa dianggap ada.
- (2) Akses publik: tidak diketahui. Tidak ada halaman daftar tender publik yang ditemukan.
- (3) Format: tidak diketahui. Tidak ada RSS/API tender yang ditemukan.
- (4) Catatan teknis bot [PORTAL]: robots.txt www.bca.co.id hanya melarang /others/, /sitecore/, /id/others/, /en/campaign/, /search-result/, /risetanddevelopt/, /id/search-result/, beberapa halaman form/promo, plus menunjuk sitemap.xml. Tidak ada path pengadaan di robots.txt. Sitemap berformat XML tidak bisa dibaca alat fetch ini ([robots.txt](https://www.bca.co.id/robots.txt), diakses 2026-10-23). Jalur /sitecore/ menandakan situs dibangun di CMS Sitecore (inferensi dari path, belum dicek lebih jauh).
- (5) Tender/berita EDC: [TIDAK DITEMUKAN] dalam batas riset. Pencarian berita vendor EDC Android BCA hanya memunculkan aplikasi Merchant BCA/info EDC BCA di Google Play (bukan tender).
- Kesimpulan untuk bot: BCA kemungkinan besar mengadakan pengadaan secara tertutup (undangan ke vendor terdaftar). Ini DUGAAN yang belum terverifikasi; perlu dicek manual, misalnya bagian tata kelola/pengadaan di Laporan Tahunan BCA.

### 2. CIMB Niaga (PT Bank CIMB Niaga Tbk)
- (1) Portal e-procurement: [TIDAK DITEMUKAN]. Empat kueri (ID/EN, termasuk "vendor management", "eproc", "rekanan") tidak memunculkan portal vendor/tender di domain cimbniaga.co.id. Yang muncul hanya profil ZoomInfo seorang staf procurement CIMB Niaga (menandakan ada fungsi procurement internal, bukan portal publik).
- Terkait grup [PORTAL grup]: CIMB Group menerbitkan Vendor Code of Conduct yang berlaku untuk vendor di seluruh grup ([PDF via cimbbank.com.ph](https://www.cimbbank.com.ph/content/dam/cimb/group/documents/sustainbility/vendor-code-of-conduct.pdf), cuplikan pencarian 2026-10-23; isi PDF belum dibaca penuh). Ini dokumen etika vendor, bukan daftar tender.
- (2) Akses publik: tidak diketahui (portal tidak ditemukan).
- (3) Format: tidak diketahui; tidak ada RSS/API tender yang ditemukan.
- (4) Catatan teknis bot [PORTAL]: robots.txt www.cimbniaga.co.id melarang /cgi-bin/, /jcr:content/*, /_jcr_content/*, /apps-content/*, /screen/*, halaman error, /clientlib-site/, dan satu PDF internal; menunjuk dua sitemap ([robots.txt](https://www.cimbniaga.co.id/robots.txt), diakses 2026-10-23). Path jcr:content/clientlib menandakan situs dibangun di Adobe Experience Manager (inferensi dari path).
- (5) Tender EDC: [TIDAK DITEMUKAN]. Yang ditemukan hanya konteks bisnis: CIMB Niaga punya aplikasi "OCTO Merchant" untuk mitra merchant/EDC (package id `com.cimbedc`) di [Google Play](https://play.google.com/store/apps/details?hl=en&id=com.cimbedc) (cuplikan pencarian 2026-10-23), dan ada makalah Telkom University tentang proses bisnis transaksi debit EDC dengan studi kasus CIMB Niaga ([PDF](https://socj.telkomuniversity.ac.id/ojs/index.php/indojc/article/download/880/407); isi PDF tidak bisa dibaca alat fetch). Keduanya bukan tender.

### 3. Danamon (PT Bank Danamon Indonesia Tbk, grup MUFG)
- (1) Portal e-procurement: [TIDAK DITEMUKAN]. Tiga kueri (termasuk "eproc danamon", "pengadaan rekanan") hanya memunculkan dokumen laporan tahunan, FAQ mobile banking, dan TradeConnect (layanan trade finance nasabah, [tradeconnect.danamon.co.id](https://tradeconnect.danamon.co.id/)), bukan portal vendor.
- Profil [PORTAL]: per 31 Des 2024, 92,47% saham Danamon dimiliki MUFG; aset konsolidasi Rp242,33 triliun bersama Adira Finance ([AR 2024 Company Profile, PDF](https://www.danamon.co.id/-/media/ALL-CONTENT-ABOUT-DANAMON/LAPORAN-KEUANGAN/LAPORAN-TAHUNAN/2024/en/5-Company-Profile-AR-Bank-Danamon-2024-ENG-25-Feb-Malam2web-Medium4.pdf), cuplikan pencarian 2026-10-23).
- (2) Akses publik: tidak diketahui (portal tidak ditemukan).
- (3) Format: tidak diketahui; tidak ada RSS/API tender yang ditemukan.
- (4) Catatan teknis bot [PORTAL]: robots.txt www.danamon.co.id berisi "User-agent: * Allow: /" plus sitemap ([robots.txt](https://www.danamon.co.id/robots.txt), diakses 2026-10-23), jadi tidak ada larangan crawling di robots.txt. ToS situs belum dicek. Path /-/media/ menandakan CMS Sitecore (inferensi dari path).
- (5) Tender EDC: [TIDAK DITEMUKAN]. Konteks bisnis saja: Danamon punya layanan Merchant QR (aplikasi Danamon QR di Android, login Merchant ID 10 digit + PIN 6 digit via SMS) menurut [RIPLAY Layanan Merchant QR Danamon (PDF)](https://www.danamon.co.id/-/media/ALL-CONTENT-EBANKING/QRIS/QR-Merchant/18-06-2025/RIPLAY---Layanan-Merchant-QR-Danamon---Final_non-iOS-include-sameday---EN.pdf) (cuplikan pencarian 2026-10-23). Tidak ada berita pengadaan/vendor EDC Danamon yang ditemukan.

### 4. PermataBank (PT Bank Permata Tbk)
- (1) Portal e-procurement: [TIDAK DITEMUKAN]. Tiga kueri (ID/EN, termasuk "eproc", "vendor login") hanya memunculkan Permata eBusiness (internet banking korporat), Permata ME, dan Permata QR Merchant.
- (2) Akses publik: tidak diketahui (portal tidak ditemukan).
- (3) Format: tidak diketahui; tidak ada RSS/API tender yang ditemukan.
- (4) Catatan teknis bot [PORTAL]: situs www.permatabank.com menolak alat fetch otomatis dengan HTTP 403 Forbidden, baik untuk [robots.txt](https://www.permatabank.com/robots.txt) maupun halaman spesifik [bergabung-menjadi-merchant](https://www.permatabank.com/id/digital-channel/permataqr/bergabung-menjadi-merchant) (keduanya diakses 2026-10-23). Artinya ada proteksi bot/WAF di sisi server; isi robots.txt dan ToS tidak bisa dibaca dari sini. Untuk bot nanti: blokir ini sebaiknya dihormati (pantau manual, atau minta akses/izin resmi ke bank), bukan diakali.
- (5) Tender EDC: [TIDAK DITEMUKAN]. Konteks bisnis saja: PermataBank menjalankan layanan Permata QR Merchant ([Google Play](https://play.google.com/store/apps/details?hl=en_GB&id=com.permatabank.qram), cuplikan pencarian 2026-10-23). Tidak ada berita pengadaan/vendor EDC Permata yang ditemukan.

### 5. Maybank Indonesia (PT Bank Maybank Indonesia Tbk)
- (1) Portal e-procurement Indonesia: [TIDAK DITEMUKAN]. Tiga kueri tidak memunculkan portal vendor/tender di maybank.co.id. Hasil yang muncul hampir semuanya milik Maybank Malaysia/Singapura.
- Terkait grup [BERITA/pihak ketiga]: studi kasus vendor MyBiz Solutions menyebut tim strategic procurement Maybank ditugasi "transform procurement for Maybank Group through the implementation of a Group-wide eProcurement system" ([PDF mybiz.net](https://www.mybiz.net/_files/ugd/c29f77_aa494836ecc64a39bda6d27ee782e421.pdf), cuplikan pencarian 2026-10-23; datanya per 2012 sehingga bisa usang). Maybank Group juga menerbitkan Sustainable Procurement Principles ([salinan di banktrack.org](https://www.banktrack.org/download/sustainable_procurement_principles)) dan ESG Code of Conduct pemasok yang wajib dipatuhi ([PDF maybank2u.com.sg](https://www.maybank2u.com.sg/iwov-resources/sg/pdf/esg-code-of-conduct.pdf)); keduanya dari cuplikan pencarian 2026-10-23. Belum terverifikasi apakah Maybank Indonesia memakai sistem grup yang sama.
- (2) Akses publik: tidak diketahui.
- (3) Format: tidak diketahui; tidak ada RSS/API tender yang ditemukan.
- (4) Catatan teknis bot [PORTAL]: robots.txt www.maybank.co.id hanya "Disallow: /sitecore" + sitemap ([robots.txt](https://www.maybank.co.id/robots.txt), diakses 2026-10-23). Situs berbasis Sitecore (inferensi dari path). Halaman "NewsAndAnnouncement" Maybank Indonesia terindeks publik di mesin pencari (mis. [pengumuman pemeliharaan sistem rekening joint, 17 Apr 2026](https://www.maybank.co.id/en/NewsAndAnnouncement/NewsAndAnnouncements/2026/04/17/01/11/Informasi-Pemeliharaan-Sistem-Rekening-Joint), cuplikan pencarian; halaman tidak dibuka langsung), tapi tidak ditemukan pengumuman tender di sana.
- (5) Tender EDC Indonesia: [TIDAK DITEMUKAN]. Semua hasil EDC/POS/Tap2Phone/QRPayBiz yang muncul milik Maybank Malaysia, bukan Indonesia.

### 6. OCBC Indonesia (PT Bank OCBC NISP Tbk)
- (1) Portal e-procurement: [TIDAK DITEMUKAN]. Dua kueri hanya memunculkan OCBC Corporate Internet Banking ([business.ocbc.id](https://business.ocbc.id/), layanan nasabah, bukan vendor), anggaran dasar, dan rilis grup OCBC.
- Terkait grup [PORTAL grup]: OCBC menerbitkan [OCBC Supplier Code of Conduct (PDF)](https://www.ocbc.com/iwov-resources/sg/ocbc/gbc/pdf/ocbc-supplier-code-of-conduct.pdf) dan halaman [Acting with integrity](https://www.ocbc.com/group/sustainability/sustainability-framework/acting-with-integrity.page) yang menyebut sikap anti-suap disampaikan ke pemasok lewat "ABC Notification Guidance and Supplier Code of Conduct" (cuplikan pencarian 2026-10-23). Dokumen etika, bukan daftar tender.
- (2) Akses publik: tidak diketahui.
- (3) Format: tidak diketahui; tidak ada RSS/API tender yang ditemukan.
- (4) Catatan teknis bot [PORTAL]: robots.txt www.ocbc.id melarang semua URL ber-query string untuk semua bot ("Disallow: /*?", kecuali file .js/.css/.png/.ico dan ?rev=), melarang /sitecore dan /hasil-pencarian; khusus Googlebot juga melarang /*.pdf dan /*.ashx ([robots.txt](https://www.ocbc.id/robots.txt), diakses 2026-10-23). Implikasi: bot yang memakai URL pencarian/filter ber-parameter (?page=, ?q=) akan melanggar robots.txt situs ini. Berbasis Sitecore (inferensi dari path).
- (5) Tender EDC: [TIDAK DITEMUKAN]. Konteks bisnis: aplikasi [OCBC Merchant](https://play.google.com/store/apps/details?id=id.ocbc.merchant) untuk merchant OCBC; dan [rilis PR Newswire 10 Nov 2025](https://www.prnewswire.com/apac/news-releases/ocbc-launches-tap-credit-card-seamless-nfc-transactions-for-speed-and-convenience-302610100.html) tentang peluncuran Tap Credit Card (bayar dengan menempelkan ponsel Android NFC ke terminal EDC/POS contactless). Keduanya cuplikan pencarian 2026-10-23, bukan tender. Konteks lain: OCBC Indonesia menandatangani akuisisi bisnis ritel/wealth HSBC Indonesia pada 4 Mei 2026 ([rilis OCBC](https://www.ocbc.com/group/media/release/2026/ocbc-acquires-hsbc-international-wealth-and-premier-banking-indonesia)), yang bisa memicu kebutuhan integrasi sistem.

### 7. Panin Bank (PT Bank Pan Indonesia Tbk)
- (1) Portal e-procurement: [TIDAK DITEMUKAN]. Dua kueri (termasuk "pengumuman pengadaan tender vendor rekanan") hanya memunculkan laporan keuangan di panin.co.id dan profil perusahaan di situs pihak ketiga.
- (2) Akses publik: tidak diketahui.
- (3) Format: tidak diketahui; tidak ada RSS/API tender yang ditemukan.
- (4) Catatan teknis bot [PORTAL]: www.panin.co.id menolak alat fetch otomatis dengan HTTP 403 Forbidden di dua URL berbeda: [robots.txt](https://www.panin.co.id/robots.txt) dan halaman publik [/id/kurs](https://www.panin.co.id/id/kurs) (keduanya diakses 2026-10-23). Jadi ada proteksi bot/WAF di seluruh situs untuk klien non-browser; isi robots.txt dan ToS tidak terbaca. Path /sites/default/files/ pada PDF laporan keuangan menandakan CMS Drupal (inferensi dari path).
- (5) Tender EDC: [TIDAK DITEMUKAN]. Pencarian berita EDC Panin hanya memunculkan artikel umum EDC dan bank luar negeri.

### 8. Bank Mega (PT Bank Mega Tbk)
- (1) Portal e-procurement: [TIDAK DITEMUKAN]. Kueri pencarian hanya memunculkan halaman produk bankmega.com. Menu situs (Personal, Business, Services, About Us, Career, Blog) tidak memuat menu pengadaan/vendor; halaman [Corporate Governance](https://bankmega.com/en/about-us/corporate-governance/) (diakses 2026-10-23) hanya berisi laporan GCG 2009–2025, Board Manual, pedoman integritas/anti-fraud, anggaran dasar, dan GCG terintegrasi Mega Corpora, tanpa bagian pengadaan. Menu "Catalog of AYDA" adalah katalog agunan yang diambil alih (lelang aset), bukan tender pengadaan.
- (2) Akses publik: tidak diketahui.
- (3) Format: tidak diketahui; tidak ada RSS/API tender yang ditemukan. Bank Mega punya portal API perbankan untuk nasabah korporat ([developer.bankmega.com](https://developer.bankmega.com/), cuplikan pencarian), bukan API tender.
- (4) Catatan teknis bot [PORTAL]: robots.txt bankmega.com hanya melarang /admin/ dan /@@!!admin!!@@/, sisanya "Allow: /" ([robots.txt](https://bankmega.com/robots.txt), diakses 2026-10-23). Halaman situs berhasil diambil sebagai HTML biasa (bisa dibaca tanpa render JS). Path /media/filer_public/ menandakan Django CMS (inferensi dari path). ToS belum dicek.
- (5) Tender EDC: [TIDAK DITEMUKAN]. Konteks bisnis: ada dokumen Scribd berupa contoh "Surat Permohonan Penarikan EDC" yang ditujukan ke Bank Mega sebagai PIC Merchant Relationship (menyebut MID, TID, merek dan jumlah EDC) ([Scribd](https://www.scribd.com/document/343502745/Surat-Permohonan-Penarikan), cuplikan pencarian 2026-10-23; dokumen pihak ketiga, tidak terverifikasi). Ini menandakan Bank Mega mengelola armada EDC merchant, tapi bukan bukti tender.

### 9. SMBC Indonesia (PT Bank SMBC Indonesia Tbk, eks Bank BTPN)
- (1) Portal [PORTAL, tapi domain pihak ketiga]: dua alamat di platform iProc milik pengadaan.com, yaitu [iprocsmbci.pengadaan.com](https://iprocsmbci.pengadaan.com/) dan [smbci.pengadaan.com](https://smbci.pengadaan.com/) (keduanya diakses 2026-10-23). Footer halaman menyebut "Dikembangkan oleh ADW Consulting untuk PT Bank SMBC Indonesia Tbk" dan menautkan ke www.btpn.com. PERHATIAN: domainnya pengadaan.com, BUKAN domain bank (smbci.com/btpn.com). Belum ada tautan dari situs resmi bank yang mengonfirmasi portal ini; status kepemilikan = klaim di halaman portal, belum dicek silang.
- (2) Akses publik: TIDAK. Kedua alamat hanya menampilkan formulir "iProc Intranet — Login" (tampaknya untuk staf SCM internal, judul halaman "Internal PT Bank SMBCI Tbk"). Tidak ada daftar tender publik. Situs induk [pengadaan.com](https://pengadaan.com/) langsung mengalihkan ke login SSO (login.pengadaan.com), diakses 2026-10-23.
- (3) Format: tidak terlihat tanpa login. Tidak ada RSS/API publik.
- (4) Catatan teknis bot: halaman login berupa HTML sederhana; robots.txt di smbci.pengadaan.com tidak ada (HTTP 404, diakses 2026-10-23). Karena semua konten ada di balik login, bot tidak bisa memantau tanpa akun vendor; dan tugas ini melarang login/registrasi.
- (5) Tender EDC: [TIDAK DITEMUKAN]. Tidak ada daftar tender yang terlihat publik.
- Profil bank [PORTAL]: SMBC Indonesia adalah nama baru PT Bank BTPN Tbk, hasil merger BTPN dan PT Bank Sumitomo Mitsui Indonesia (Februari 2019) ([smbci.com/en/tentang-kami](https://www.smbci.com/en/tentang-kami), cuplikan hasil pencarian 2026-10-23).

### 10. UOB Indonesia (PT Bank UOB Indonesia) — tambahan, riset singkat
- (1) Portal e-procurement: [TIDAK DITEMUKAN]. Satu kueri hanya memunculkan halaman produk uob.co.id dan "UOB Procure-to-Pay" milik UOB Malaysia ([uob.com.my](https://uob.com.my/business/transact/cards/uob-procure-to-pay.page), cuplikan pencarian). Itu produk pembayaran untuk nasabah korporat, BUKAN portal vendor UOB.
- (2)/(3) Akses publik dan format: tidak diketahui; tidak ada RSS/API tender yang ditemukan.
- (4) Catatan teknis bot [PORTAL]: [robots.txt](https://www.uob.co.id/robots.txt) tidak ada di path standar (HTTP 404, diakses 2026-10-23). ToS belum dicek.
- (5) Tender EDC: tidak dicari mendalam karena batas waktu.

### 11. Bank Sinarmas (PT Bank Sinarmas Tbk) — tambahan, riset singkat
- (1) Portal e-procurement: [TIDAK DITEMUKAN]. Satu kueri hanya memunculkan dokumen RUPS, promo kartu kredit, dan profil ZoomInfo seorang staf "Information Technology Procurement" Bank Sinarmas (menandakan ada fungsi procurement TI internal, bukan portal publik).
- (2)/(3) Akses publik dan format: tidak diketahui; tidak ada RSS/API tender yang ditemukan.
- (4) Catatan teknis bot [PORTAL]: www.banksinarmas.com tidak bisa dihubungi alat fetch (gagal koneksi) baik untuk [robots.txt](https://www.banksinarmas.com/robots.txt) maupun halaman spesifik [/id/promosi/kartukredit](https://www.banksinarmas.com/id/promosi/kartukredit), diakses 2026-10-23. Penyebab tidak diketahui (bisa pembatasan lokasi/IP, bisa gangguan sementara); hasil pencarian membuktikan situsnya ada.
- (5) Tender EDC: tidak dicari mendalam karena batas waktu.

## Daftar tender / berita EDC
Tidak ada satu pun tender EDC (managed service, sewa/pengadaan, pemeliharaan, Android EDC/smart POS, field service, merchant acquiring) dari 11 bank ini yang ditemukan dalam batas riset. Tidak ada judul, nomor, atau tanggal tender yang bisa dicatat, dan tidak ada berita pemenang/kontrak EDC dengan nama bank yang ditemukan.

Yang ditemukan hanya konteks (bukan tender):

| Bank | Temuan | Jenis bukti | Sumber |
|---|---|---|---|
| BCA | Aplikasi Merchant BCA untuk pengajuan EDC/QRIS dan penanganan masalah EDC; Merchant Hotline BCA 1500788 | cuplikan pencarian (Google Play) | [Merchant BCA](https://play.google.com/store/apps/details?id=com.bca.msb), [info EDC BCA](https://play.google.com/store/apps/details?id=com.bca.info.edc) |
| CIMB Niaga | Aplikasi OCTO Merchant (package `com.cimbedc`) untuk mitra merchant | cuplikan pencarian | [Google Play](https://play.google.com/store/apps/details?hl=en&id=com.cimbedc) |
| Danamon | Layanan Merchant QR Danamon (aplikasi Android) | cuplikan pencarian (RIPLAY resmi) | [RIPLAY PDF](https://www.danamon.co.id/-/media/ALL-CONTENT-EBANKING/QRIS/QR-Merchant/18-06-2025/RIPLAY---Layanan-Merchant-QR-Danamon---Final_non-iOS-include-sameday---EN.pdf) |
| Permata | Aplikasi Permata QR Merchant | cuplikan pencarian | [Google Play](https://play.google.com/store/apps/details?hl=en_GB&id=com.permatabank.qram) |
| OCBC Indonesia | Aplikasi OCBC Merchant; peluncuran Tap Credit Card di terminal EDC/POS contactless (10 Nov 2025) | cuplikan pencarian (rilis PR Newswire) | [OCBC Merchant](https://play.google.com/store/apps/details?id=id.ocbc.merchant), [PR Newswire](https://www.prnewswire.com/apac/news-releases/ocbc-launches-tap-credit-card-seamless-nfc-transactions-for-speed-and-convenience-302610100.html) |
| Bank Mega | Contoh surat penarikan EDC yang ditujukan ke Bank Mega (PIC Merchant Relationship) | dokumen pihak ketiga, tidak terverifikasi | [Scribd](https://www.scribd.com/document/343502745/Surat-Permohonan-Penarikan) |

Konteks vendor EDC (bukan tender, berguna untuk peta pesaing/mitra):
- PT Prima Vista Solusi (PVS): profil PitchBook menyebut PVS menawarkan terminal EDC, payment gateway, integrated terminal management system, "full managed services", pelatihan kasir, distribusi kertas struk, dan EDC berbasis Android ([PitchBook](https://pitchbook.com/profiles/company/154346-14), cuplikan pencarian 2026-10-23). Akun resminya menyebut "PVS menyediakan layanan EDC, POS, dan Payment Gateway sejak 2002. Diawasi oleh Bank Indonesia" ([linktr.ee](https://linktr.ee/primavistasolusi), cuplikan pencarian). Daftar bank klien PVS TIDAK terverifikasi: situs [primavista-solusi.com](https://primavista-solusi.com/) tidak mengembalikan teks yang bisa dibaca (kemungkinan dirender JavaScript), diakses 2026-10-23.

## Keterbatasan
- "Tidak ditemukan" di file ini berarti tidak ketemu lewat web_search + web_fetch dalam ~45 menit, BUKAN bukti portal/tender tidak ada. Portal vendor bank swasta lazim berada di balik login dan diberi noindex, sehingga tidak muncul di mesin pencari.
- Mesin pencari yang dipakai lemah untuk berita berbahasa Indonesia: hasilnya didominasi halaman Google Play, situs luar negeri, dan repositori kampus. Media seperti Kontan, Bisnis.com, atau Infobank tidak muncul sama sekali untuk kueri EDC.
- Alat fetch tidak bisa membaca PDF dan sitemap XML. Laporan tahunan/laporan GCG (tempat bank biasanya menjelaskan kebijakan pengadaan) tidak terbaca; beberapa fakta hanya berasal dari cuplikan pencarian dan ditandai begitu.
- PermataBank dan Panin menolak alat fetch dengan 403; Bank Sinarmas tidak terjangkau. Blokir ini mungkin hanya berlaku untuk klien non-browser, jadi belum tentu berlaku untuk pengguna biasa.
- ToS situs tidak dicek untuk bank mana pun; yang dicek hanya robots.txt.
- Tidak ada login, registrasi, atau pengisian formulir (sesuai aturan tugas), jadi isi portal SMBC Indonesia di balik login tidak diketahui.
- UOB Indonesia dan Bank Sinarmas hanya diriset singkat.

## Sumber (URL + tanggal akses)
Semua diakses 2026-10-23 (WIB).

Dibuka langsung dan berhasil:
- [robots.txt BCA](https://www.bca.co.id/robots.txt)
- [iProc SMBC Indonesia (iprocsmbci)](https://iprocsmbci.pengadaan.com/)
- [iProc SMBC Indonesia (smbci)](https://smbci.pengadaan.com/)
- [robots.txt CIMB Niaga](https://www.cimbniaga.co.id/robots.txt)
- [robots.txt Danamon](https://www.danamon.co.id/robots.txt)
- [robots.txt Maybank Indonesia](https://www.maybank.co.id/robots.txt)
- [robots.txt OCBC Indonesia](https://www.ocbc.id/robots.txt)
- [robots.txt Bank Mega](https://bankmega.com/robots.txt)
- [Bank Mega — Corporate Governance](https://bankmega.com/en/about-us/corporate-governance/)

Dibuka langsung tapi gagal (hasil gagal itu sendiri dipakai sebagai temuan):
- [eproc.bca.co.id](https://eproc.bca.co.id/) — gagal koneksi
- [sitemap BCA](https://www.bca.co.id/sitemap.xml) — format XML tak didukung alat
- [robots.txt smbci.pengadaan.com](https://smbci.pengadaan.com/robots.txt) — 404
- [pengadaan.com](https://pengadaan.com/) — dialihkan ke login SSO
- [robots.txt PermataBank](https://www.permatabank.com/robots.txt) — 403
- [PermataBank bergabung-menjadi-merchant](https://www.permatabank.com/id/digital-channel/permataqr/bergabung-menjadi-merchant) — 403
- [robots.txt Panin](https://www.panin.co.id/robots.txt) — 403
- [Panin /id/kurs](https://www.panin.co.id/id/kurs) — 403
- [robots.txt UOB Indonesia](https://www.uob.co.id/robots.txt) — 404
- [robots.txt Bank Sinarmas](https://www.banksinarmas.com/robots.txt) — gagal koneksi
- [Bank Sinarmas /id/promosi/kartukredit](https://www.banksinarmas.com/id/promosi/kartukredit) — gagal koneksi
- [primavista-solusi.com](https://primavista-solusi.com/) — tidak ada teks terbaca (versi http gagal koneksi)
- [Makalah Telkom University EDC CIMB Niaga (PDF)](https://socj.telkomuniversity.ac.id/ojs/index.php/indojc/article/download/880/407) — PDF tak didukung alat

Hanya dari cuplikan hasil pencarian (halaman tidak dibuka):
- [CIMB Group Vendor Code of Conduct (PDF)](https://www.cimbbank.com.ph/content/dam/cimb/group/documents/sustainbility/vendor-code-of-conduct.pdf)
- [OCTO Merchant — Google Play](https://play.google.com/store/apps/details?hl=en&id=com.cimbedc)
- [Danamon AR 2024 Company Profile (PDF)](https://www.danamon.co.id/-/media/ALL-CONTENT-ABOUT-DANAMON/LAPORAN-KEUANGAN/LAPORAN-TAHUNAN/2024/en/5-Company-Profile-AR-Bank-Danamon-2024-ENG-25-Feb-Malam2web-Medium4.pdf)
- [RIPLAY Merchant QR Danamon (PDF)](https://www.danamon.co.id/-/media/ALL-CONTENT-EBANKING/QRIS/QR-Merchant/18-06-2025/RIPLAY---Layanan-Merchant-QR-Danamon---Final_non-iOS-include-sameday---EN.pdf)
- [Danamon TradeConnect](https://tradeconnect.danamon.co.id/)
- [Permata QR Merchant — Google Play](https://play.google.com/store/apps/details?hl=en_GB&id=com.permatabank.qram)
- [Studi kasus eProcurement Maybank Group — MyBiz (PDF)](https://www.mybiz.net/_files/ugd/c29f77_aa494836ecc64a39bda6d27ee782e421.pdf)
- [Maybank Group Sustainable Procurement Principles — banktrack.org](https://www.banktrack.org/download/sustainable_procurement_principles)
- [Maybank ESG Code of Conduct pemasok (PDF)](https://www.maybank2u.com.sg/iwov-resources/sg/pdf/esg-code-of-conduct.pdf)
- [Maybank Indonesia — pengumuman 17 Apr 2026](https://www.maybank.co.id/en/NewsAndAnnouncement/NewsAndAnnouncements/2026/04/17/01/11/Informasi-Pemeliharaan-Sistem-Rekening-Joint)
- [OCBC Corporate Internet Banking](https://business.ocbc.id/)
- [OCBC Supplier Code of Conduct (PDF)](https://www.ocbc.com/iwov-resources/sg/ocbc/gbc/pdf/ocbc-supplier-code-of-conduct.pdf)
- [OCBC — Acting with integrity](https://www.ocbc.com/group/sustainability/sustainability-framework/acting-with-integrity.page)
- [OCBC Merchant — Google Play](https://play.google.com/store/apps/details?id=id.ocbc.merchant)
- [PR Newswire — OCBC Tap Credit Card](https://www.prnewswire.com/apac/news-releases/ocbc-launches-tap-credit-card-seamless-nfc-transactions-for-speed-and-convenience-302610100.html)
- [OCBC — akuisisi HSBC IWPB Indonesia](https://www.ocbc.com/group/media/release/2026/ocbc-acquires-hsbc-international-wealth-and-premier-banking-indonesia)
- [Bank Mega Developer API](https://developer.bankmega.com/)
- [Scribd — Surat Permohonan Penarikan EDC](https://www.scribd.com/document/343502745/Surat-Permohonan-Penarikan)
- [SMBC Indonesia — Tentang Kami](https://www.smbci.com/en/tentang-kami)
- [UOB Procure-to-Pay (Malaysia)](https://uob.com.my/business/transact/cards/uob-procure-to-pay.page)
- [Merchant BCA — Google Play](https://play.google.com/store/apps/details?id=com.bca.msb)
- [info EDC BCA — Google Play](https://play.google.com/store/apps/details?id=com.bca.info.edc)
- [PitchBook — Prima Vista Solusi](https://pitchbook.com/profiles/company/154346-14)
- [linktr.ee — Prima Vista Solusi](https://linktr.ee/primavistasolusi)
- [eProc Vendor BRI](https://eproc.bri.co.id/) (pembanding saja, di luar cakupan bagian 2)
