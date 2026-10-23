# Riset Tender Bot — Bagian 3: BPD, Portal Agregat, dan Berita Tender EDC Lintas-Bank

Status: SELESAI (versi akhir run ini)
Mulai: 2026-10-23 15:05 WIB · Tanggal akses semua sumber: 2026-10-23
Metode: DeerFlow ringkas (Coordinator → Planner → Research Team → Reporter); alat hanya web_search + web_fetch.

## Pertanyaan inti
Di mana dan bagaimana BPD utama, portal pengadaan agregat, dan media mengumumkan tender (khususnya EDC: managed service, pengadaan, sewa, pemeliharaan), dan seberapa layak dipantau otomatis oleh bot?

## Legenda status bukti
- [PORTAL] = terverifikasi langsung dari portal/situs resmi (di-fetch)
- [BERITA] = dari berita/pihak ketiga
- [TIDAK DITEMUKAN] = dicari, tidak ketemu (bukan berarti pasti tidak ada)
- [TERBATAS] = tidak bisa diverifikasi karena portal gagal di-fetch / butuh login / JS

## Rencana (Planner)
1. BPD utama: bjb, Jatim, DKI, Jateng, Sumut, Nagari, BPD Bali, Kalbar/Kaltimtara
2. SPSE/LPSE & INAPROC: apakah BPD/BUMD memakainya
3. Portal pengadaan BUMN bersama
4. Agregator tender swasta (berbayar) + model akses
5. Iklan tender di media cetak/online
6. Berita tender/pemenang EDC lintas-bank (3 tahun terakhir) + vendor yang sering menang

## Jawaban singkat
Dari 9 BPD yang dicek, hanya Bank Jatim dan Bank Sumut yang daftar tendernya terbaca penuh dengan fetch HTML biasa. Bank Sumut baru mengumumkan tender EDC: "Sewa Beli Mesin Smart EDC", nomor 005/LPd-PP/SMRT-EDC-BS/L/2026, diposting 13 Okt 2026, nilai Rp6,993 miliar (batas pendaftaran ada di lampiran yang belum terbaca). BPD tampak memakai portal dan aturan pengadaan sendiri, bukan SPSE/INAPROC, dan tidak ada agregator yang terlihat meliput tender bank secara sistematis. Jadi bot perlu memantau situs tiap bank langsung. Sebagian situs (bjb, Bank Jakarta/DKI, Jateng, Kalbar) dirender JavaScript atau menolak klien otomatis.

