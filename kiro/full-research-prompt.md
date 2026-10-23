# Instruksi riset penuh Tender Bot (cron KiroCrew)

Dibaca oleh sesi cron KiroCrew setiap Senin, Rabu, dan Jumat pukul 06.30 WIB. Semua langkah dijalankan di laptop. Repo lokalnya `O:\Work\Tender Bot`.

Tujuannya: menemukan tender pengadaan EDC atau managed service EDC di bank Indonesia yang **masih berjalan atau akan segera dibuka**. Hasilnya diserahkan ke GitHub Actions, dan Actions yang mengirimnya ke Google Chat. Laptop tidak pernah memegang URL webhook.

## 0. Cek hari

- Hitung tanggal hari ini dalam WIB (`Asia/Jakarta`), format `YYYY-MM-DD`. Sebut nilainya `TGL`.
- Bila hari Sabtu/Minggu, atau `TGL` ada di `data/holidays.yaml`, berhenti di sini dengan `nothing_to_do`.
- Perbarui repo dengan dua perintah terpisah:
  - `git -C "O:\Work\Tender Bot" checkout main`
  - `git -C "O:\Work\Tender Bot" pull --ff-only origin main`

## 1. Riset: tiga agen paralel

Panggil `spawn_sub_agents` (blocking) dengan tiga agen `crew` "Yang ngeriset", satu per kelompok:

1. BUMN + swasta: BRI, Bank Mandiri, BNI, BTN, BSI, BCA, CIMB Niaga, Danamon, PermataBank, Maybank Indonesia, OCBC Indonesia, Panin, Bank Mega, SMBC Indonesia, UOB Indonesia.
2. BPD Sumatra & Jawa: Aceh Syariah, Sumut, Nagari, Riau Kepri Syariah, Jambi, Sumsel Babel, Bengkulu, Lampung, bjb, Bank Jakarta, Jateng, DIY, Jatim, Banten.
3. BPD Bali–Papua: BPD Bali, NTB Syariah, NTT, Kalbar, Kalteng, Kalsel, Bankaltimtara, SulutGo, Sulselbar, Sultra, Sulteng, Maluku Malut, Papua.

Teks tugas tiap agen wajib memuat semua aturan berikut.

**Bacaan awal**
- `C:\Users\arify\.claude\skills\deer-flow-research\SKILL.md`, diikuti secara ringkas.
- `O:\Work\Tender Bot\data\banks.yaml` dan `O:\Work\Tender Bot\docs\registrasi-vendor.md`, untuk tahu alamat portal tiap bank.

**Yang dicari**
- Tender, pelelangan, pengumuman pengadaan, market sounding, atau RFI/RFP untuk EDC: mesin EDC, Smart EDC, EDC Android, soundbox, sewa/sewa beli EDC, pemeliharaan, managed service, dan field service EDC. Hanya yang **berjalan atau akan dibuka** pada `TGL`.
- Lewati yang sudah tutup. Lewati juga yang tidak punya tanggal dan sudah diposting lebih dari 45 hari.

**Sumber**
1. Portal dan halaman pengumuman resmi bank.
2. Media kredibel: kompas.com, detik.com, cnbcindonesia.com, bisnis.com, kontan.co.id, katadata.co.id, tempo.co, antaranews.com, infobanknews.com, idxchannel.com, investor.id, cnnindonesia.com.

Sumber lain boleh dipakai, tetapi item dari sumber itu ditandai `"unverified_source": true`.

**Alat**
- Utamakan `web_search` dan `web_fetch`. Bila hasil fetch hanya menu, ulangi dengan mode full.
- Halaman yang dirender JavaScript boleh dibuka dengan `playwright-cli` HEADED, dengan sesi sendiri `-s=full-k<n>` di setiap perintah. Jalankan selalu lewat `Start-Process` dengan output dialihkan ke file dan `WaitForExit(60000)`. Bila waktunya habis, matikan HANYA proses milik sesi itu.
- JANGAN pakai `Start-Job`: terbukti macet 90 menit sampai 3 jam.
- Jangan sentuh tab Chrome milik Arif.
- Tutup sesi browser di akhir.

