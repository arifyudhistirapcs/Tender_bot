# Tender Bot — Desain

Status: disetujui Arif 2026-10-23.

## Tujuan

Pada hari kerja, bot mencari info tender terbuka untuk pengadaan EDC dan managed service EDC di bank-bank besar Indonesia, lalu melaporkannya ke Space Google Chat perusahaan.

- Tender yang sudah pernah dilaporkan tidak dikirim lagi.
- Bila tidak ada yang baru, bot tetap mengirim pesan "tidak ada yang baru".

## Cakupan bank

BUMN (BRI, Mandiri, BNI, BTN, BSI), bank swasta KBMI 3–4 versi OJK, dan seluruh BPD. Daftar lengkap ada di `data/banks.yaml`. Isi awalnya diambil dari `kerja/riset/riset-eproc-bank-edc.md`.

Tiap bank punya `access`:

| access | arti | cara pantau |
|---|---|---|
| `public` | daftar tender terbuka tanpa login | baca langsung (RSS, HTML, PDF) |
| `vendor_login` | wajib akun vendor (BRI, BTN, SMBC) | berita + rilis pers; email undangan bila nanti ada akun |
| `not_found` | portal tidak ditemukan | berita + rilis pers + halaman pengumuman bank |
| `blocked` | situs menolak klien otomatis | berita saja; blokir tidak diakali |

Setiap run harus menyentuh SEMUA bank di daftar, minimal lewat pencarian berita. Laporan menyebut jumlah bank yang dicek dan bank yang gagal diakses beserta alasannya.

## Dua mode run

| Mode | Kapan (WIB) | Isi |
|---|---|---|
| `full` | Senin, Rabu & Jumat, mulai 06.30, laporan sebelum ±08.00 | riset agen AI KiroCrew (crew "Yang ngeriset") di laptop Arif yang menyala 24/7, dibagi tiga kelompok bank (BUMN / swasta / BPD), ditambah kolektor `light` |
| `light` | 08.00: Selasa, Kamis, Jumat. 17.00: Senin–Jumat | kolektor deterministik + saringan aturan (tanpa model AI) di GitHub Actions |

Hari libur nasional dilewati berdasarkan `data/holidays.yaml`, yang diperbarui tiap tahun.

### Mode `full`: KiroCrew → GitHub Actions

Model AI-nya adalah KiroCrew sendiri, jadi tidak perlu kunci API.

1. Cron KiroCrew (zona `Asia/Jakarta`, `30 6 * * 1,3,5`) mengecek hari libur, lalu menjalankan tiga agen riset paralel. Aturan agen:
   - utamakan web_search/web_fetch; untuk sumber `needs_js` pakai `playwright-cli` headed dengan sesi sendiri per agen (`-s=<nama>`) dan batas waktu keras 60 detik per perintah; tab Chrome milik Arif tidak disentuh;
   - riset berita hanya dari media kredibel (`credible_news_domains`), sumber lain diberi label belum terverifikasi;
   - membatasi jumlah panggilan per situs;
   - menulis hasil secara bertahap.

   Instruksi agen ada di `kiro/full-research-prompt.md`.
2. Hasil digabung ke satu file `inbox/full-YYYY-MM-DD.json`. Skemanya bisa dilihat di bagian berikutnya.
3. File itu di-push ke branch `inbox/full-YYYY-MM-DD` dengan `gh` yang sudah login di laptop. Setelah itu `gh workflow run tender-bot.yml -f mode=full -f inbox_ref=inbox/full-YYYY-MM-DD` dijalankan.
4. Actions melakukan beberapa langkah berurutan:
   - membaca file inbox;
   - menggabungkannya dengan hasil kolektor `light`;
   - membuang item duplikat;
   - mengirim laporan ke Google Chat;
   - meng-commit `state/`;
   - menghapus branch inbox.

   Laptop tidak memegang URL webhook.
5. Cadangan: run `light` pagi tetap dijadwalkan Senin, Rabu, dan Jumat pukul 07.40. Bila `state/runs.json` sudah mencatat run `full` untuk hari itu, run ini berhenti tanpa mengirim apa pun. Bila belum ada, run ini berjalan sebagai `light`, dan laporannya diberi catatan "riset penuh tidak berjalan hari ini".

Skema `inbox/full-*.json`:

```json
{
  "run_date": "2026-10-26",
  "mode": "full",
  "items": [
    {"bank": "Bank Sumut", "title": "...", "url": "https://...", "published": "2026-10-13",
     "deadline": null, "value_idr": 6993000000, "source_type": "portal|berita|rilis",
     "evidence": "kutipan singkat dari sumber"}
  ],
  "coverage": {
    "checked": ["BRI", "..."],
    "failed": [{"bank": "PermataBank", "reason": "HTTP 403"}]
  }
}
```

Setiap item wajib punya `url` sumber yang benar-benar dibuka. Field yang tidak diketahui diisi `null`, bukan ditebak.