## Tabel ringkas
| Bank/Portal | URL pengadaan | Akses baca | Format | RSS/API | Kesulitan bot | Tender EDC |
|---|---|---|---|---|---|---|
| Bank Sumut | [/pengadaan-barang-jasa/](https://www.banksumut.co.id/pengadaan-barang-jasa/) | Publik | WordPress (post `jasa_barang`) + lampiran | RSS `/feed/` ada; REST JSON merespons (isi belum dicek) | Rendah | YA — Smart EDC sewa beli, 13 Okt 2026, Rp6,993 M [PORTAL] |
| Bank Jatim | [Lelang Pengadaan](https://www.bankjatim.co.id/id/informasi/lelang-pengadaan) | Publik; pendaftaran peserta luring | HTML daftar + PDF | Tidak terlihat | Rendah (robots tanpa Disallow) | Tidak ditemukan; ada sewa ATM & CRM 2022 |
| BPD Bali | menu "INFO LELANG" (URL belum tertangkap) | ? | HTML server-side | ? | Sedang (perlu pemetaan URL sekali) | Tidak ditemukan |
| Bankaltimtara | menu "Info Lelang" (beda dari "Info Lelang Jaminan") | ? | HTML | ? | Sedang | Tidak ditemukan; bank punya layanan EDC sendiri |
| Bank Nagari | menu "Informasi Lelang" | ? | HTML, parameter URL terenkripsi | ? | Sedang | Tidak ditemukan |
| bank bjb | tidak ditemukan | ? | situs JS; eproc.* = halaman tantangan | ? | Tinggi | Tidak ditemukan |
| Bank DKI → Bank Jakarta | tidak ditemukan; ada VMS calon vendor (pihak ketiga) | ? | — | ? | Tinggi (HTTP 403) | Tidak ditemukan |
| Bank Jateng | tidak ditemukan (lelang.* = agunan) | ? | konten dimuat JS | ? | Tinggi | Tidak ditemukan |
| Bank Kalbar | tidak ditemukan | ? | tak terbaca | ? | Tinggi | Tidak ditemukan |
| SPSE/LPSE/INAPROC | — | Publik | — | pyproc (open source) | — | BPD tak terlihat memakai |
| TenderKita | [tenderkita.com](https://tenderkita.com/) | Publik | daftar LPSE + beberapa BUMD | ? | — | Tidak ada bank di daftar instansi |
| Tender Indonesia | [tender-indonesia.com](https://tender-indonesia.com/) | Diduga berbayar (tak terverifikasi) | — | ? | — | Tidak terverifikasi |

## Implikasi untuk Tender Bot
1. Prioritas 1 (fetch HTML sederhana, bisa jalan hari ini): Bank Sumut (coba RSS/REST WordPress dulu, cadangan: halaman arsip) dan Bank Jatim (daftar HTML + pola URL PDF `files/pengumuman/<tahun>/<bulan>/`).
2. Prioritas 2 (petakan URL menu "Info Lelang" sekali secara manual, lalu fetch biasa): BPD Bali, Bankaltimtara, Bank Nagari.
3. Prioritas 3 (butuh browser headless dan pola akses sopan, atau cukup dipantau lewat berita): bjb, Bank Jakarta/DKI, Bank Jateng, Bank Kalbar.
4. Filter wajib: kata "lelang" saja tidak cukup; buang item berisi "agunan"/"jaminan" (Jateng, Nagari, Bankaltimtara punya portal lelang agunan).
5. Alias nama: "Bank DKI" = "Bank Jakarta" (domain baru sejak Agustus 2026).

## Rincian per bank/portal

### 1. Bank Jatim (PT BPD Jawa Timur Tbk)
- URL resmi daftar tender: [Lelang Pengadaan – bankjatim.co.id](https://www.bankjatim.co.id/id/informasi/lelang-pengadaan) [PORTAL, diakses 2026-10-23]
- Akses: PUBLIK, tanpa login, untuk membaca daftar dan PDF pengumuman. Pendaftaran peserta/pengambilan dokumen kualifikasi secara historis LURING: "General Division Room, 3rd floor, Jl. Basuki Rachmad 98-104 Surabaya", dengan surat tugas asli, akta PT, NIB (contoh: [pengumuman Mobile App Security 2025, PDF](https://www.bankjatim.co.id/files/pengumuman/2025/september/pengumuman_website_pengadaan_english.pdf)) [PORTAL via hasil pencarian, diakses 2026-10-23]
- Format: halaman daftar HTML (tanggal + judul), isi per item tertaut ke PDF. Jenis item yang terlihat di halaman 1 (22 Okt 2026 s.d. 18 Sep 2026): "Pengumuman Tender Pascakualifikasi", "Market Sounding", "Hasil Rekapitulasi Evaluasi Dokumen Penawaran", "Pengumuman Pemenang". Contoh: "Pengumuman Tender Pascakualifikasi Pengadaan 1 (satu) Unit Server Baremetal DataWarehouse Bank Jatim" (16 Okt 2026), "Pemenang Pengadaan Network Monitoring System (NMS) Bank Jatim" (14 Okt 2026). [PORTAL, diakses 2026-10-23]
- Pola URL PDF konsisten dan mudah ditebak bot: `bankjatim.co.id/files/pengumuman/<tahun>/<bulan>/<nama>.pdf` (juga mirror domain `bankjatim.id`). Ada versi bahasa Inggris (`..._english.pdf`).
- RSS/API: tidak terlihat. [TIDAK DITEMUKAN]
- Catatan teknis bot: daftar dirender server-side (teks judul dan tanggal langsung terbaca oleh web_fetch biasa, tanpa JS); paginasi "1 2 3 4 Next Last"; tidak ada CAPTCHA saat fetch. Pola URL halaman detail dan parameter paginasi tidak tertangkap oleh alat fetch (hanya label link) [TERBATAS]. `robots.txt` hanya berisi `User-agent: *` tanpa baris Disallow, jadi tidak ada larangan crawling di robots.txt ([robots.txt](https://www.bankjatim.co.id/robots.txt), diakses 2026-10-23). Halaman ToS soal scraping tidak dicek.
- Peringatan: halaman "Pengumuman" ([link](https://www.bankjatim.co.id/id/informasi/pengumuman)) berbeda dari "Lelang Pengadaan" dan berisi promo/IR, bukan tender. Bot harus memantau "Lelang Pengadaan".
- Tender EDC: TIDAK DITEMUKAN pengumuman EDC lewat pencarian. Yang paling dekat (kategori sewa perangkat kanal): "Procurement of ATM Machine Rental Service" 2022, HPS Rp3.118.197 per unit per bulan, pendaftaran 29 Jun–5 Jul 2022 ([PDF](https://www.bankjatim.id/files/pengumuman/2022/juni/pengumuman_website_pengadaan_jasa_sewa_mesin_atm_2022_english.pdf)), dan "Jasa Sewa Mesin CRM 2022" ([PDF](https://www.bankjatim.id/files/pengumuman/2022/juli/pengumuman_website_pengadaan_jasa_sewa_mesin_crm_2022_english.pdf)). [PORTAL via hasil pencarian, diakses 2026-10-23]

### 2. Bank Jateng (PT BPD Jawa Tengah) — catatan awal
- JEBAKAN: subdomain [lelang.bankjateng.co.id](https://lelang.bankjateng.co.id/) adalah portal LELANG AGUNAN (jual aset jaminan: private selling/lelang/non-lelang), BUKAN pengadaan barang/jasa. Bot tidak boleh memakai kata "lelang" saja sebagai penanda tender. [PORTAL, diakses 2026-10-23]
- Rincian pengadaan: lihat bagian 6 (Bank Jateng, lanjutan).

### 3. Bank Sumut (PT BPD Sumatera Utara / Perseroda) — TEMUAN EDC TERBARU
- URL resmi: [Pengadaan Barang & Jasa – banksumut.co.id](https://www.banksumut.co.id/pengadaan-barang-jasa/) dan arsip [archive-jasa-barang](https://www.banksumut.co.id/archive-jasa-barang/); versi Inggris [procurement-of-goods-and-services](https://www.banksumut.co.id/en/procurement-of-goods-and-services/). [PORTAL, diakses 2026-10-23]
- Akses: PUBLIK, tanpa login untuk membaca pengumuman. Pedoman: Peraturan Bank SUMUT No. 007/Dir/Dum-ULP/PBS/2023 tgl 22 Nov 2023 (teks halaman daftar) — halaman detail menulis "007/Dir/DUm-LPd/PBS/2023 tanggal 21 November 2023". Ada selisih kode/tanggal di teks bank sendiri; dicatat apa adanya.
- TENDER EDC (masih tayang saat diakses; batas pendaftaran tidak diketahui):
  - Judul: "Pekerjaan Pengadaan Sewa Beli Mesin Smart Electronic Data Capture (Smart EDC) PT Bank Sumut (Perseroda)"
  - Nomor: 005/LPd-PP/SMRT-EDC-BS/L/2026
  - Tanggal posting: Selasa, 13 Oktober 2026
  - Metode: Pelelangan Umum, Sistem Pascakualifikasi
  - Nilai Pekerjaan: Rp6.993.000.000
  - Status: diumumkan; jadwal pendaftaran dan dokumen lengkap ada di lampiran unduhan yang tautannya TIDAK tertangkap oleh alat fetch [TERBATAS]
  - Link: [detail tender Smart EDC](https://www.banksumut.co.id/jasa_barang/pekerjaan-pengadaan-sewa-beli-mesin-smart-electronic-data-capture-smart-edc-pt-bank-sumut-perseroda/) [PORTAL, diakses 2026-10-23]
- Format: WordPress. Pengumuman = custom post type `jasa_barang`, pola URL `/jasa_barang/<slug-judul>/`; ringkasan teks di HTML + lampiran unduhan.
- RSS/API: endpoint [/feed/](https://www.banksumut.co.id/feed/) merespons dengan content-type `application/rss+xml` (feed RSS situs ada). Endpoint REST WordPress `/wp-json/wp/v2/jasa_barang?per_page=5` merespons `application/json`, tetapi isinya tidak bisa dibaca alat riset — perlu dicek apakah berisi data tender atau pesan error [TERBATAS]. Feed khusus `jasa_barang` (`/jasa_barang/feed/`) belum diuji.
- Catatan teknis bot: HTML dirender server (judul, nomor, nilai terbaca tanpa JS); tidak ada CAPTCHA saat fetch. Kandidat jalur termurah: RSS/REST WordPress bila memuat `jasa_barang`, jika tidak, polling halaman arsip. robots.txt/ToS belum dicek.
- JEBAKAN: menu "Lelang PT Bank Sumut" ([/lelang/](https://www.banksumut.co.id/lelang/)) terpisah dari "Pengadaan Barang & Jasa"; kemungkinan lelang agunan (belum dibuka).

### 4. bank bjb (PT BPD Jawa Barat dan Banten Tbk)
- Halaman pengadaan publik di situs utama: TIDAK DITEMUKAN lewat pencarian. Fetch [bankbjb.co.id](https://www.bankbjb.co.id/) hanya mengembalikan judul "Bank bjb Bakti Untuk Negri." — indikasi situs dirender JavaScript sehingga isi menu tak terbaca alat biasa. [TERBATAS, diakses 2026-10-23]
- Subdomain `eproc.bankbjb.co.id` (ditebak dari pola umum, BUKAN dari tautan resmi) merespons halaman "Please wait a while..." — pola halaman tantangan anti-bot/JS. Keberadaan dan fungsi portal ini sebagai e-procurement resmi bjb BELUM terverifikasi. [TERBATAS]
- Tender EDC bjb: TIDAK DITEMUKAN (pencarian "bjb pengadaan EDC" hanya menghasilkan dokumen panduan kendala EDC bjb di Scribd, bukan tender).
- Konteks risiko: KPK menyidik dugaan korupsi pengadaan iklan bjb periode 2021–2023 ([VOI, 2026](https://voi.id/en/news/597746), diakses 2026-10-23) [BERITA]. Relevan sebagai catatan bahwa transparansi pengadaan bjb sedang disorot; tidak membuktikan apa pun soal pengadaan EDC.
- Implikasi bot: bjb butuh browser headless (atau pemantauan berita/agregator) — tidak cocok untuk fetch HTML sederhana.

### 5. Bank DKI → kini "Bank Jakarta"
- Perubahan domain: situs resmi pindah dari bankdki.co.id ke [bankjakarta.co.id](https://www.bankjakarta.co.id/) (diumumkan 9 Agustus 2026) ([VOI, 9 Agu 2026](https://voi.id/en/economy/588894), diakses 2026-10-23) [BERITA]. Bot harus memakai nama "Bank DKI" DAN "Bank Jakarta" sebagai kata kunci.
- Akses: kedua domain ([bankjakarta.co.id](https://www.bankjakarta.co.id/) dan [bankdki.co.id](https://www.bankdki.co.id/)) mengembalikan HTTP 403 Forbidden ke alat fetch — ada proteksi anti-bot/WAF. [TERBATAS, diakses 2026-10-23]
- Registrasi vendor: ada sistem pendaftaran "Calon Vendor PT. Bank DKI" online (jenis vendor mis. Prinsipal; kategori NON-IT/KONSTRUKSI; konfirmasi via email) — hanya dari cuplikan dokumen yang diunggah pihak ketiga di [Scribd](https://www.scribd.com/document/775698019/Vendor-Management-Bank-DKI) [BERITA/PIHAK KETIGA, diakses 2026-10-23]. URL sistemnya tidak ditemukan.
- Halaman pengumuman tender publik & tender EDC: TIDAK DITEMUKAN.
- Implikasi bot: perlu browser headless dengan pola akses sopan, atau sumber sekunder (berita, agregator).

### 6. Bank Jateng (lanjutan)
- Situs utama [bankjateng.co.id](https://www.bankjateng.co.id/) bisa di-fetch, tetapi isi berita/pengumuman hanya tampil sebagai placeholder "Loading." — konten dimuat JavaScript. Ada tab "Pengumuman" di beranda. [TERBATAS, diakses 2026-10-23]
- Beberapa subdomain (mis. plo., ibanking., pengaduan.) muncul di hasil pencarian dengan judul "Request Rejected" — pola WAF yang menolak klien otomatis. [dari hasil pencarian, 2026-10-23]
- Halaman pengadaan barang/jasa & tender EDC: TIDAK DITEMUKAN. Ingat: lelang.bankjateng.co.id = lelang agunan (lihat bagian 2).

### 7. Bank Nagari (PT BPD Sumatera Barat)
- Situs [banknagari.co.id](https://www.banknagari.co.id/) terbaca (HTML server-side). Menu PUBLIKASI memuat "Berita dan Informasi" dan "Informasi Lelang". URL "Informasi Lelang" tidak tertangkap, dan halaman situs memakai parameter terenkripsi (contoh pola: `produk?page=jWypp0/091XwfzajKYzOGA%3D%3D`), sehingga URL tak bisa ditebak. [PORTAL/TERBATAS, diakses 2026-10-23]
- Belum dipastikan apakah "Informasi Lelang" berisi pengadaan atau lelang agunan. Bank Nagari punya aplikasi terpisah "Nagari Portal Lelang" untuk agunan ([andro.io](https://bn-webview.andro.io/), pihak ketiga).
- Tender EDC: TIDAK DITEMUKAN.

### 8. BPD Bali (Bank BPD Bali)
- Situs [bpdbali.co.id](https://www.bpdbali.co.id/) terbaca (menu HTML server-side). Ada menu utama "INFO LELANG" dan "KONTAK > Pengumuman". URL "INFO LELANG" tidak tertangkap alat; isinya (pengadaan vs agunan) belum diverifikasi. [PORTAL/TERBATAS, diakses 2026-10-23]
- Tender EDC: TIDAK DITEMUKAN.

### 9. Bankaltimtara (BPD Kaltim & Kaltara)
- Situs [bankaltimtara.co.id](https://www.bankaltimtara.co.id/) terbaca. Di bawah "Berita" ada "Info Lelang", TERPISAH dari tautan "Info Lelang Jaminan (membuka tab baru)" — indikasi "Info Lelang" adalah lelang pengadaan, tapi belum dibuka. Ada pegawai berjabatan "Pengadaan Barang and Jasa" (profil [ZoomInfo](https://www.zoominfo.com/p/Rizky-Putra/17708517810), pihak ketiga). [PORTAL/TERBATAS, diakses 2026-10-23]
- Bankaltimtara punya layanan "EDC Bankaltimtara" dan QRIS (menu Layanan Elektronik), artinya bank ini mengoperasikan EDC sendiri dan calon pembeli pengadaan/sewa EDC. [PORTAL]
- Tender EDC: TIDAK DITEMUKAN.

### 10. Bank Kalbar
- Fetch [bankkalbar.co.id](https://www.bankkalbar.co.id/) hanya mengembalikan kerangka tabel tanpa teks menu yang berguna; subdomain cms.bankkalbar.co.id berjudul "Request Rejected" di hasil pencarian. Halaman pengadaan & tender EDC: TIDAK DITEMUKAN. [TERBATAS, diakses 2026-10-23]

### 11. Catatan BPD lain (di luar daftar, ditemukan sambil lalu)
- Bank Sultra punya portal tender sendiri [e-tender.banksultra.co.id](https://e-tender.banksultra.co.id/) ("Tender Online"; contoh paket di cuplikan: "PENGADAAN MEUBELAIR TOWER PT BANK PEMBANGUNAN DAERAH SULAWESI TENGGARA 14,547,000,000") [dari hasil pencarian, belum di-fetch].
- Bank Sulteng: [eproc.banksulteng.co.id](https://eproc.banksulteng.co.id/) muncul di hasil pencarian [belum di-fetch].
- Pola: sebagian BPD memakai e-procurement milik sendiri, bukan SPSE.

## Portal agregat dan jalur lain

### A. SPSE/LPSE & INAPROC — apakah BPD/BUMD memakainya?
- Bukti langsung dari pengumuman bank: Bank Jatim merujuk "Decision of Bank Jatim Directors No.060/03/34/DIR/UMM/KEP" sebagai pedoman pengadaan, dan Bank Sumut merujuk Peraturan Direksi 007/2023. Keduanya mengumumkan di situs sendiri (Jatim: pendaftaran luring di kantor pusat), bukan lewat SPSE. [PORTAL]
- Agregator TenderKita memisahkan sumber "LPSE ..." dari portal e-proc BUMD/BUMN sendiri ("eSCM PT Transportasi Jakarta", "PT Jakarta Propertindo (PERSERODA)", "PT Bukit Asam Tbk (SPEND)") — konsisten dengan pola BUMD memakai sistem sendiri ([tenderkita.com](https://tenderkita.com/), diakses 2026-10-23). Tidak satu pun bank ada di daftar instansi TenderKita.
- Dasar hukum (mis. PP 54/2017 tentang BUMD, ruang lingkup Perpres 16/2018): TIDAK terverifikasi dalam riset ini; pencarian tidak memberi sumber primer. Kesimpulan "BPD tidak wajib SPSE" adalah dugaan kuat dari pola pengumuman, belum dari teks peraturan.
- Akses teknis data SPSE untuk bot (bila ada BUMD yang memakai LPSE pemda): pustaka open source [pyproc (GitHub)](https://github.com/wakataw/pyproc) mengubah data publik SPSE/Inaproc menjadi alat MCP/Python; dan [Nusantara Procurement Data](https://nusantara-platform.site/) mengklaim 1.785.304 tender pemerintah sejak 2008 dari 597 portal [dari hasil pencarian, pihak ketiga, diakses 2026-10-23].

### B. Portal pengadaan BUMN bersama
- [PaDi UMKM](https://apps.apple.com/it/app/padi-umkm-seller/id1588822356): marketplace inisiatif Kementerian BUMN yang mempertemukan BUMN dengan produk UMKM (aplikasi dikembangkan Telkom). Ini katalog belanja UMKM, BUKAN portal tender terbuka, dan BPD bukan BUMN. Relevansi untuk tender EDC: rendah. [pihak ketiga/app store, diakses 2026-10-23]
- Portal tender bersama untuk seluruh BUMN: TIDAK DITEMUKAN; tiap BUMN/bank tampak memakai portal sendiri (contoh di hasil pencarian: lelang.bankmandiri.co.id — tidak dibuka, di luar cakupan bagian 3).
- Contoh format terstruktur yang bagus untuk parser: halaman pengadaan Bank Indonesia memuat field "Nomor Pengadaan, Nama Pengadaan, Tanggal Pengumuman, Satuan Kerja, Cara Pengadaan, Metode Evaluasi, Pagu, Status (mis. Open for RFI), Closing Date, Rekanan Pemenang, Lampiran" ([contoh BI, 2026](https://www.bi.go.id/id/layanan/lelang-jasa-barang/announcement/Pages/Pengadaan-Infrastruktur-Software-Microsoft-Azure-Local-untuk-Infra-Dev-Test-Bank-Indonesia-TA-2026.aspx)) [dari hasil pencarian].

### C. Agregator tender swasta / pihak ketiga
| Layanan | Cakupan yang terlihat | Model akses | Status bukti |
|---|---|---|---|
| [TenderKita](https://tenderkita.com/) | LPSE pemerintah + beberapa e-proc BUMD/BUMN; filter kata kunci, jenis, lokasi, instansi | Daftar tender terbaca publik tanpa login (halaman depan) | [PORTAL, 2026-10-23]; bank tidak ada di daftar instansi |
| [Tender Indonesia](https://tender-indonesia.com/tender_home/tender.php) | Klaim "complete bid/tender information in Indonesia"; layanan Tender Info & Tender Award Info; pemilik proyek pemerintah & BUMN | Model langganan/biaya TIDAK terbaca (halaman berupa tata letak); [blog pihak ketiga](https://abouttenderindonesia.blogspot.com/) menyebut fokus migas, tambang, listrik, telekomunikasi, infrastruktur | [TERBATAS] |
| [pengadaan.info](https://pengadaan.info/) | "Informasi LPSE Terbaru Hari Ini" | Belum dibuka | [dari hasil pencarian] |
| [IndoTender](http://indotender.com/) | Data tender LPSE + pencarian perusahaan, volume historis | Belum dibuka | [dari hasil pencarian] |
| [TenderTiger](https://indonesia.tendertiger.com/), [tenderinfo.org](http://indonesia.tenderinfo.org/), [IndonesiaTenders](https://www.indonesiatenders.com/) | Agregator internasional (tender pemerintah, proyek besar) | Umumnya berbayar (belum diverifikasi) | [dari hasil pencarian] |
- Kesimpulan sementara: tidak ada agregator yang terlihat mencakup tender bank/BPD secara sistematis. Untuk tender EDC bank, sumber primer tetap situs masing-masing bank.

### D. Iklan tender di media cetak/online
- Biro iklan mencantumkan kategori "Iklan Lelang Bisnis Indonesia" dan "Iklan Pengumuman Bisnis Indonesia" ([pusatpemasanganiklan.com](https://pusatpemasanganiklan.com/koran/1-bisnis-indonesia), diakses 2026-10-23) — membuktikan jalur iklan lelang di koran nasional masih dijual, BUKAN bahwa bank memakainya untuk tender EDC.
- Iklan tender EDC bank di koran: TIDAK DITEMUKAN. Arsip iklan koran digital (mis. toko.bisnis.com) berbayar dan tidak dibuka.

## Tender/berita EDC lintas-bank

### Tender EDC yang terverifikasi
| Bank | Judul | Nomor | Tanggal | Nilai | Status | Sumber |
|---|---|---|---|---|---|---|
| Bank Sumut | Pekerjaan Pengadaan Sewa Beli Mesin Smart Electronic Data Capture (Smart EDC) PT Bank Sumut (Perseroda) | 005/LPd-PP/SMRT-EDC-BS/L/2026 | posting 13 Okt 2026 | Rp6.993.000.000 | Pelelangan Umum pascakualifikasi, diumumkan (jadwal di lampiran, belum terbaca) | [PORTAL](https://www.banksumut.co.id/jasa_barang/pekerjaan-pengadaan-sewa-beli-mesin-smart-electronic-data-capture-smart-edc-pt-bank-sumut-perseroda/), diakses 2026-10-23 |

### Tender sejenis (perangkat kanal, bukan EDC)
| Bank | Judul | Tanggal | Nilai/HPS | Sumber |
|---|---|---|---|---|
| Bank Jatim | Procurement of ATM Machine Rental Service | pendaftaran 29 Jun–5 Jul 2022 | Rp3.118.197 per unit per bulan (incl. PPN) | [PDF resmi](https://www.bankjatim.id/files/pengumuman/2022/juni/pengumuman_website_pengadaan_jasa_sewa_mesin_atm_2022_english.pdf) |
| Bank Jatim | Pengadaan Jasa Sewa Mesin CRM 2022 | Juli 2022 | tidak terbaca di cuplikan | [PDF resmi](https://www.bankjatim.id/files/pengumuman/2022/juli/pengumuman_website_pengadaan_jasa_sewa_mesin_crm_2022_english.pdf) |

### Tidak ditemukan
- Berita pemenang tender "Managed Service EDC", "pengadaan EDC", "sewa EDC", "pemeliharaan EDC" di bank mana pun dalam 3 tahun terakhir: TIDAK DITEMUKAN lewat web_search. Ini keterbatasan riset (lihat di bawah), bukan bukti tender semacam itu tidak ada.
- Daftar "vendor yang sering menang" tender EDC: TIDAK DITEMUKAN di sumber publik.

### Lanskap vendor EDC (konteks, BUKAN data pemenang tender)
- PT Prima Vista Solusi (PVS): "menyediakan layanan EDC, POS, dan Payment Gateway sejak 2002. Diawasi oleh Bank Indonesia" ([linktr.ee resmi PVS](https://linktr.ee/primavistasolusi); [situs PVS](http://primavista-solusi.com/)). Abstrak laporan kerja praktik mahasiswa UPJ menyebut PVS-WIDE sebagai distributor EDC yang memperbaiki EDC Verifone, menangani penarikan/pengembalian EDC rusak dari Bank Artha Graha, Bank Mandiri, BTPN, Permata Bank, dan BNI, serta proyek EDC C680 untuk Mitra Transaksi Indonesia (MTI) dan EDC Ingenico untuk Perdana Prima Bakti Mandiri (PPBM) ([eprints UPJ](http://eprints.upj.ac.id/id/eprint/6216/3/abstract.pdf)) [PIHAK KETIGA, tahun laporan tidak tercantum di cuplikan].
- PT Mitra Transaksi Indonesia (dba Yokke): perusahaan patungan solusi pembayaran, berdiri 2016 ([Preqin](https://www.preqin.com/data/profile/asset/pt-mitra-transaksi-indonesia/449977)) [PIHAK KETIGA].
- Ingenico memasarkan terminal Android AXIUM untuk bank/acquirer di APAC termasuk konteks QRIS Indonesia ([blog Ingenico](https://ingenico.com/apac/newsroom/blogs/beyond-payments-why-modern-infrastructure-becoming-strategic-across-apac)) [materi pemasaran vendor, bukan bukti kontrak].

### Catatan kata kunci untuk bot
- "EDC" bertabrakan dengan Export Development Canada, Electric Daisy Carnival, dan "everyday carry" di hasil pencarian. Pakai frasa: "Electronic Data Capture", "mesin EDC", "Smart EDC", "EDC Android", "terminal EDC", plus konteks bank.
- Bank Sumut memakai istilah "Sewa Beli" — kata kunci bot harus mencakup: pengadaan, sewa, sewa beli, pemeliharaan, managed service, pengelolaan, jasa layanan EDC.

## Keterbatasan
1. Sesuai aturan tugas, tidak memakai browser/Playwright. Akibatnya situs yang dirender JavaScript (bjb, Bank Jateng), yang menolak klien otomatis (Bank Jakarta/DKI: HTTP 403; beberapa subdomain Jateng/Kalbar: "Request Rejected"; eproc.bankbjb.co.id: "Please wait a while...") tidak bisa dibaca. "Tidak ditemukan" pada bank-bank ini berarti "tidak terbaca", bukan "tidak ada".
2. Menu "Info Lelang"/"Informasi Lelang" di BPD Bali, Bankaltimtara, dan Bank Nagari tidak dibuka karena URL-nya tidak tertangkap alat fetch (hanya label menu); isinya bisa pengadaan atau lelang agunan.
3. Lampiran unduhan tender Smart EDC Bank Sumut (jadwal, syarat, HPS rinci) tidak tertangkap; hanya ringkasan HTML yang terverifikasi.
4. Endpoint RSS (`/feed/`) dan REST JSON Bank Sumut terbukti merespons dengan content-type yang benar, tetapi isinya tidak bisa dibaca alat riset; perlu satu uji manual/oleh bot.
5. robots.txt hanya dicek untuk Bank Jatim; syarat penggunaan (ToS) soal scraping tidak dicek untuk situs mana pun.
6. Dasar hukum pengadaan BUMD (PP 54/2017, ruang lingkup Perpres 16/2018) tidak terverifikasi dari sumber primer.
7. Pencarian web didominasi PDF Bank Jatim dan halaman Bank Indonesia; cakupan BPD lain dan berita pemenang tender tidak merata. Riset dibatasi ~45 menit, sehingga Bank Kalbar dan Bankaltimtara dangkal.
8. Model harga/akses agregator berbayar (Tender Indonesia, TenderTiger, dll.) tidak terverifikasi.

## Daftar URL sumber + tanggal akses
Semua diakses 2026-10-23. Kode: F = di-fetch langsung; S = hanya dari cuplikan hasil pencarian.

Bank Jatim
- F [Lelang Pengadaan](https://www.bankjatim.co.id/id/informasi/lelang-pengadaan)
- F [Pengumuman (non-tender)](https://www.bankjatim.co.id/id/informasi/pengumuman)
- F [robots.txt](https://www.bankjatim.co.id/robots.txt)
- S [Mobile App Security 2025 (PDF)](https://www.bankjatim.co.id/files/pengumuman/2025/september/pengumuman_website_pengadaan_english.pdf)
- S [ATM Machine Rental 2022 (PDF)](https://www.bankjatim.id/files/pengumuman/2022/juni/pengumuman_website_pengadaan_jasa_sewa_mesin_atm_2022_english.pdf)
- S [Sewa Mesin CRM 2022 (PDF)](https://www.bankjatim.id/files/pengumuman/2022/juli/pengumuman_website_pengadaan_jasa_sewa_mesin_crm_2022_english.pdf)

Bank Sumut
- F [Pengadaan Barang & Jasa](https://www.banksumut.co.id/pengadaan-barang-jasa/)
- F [Detail tender Smart EDC](https://www.banksumut.co.id/jasa_barang/pekerjaan-pengadaan-sewa-beli-mesin-smart-electronic-data-capture-smart-edc-pt-bank-sumut-perseroda/)
- F [RSS /feed/ (content-type rss+xml)](https://www.banksumut.co.id/feed/)
- F [REST /wp-json/wp/v2/jasa_barang (content-type json)](https://www.banksumut.co.id/wp-json/wp/v2/jasa_barang?per_page=5)
- S [Arsip jasa-barang](https://www.banksumut.co.id/archive-jasa-barang/) (tautan dari halaman detail)

bank bjb
- F [bankbjb.co.id](https://www.bankbjb.co.id/)
- F [eproc.bankbjb.co.id (tebakan, halaman tantangan)](https://eproc.bankbjb.co.id/)
- S [VOI: KPK dalami pengumpulan dana non-budgeter bjb](https://voi.id/en/news/597746)

Bank DKI / Bank Jakarta
- F [VOI 9 Agu 2026: bankjakarta.co.id](https://voi.id/en/economy/588894)
- F [bankjakarta.co.id (403)](https://www.bankjakarta.co.id/)
- F [bankdki.co.id (403)](https://www.bankdki.co.id/)
- F/S [Scribd: Vendor Management Bank DKI](https://www.scribd.com/document/775698019/Vendor-Management-Bank-DKI) (isi hanya dari cuplikan pencarian)

Bank Jateng
- F [bankjateng.co.id](https://www.bankjateng.co.id/)
- F [lelang.bankjateng.co.id (lelang agunan)](https://lelang.bankjateng.co.id/)

Bank Nagari, BPD Bali, Bankaltimtara, Bank Kalbar
- F [banknagari.co.id](https://www.banknagari.co.id/)
- S [Nagari Portal Lelang (andro.io)](https://bn-webview.andro.io/)
- F [bpdbali.co.id](https://www.bpdbali.co.id/)
- F [bankaltimtara.co.id](https://www.bankaltimtara.co.id/)
- S [ZoomInfo: staf Pengadaan Bankaltimtara](https://www.zoominfo.com/p/Rizky-Putra/17708517810)
- F [bankkalbar.co.id](https://www.bankkalbar.co.id/)

BPD lain
- S [e-tender.banksultra.co.id](https://e-tender.banksultra.co.id/)
- S [eproc.banksulteng.co.id](https://eproc.banksulteng.co.id/)

Portal agregat, BUMN, media
- F [TenderKita](https://tenderkita.com/)
- F [Tender Indonesia (beranda)](https://tender-indonesia.com/)
- S [Tender Indonesia – daftar proyek](https://tender-indonesia.com/tender_home/tender.php)
- S [Blog tentang Tender Indonesia](https://abouttenderindonesia.blogspot.com/)
- S [pengadaan.info](https://pengadaan.info/)
- S [IndoTender](http://indotender.com/)
- S [TenderTiger Indonesia](https://indonesia.tendertiger.com/)
- S [tenderinfo.org Indonesia](http://indonesia.tenderinfo.org/)
- S [IndonesiaTenders](https://www.indonesiatenders.com/)
- S [pyproc (GitHub)](https://github.com/wakataw/pyproc)
- S [Nusantara Procurement Data](https://nusantara-platform.site/)
- S [PaDi UMKM Seller (App Store)](https://apps.apple.com/it/app/padi-umkm-seller/id1588822356)
- S [Contoh pengumuman pengadaan Bank Indonesia](https://www.bi.go.id/id/layanan/lelang-jasa-barang/announcement/Pages/Pengadaan-Infrastruktur-Software-Microsoft-Azure-Local-untuk-Infra-Dev-Test-Bank-Indonesia-TA-2026.aspx)
- S [Biro iklan: Iklan Lelang Bisnis Indonesia](https://pusatpemasanganiklan.com/koran/1-bisnis-indonesia)

Vendor EDC
- S [linktr.ee resmi PVS](https://linktr.ee/primavistasolusi)
- S [Situs PVS](http://primavista-solusi.com/)
- S [Abstrak kerja praktik UPJ tentang PVS-WIDE](http://eprints.upj.ac.id/id/eprint/6216/3/abstract.pdf)
- S [Preqin: PT Mitra Transaksi Indonesia](https://www.preqin.com/data/profile/asset/pt-mitra-transaksi-indonesia/449977)
- S [Blog Ingenico APAC](https://ingenico.com/apac/newsroom/blogs/beyond-payments-why-modern-infrastructure-becoming-strategic-across-apac)