**Larangan**
- Jangan login, mendaftar akun, atau mengisi formulir.
- Jangan mengakali CAPTCHA, WAF, atau `robots.txt`.

**Batas kerja**
- Maksimal ~8 panggilan alat per bank.
- Total ~45 menit.

**Output**
- Tulis bertahap ke `O:\Work\Tender Bot\kerja\full\<TGL>\part-<n>.json`, dengan skema di bawah.
- Setiap item wajib punya `url` yang benar-benar dibuka.
- Field yang tidak diketahui diisi `null`. Jangan menebak.
- Jangan git commit.

Skema `part-<n>.json`, sama dengan `inbox` di `docs/DESIGN.md`:

```json
{
  "run_date": "TGL",
  "mode": "full",
  "items": [
    {"bank": "...", "title": "judul lengkap", "url": "https://...", "published": "YYYY-MM-DD|null",
     "deadline": "YYYY-MM-DD|null", "value_idr": 0, "source_type": "portal|berita|rilis",
     "evidence": "kutipan singkat dari sumber"}
  ],
  "coverage": {"checked": ["Bank ..."], "failed": [{"bank": "...", "reason": "..."}]}
}
```

## 2. Gabung dan validasi

1. Gabungkan ketiga part menjadi `O:\Work\Tender Bot\inbox\full-<TGL>.json`.
   - `items`: gabungan dari ketiga part, buang yang URL-nya sama.
   - `coverage.checked` dan `coverage.failed`: gabungan dari ketiga part.
   - Bila sebuah part tidak ada atau JSON-nya rusak, catat semua bank di kelompok itu ke `coverage.failed` dengan alasan "agen riset gagal".
2. Validasi dengan bot sendiri tanpa mengirim:
   `python -m tenderbot run --mode full --inbox "O:\Work\Tender Bot\inbox\full-<TGL>.json" --dry-run --today <TGL> --state-dir <folder sementara>`
   (`PYTHONPATH=O:\Work\Tender Bot\src`). Bila validasi gagal, perbaiki JSON-nya dan jalankan ulang.

## 3. Serahkan ke GitHub Actions

Jalankan setiap perintah git terpisah. Jangan gabungkan dengan `if` atau `{}`.

1. `git -C "O:\Work\Tender Bot" checkout -b inbox/full-<TGL> origin/main`
2. `git -C "O:\Work\Tender Bot" add inbox/full-<TGL>.json`
3. `git -C "O:\Work\Tender Bot" -c user.name=arifyudhistirapcs -c user.email=101551075+arifyudhistirapcs@users.noreply.github.com commit -m "inbox: riset penuh <TGL>"`
4. `git -C "O:\Work\Tender Bot" push origin inbox/full-<TGL>`
5. `git -C "O:\Work\Tender Bot" checkout main`
6. `& "C:\Program Files\GitHub CLI\gh.exe" workflow run tender-bot.yml --repo arifyudhistirapcs/Tender_bot --ref main -f mode=full -f inbox_ref=inbox/full-<TGL> -f dry_run=false`

Untuk uji, pakai `dry_run=true` dan jangan hapus branch inbox.

7. Pantau run sampai selesai: `gh run list --workflow tender-bot.yml --limit 1`, lalu `gh run watch <id> --exit-status`.

## 4. Lapor

- Bila sukses: `nothing_to_do`. Laporan sudah dikirim Actions ke Google Chat.
- Bila gagal di langkah mana pun: kirim `send_message(session="telegram")` ke Arif berisi langkah yang gagal dan pesan error singkat. Jangan sertakan URL webhook atau token.
- Bila sudah pukul 07.30 WIB dan langkah 3 belum selesai, hentikan dan laporkan. Run cadangan Actions pukul 07.40 akan mengambil alih.