### Jadwal GitHub Actions

Cron GitHub Actions memakai UTC, sedangkan semua jam di dokumen ini WIB (UTC+7). Jadwal Actions juga bisa terlambat 5–30 menit, jadi cron disetel sedikit lebih awal:

- light pagi: `40 0 * * 1-5` (07.40 WIB; Senin, Rabu & Jumat hanya sebagai cadangan)
- light sore: `40 9 * * 1-5` (16.40 WIB)
- full: lewat `workflow_dispatch` dari KiroCrew, tidak lewat cron Actions

Workflow memakai `concurrency: tender-bot` supaya dua run tidak menulis `state/` bersamaan.

## Alur satu run

1. **Kumpulkan** kandidat dari:
   - sumber `public` di `banks.yaml`, contohnya RSS dan arsip `jasa_barang` Bank Sumut, serta daftar Lelang Pengadaan Bank Jatim;
   - berita dari RSS resmi media di `credible_news_domains`, disaring dengan nama bank + kata EDC, ditambah GDELT DOC 2.0 API per bank. Google News RSS TIDAK dipakai karena robots.txt news.google.com melarang `/rss/search`;
   - sumber `needs_js` dilewati di mode `light` dan dicatat "dicek di mode full".

   Setiap request diberi timeout 20 detik dan retry satu kali. Robots.txt dipatuhi. Halaman blokir ("Request Rejected", Incapsula, HTTP 403) dicatat sebagai gagal akses.
2. **Saring.** Buang item yang memuat kata agunan/jaminan, EDC dalam arti lain (Export Development Canada dan sejenisnya), serta item yang lebih tua dari 90 hari. Item yang tersisa harus memenuhi dua syarat: memuat salah satu kata pengadaan (pengadaan, tender, lelang pengadaan, sewa, sewa beli, pemeliharaan, managed service, jasa layanan), dan memuat salah satu kata EDC (mesin EDC, Smart EDC, EDC Android, terminal EDC, Electronic Data Capture). Dari item itu diambil bank, judul, nilai, tanggal terbit, batas waktu, dan URL, sejauh tertulis di sumber. Pada mode `full`, penilaian ini sudah dilakukan oleh agen KiroCrew.
3. **Dedup.** `fingerprint = sha256(bank + judul dinormalisasi + url kanonik)`. Judul yang hampir sama dari bank yang sama dalam 60 hari dianggap item yang sama. Status tersimpan di `state/seen.json` dan di-commit oleh workflow.
4. **Laporkan** ke Google Chat lewat incoming webhook (secret `GCHAT_WEBHOOK_URL`):
   - Ada item baru: satu kartu per tender (bank, judul, nilai, terbit, batas waktu, link sumber).
   - Tidak ada item baru: "Tidak ada informasi tender baru. Dicek N bank; M tidak bisa diakses: …".
   - Run gagal: pesan error singkat. Fingerprint tidak ditandai terkirim, jadi item dicoba lagi di run berikutnya.
5. **Kesehatan sumber.** Sumber yang gagal 3 run berturut-turut diberi peringatan di laporan.

## Teknologi

- Python 3.12. Dependensi dikunci di `requirements.txt` dengan versi pasti.
- Workflow: `.github/workflows/tender-bot.yml` (cron + `workflow_dispatch` untuk uji manual).
- Secret: `GCHAT_WEBHOOK_URL` (sudah diset). Tidak ada kunci API model AI: mode `full` memakai KiroCrew.
- Sisi laptop: cron KiroCrew + `gh` (login sebagai arifyudhistirapcs).
- Repo ini publik. Karena itu tidak boleh ada secret di file, log, atau commit. Isi `state/seen.json` hanya data tender publik.

## Tahapan

1. `data/banks.yaml`, `keywords.yaml`, `holidays.yaml`.
2. Kolektor `public` dan berita, plus uji unit (fixture HTML/RSS lokal).
3. Penyaring, dedup, dan state.
4. Pengirim Google Chat. Mode `--dry-run` mencetak pesan ke log, bukan mengirim.
5. Workflow Actions dengan mode `light`. Uji `workflow_dispatch` dulu, kirim ke Space hanya setelah dry run benar.
6. Mode `full`: input `inbox_ref` di workflow, `kiro/full-research-prompt.md`, dan cron KiroCrew.
7. Uji coba 1 minggu, lalu evaluasi sumber yang sering gagal.
8. Pembaca email undangan tender di Gmail perusahaan (Gmail API, akses baca saja, butuh izin admin Google Workspace). Dikerjakan setelah perusahaan terdaftar sebagai vendor; daftar situs registrasi ada di field `vendor_registration_url` di `banks.yaml`.

## Keputusan (2026-10-23)

- Runner: GitHub Actions.
- Riset penuh: Senin, Rabu & Jumat pagi lewat KiroCrew. Slot lain memakai mode `light` tanpa AI.
- Cakupan: BUMN + KBMI 3–4 + seluruh BPD.
