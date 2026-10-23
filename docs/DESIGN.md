# Tender Bot — Desain

Status: draf disetujui Arif 2026-10-23. Bagian bertanda **[TERBUKA]** menunggu keputusan.

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
| `full` | Senin & Rabu, mulai 06.30, laporan sebelum ±08.00 | semua langkah `light` + agen AI riset dengan web search, per kelompok bank (BUMN / swasta / BPD), untuk menemukan sumber dan tender yang tidak tertangkap aturan |
| `light` | 08.00: Selasa, Kamis, Jumat. 17.00: Senin–Jumat | kolektor deterministik + pemeriksaan kandidat oleh model AI |

Hari libur nasional dilewati berdasarkan `data/holidays.yaml`, yang diperbarui tiap tahun.

GitHub Actions cron memakai UTC, sedangkan jadwal di atas WIB (UTC+7). Jadwal Actions juga bisa terlambat 5–30 menit, jadi cron disetel sedikit lebih awal:

- full: `30 23 * * 0,2` (Minggu & Selasa 23.30 UTC = Senin & Rabu 06.30 WIB)
- light pagi: `40 0 * * 2,4,5` (07.40 WIB)
- light sore: `40 9 * * 1-5` (16.40 WIB)

## Alur satu run

1. **Kumpulkan** kandidat dari:
   - sumber `public` di `banks.yaml`, contohnya RSS dan arsip `jasa_barang` Bank Sumut, serta daftar Lelang Pengadaan Bank Jatim;
   - pencarian berita per bank, memakai kata kunci di `data/keywords.yaml`.

   Setiap request diberi timeout 20 detik dan retry satu kali. Robots.txt dipatuhi. Halaman blokir ("Request Rejected", Incapsula, HTTP 403) dicatat sebagai gagal akses.
2. **Saring.** Buang item yang memuat kata agunan/jaminan, EDC dalam arti lain (Export Development Canada dan sejenisnya), serta item yang lebih tua dari 90 hari. Sisanya diperiksa model AI: apakah item ini pengadaan EDC/managed service oleh bank? Ekstrak bank, judul, nilai, tanggal terbit, batas waktu, dan URL.
3. **Dedup.** `fingerprint = sha256(bank + judul dinormalisasi + url kanonik)`. Judul yang hampir sama dari bank yang sama dalam 60 hari dianggap item yang sama. Status tersimpan di `state/seen.json` dan di-commit oleh workflow.
4. **Laporkan** ke Google Chat lewat incoming webhook (secret `GCHAT_WEBHOOK_URL`):
   - Ada item baru: satu kartu per tender (bank, judul, nilai, terbit, batas waktu, link sumber).
   - Tidak ada item baru: "Tidak ada informasi tender baru. Dicek N bank; M tidak bisa diakses: …".
   - Run gagal: pesan error singkat. Fingerprint tidak ditandai terkirim, jadi item dicoba lagi di run berikutnya.
5. **Kesehatan sumber.** Sumber yang gagal 3 run berturut-turut diberi peringatan di laporan.

## Teknologi

- Python 3.12. Dependensi dikunci di `requirements.txt` dengan versi pasti.
- Workflow: `.github/workflows/tender-bot.yml` (cron + `workflow_dispatch` untuk uji manual).
- Secret: `GCHAT_WEBHOOK_URL` (sudah diset). Kunci API model AI: **[TERBUKA]** provider dan nama secret.
- Repo ini publik. Karena itu tidak boleh ada secret di file, log, atau commit. Isi `state/seen.json` hanya data tender publik.

## Tahapan

1. `data/banks.yaml`, `keywords.yaml`, `holidays.yaml`.
2. Kolektor `public` dan berita, plus uji unit (fixture HTML/RSS lokal).
3. Penyaring, dedup, dan state.
4. Pengirim Google Chat. Mode `--dry-run` mencetak pesan ke log, bukan mengirim.
5. Workflow Actions dengan mode `light`. Uji `workflow_dispatch` dulu, kirim ke Space hanya setelah dry run benar.
6. Mode `full` (agen AI).
7. Uji coba 1 minggu, lalu evaluasi sumber yang sering gagal.

## Keputusan terbuka

- **[TERBUKA]** Provider model AI dan kuncinya. Kandidat: Gemini API (punya grounding Google Search), OpenAI, Anthropic.
