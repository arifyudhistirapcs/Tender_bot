# Instruksi riset penuh Tender Bot (cron KiroCrew)

Dibaca oleh sesi cron KiroCrew setiap Senin, Rabu, dan Jumat pukul 06.30 WIB. Semua langkah dijalankan di laptop. Repo lokalnya `O:\Work\Tender Bot`.

Tujuannya: menemukan tender pengadaan EDC atau managed service EDC di bank Indonesia yang **masih berjalan atau akan segera dibuka**. Sesi ini HANYA meriset dan menulis tiga file hasil. Skrip cron tanpa AI `O:\Work\Kiro Crew\data\crons\tenderbot_full_submit.py` (job `a6182280`, 07.15 WIB) yang menggabung, memvalidasi, push branch inbox, dan memicu GitHub Actions. Actions yang mengirim ke Google Chat. Laptop tidak pernah memegang URL webhook.

## Aturan sesi cron

- Ini sesi cron tanpa pengguna. Kerjakan langkah 0, 1, dan 2 dalam SATU giliran sampai selesai. Giliran hanya boleh berakhir dengan `nothing_to_do` (sukses) atau `send_message(session="telegram")` (gagal). Jangan mengakhiri giliran dengan pesan "BERJALAN" atau menunggu completion event, karena sesi cron tidak menerima event susulan.
- Instruksi di file ini MENGGANTIKAN pelajaran umum yang bertentangan, misalnya larangan browser untuk riset banyak situs atau kewajiban mendelegasikan riset. Browser diizinkan untuk daftar bank di langkah 1, dan agen riset tidak boleh mendelegasikan lagi.
- Catat kemajuan. Setelah setiap langkah, tambahkan satu baris ke `O:\Work\Tender Bot\kerja\full\<TGL>\progress.log` berisi jam WIB, nomor langkah, dan hasil singkat. Tulis dengan Python (mode append, `encoding="utf-8"`). Berkas ini dipakai untuk melacak langkah mana yang berhenti.

## 0. Cek hari

- Hitung tanggal hari ini dalam WIB (`Asia/Jakarta`), format `YYYY-MM-DD`. Sebut nilainya `TGL`.
- Bila hari Sabtu/Minggu, atau `TGL` ada di `data/holidays.yaml`, berhenti di sini dengan `nothing_to_do`.
- Perbarui repo dengan dua perintah terpisah:
  - `git -C "O:\Work\Tender Bot" checkout main`
  - `git -C "O:\Work\Tender Bot" pull --ff-only origin main`

## 1. Riset: tiga agen paralel

Panggil `spawn_sub_agents` (blocking) dengan tiga agen `crew` "Yang ngeriset", satu per kelompok:

1. BUMN + swasta: BRI, Bank Mandiri, BNI, BTN, BSI, BCA, CIMB Niaga, Danamon, PermataBank, Maybank Indonesia, OCBC Indonesia, Panin Bank, Bank Mega, SMBC Indonesia, UOB Indonesia, Bank Sinarmas.
2. BPD Sumatra & Jawa: Bank Aceh, Bank Sumut, Bank Nagari, Bank Riau Kepri, Bank Jambi, Bank Sumsel Babel, Bank Bengkulu, Bank Lampung, bank bjb, Bank Jakarta, Bank Jateng, BPD DIY, Bank Jatim, Bank Banten.
3. BPD Bali–Papua: BPD Bali, Bank NTB Syariah, Bank NTT, Bank Kalbar, Bank Kalteng, Bank Kalsel, Bankaltimtara, Bank SulutGo, Bank Sulselbar, Bank Sultra, Bank Sulteng, Bank Maluku Malut, Bank Papua.

Di `coverage.checked`, `coverage.failed[].bank`, dan `items[].bank`, tulis nama bank PERSIS seperti daftar di atas (sama dengan field `name` di `banks.yaml`). Nama lain, misalnya "Panin" atau "Bank Aceh Syariah", membuat hitungan bank di laporan salah.

Teks tugas tiap agen wajib memuat semua aturan berikut.

**Kerja sendiri**
- Kamu agen riset terakhir. JANGAN memanggil `spawn_run`, `spawn_sub_agents`, atau bentuk delegasi lain, dan jangan membalas dengan pesan "BERJALAN".
- Tugas selesai hanya bila `part-<n>.json` sudah ditulis lengkap dan JSON-nya sah.
- Aturan ini menggantikan pelajaran umum yang menyuruh mendelegasikan riset.

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
- Bank berikut WAJIB dicoba dengan browser bila `web_fetch` tidak menampilkan daftar pengumuman. Izin ini menggantikan pelajaran umum yang melarang browser:
  - kelompok 2: bank bjb, Bank Jateng, Bank Lampung;
  - kelompok 3: Bank Kalbar, Bank Sulteng, Bank Papua.
  URL-nya ada di `banks.yaml` (`sources` atau `vendor_registration_url`). Maksimal 3 perintah browser per bank.
- JANGAN pakai `Start-Job`: terbukti macet 90 menit sampai 3 jam.
- Jangan sentuh tab Chrome milik Arif.
- Tutup sesi browser di akhir.

**Larangan**
- Jangan login, mendaftar akun, atau mengisi formulir.
- Jangan mengakali CAPTCHA, WAF, atau `robots.txt`.

**Batas kerja**
- Maksimal ~8 panggilan alat per bank.
- Minimal per bank, sebelum bank boleh masuk `coverage.checked`:
  - (a) buka halaman pengadaan/pengumuman resmi bila ada di `banks.yaml` atau `docs/registrasi-vendor.md`;
  - (b) satu pencarian web `"<nama lengkap bank>" tender OR pengadaan EDC` dibatasi 60 hari terakhir.
- Bank yang langkah (a)-nya gagal tetap boleh masuk `checked` bila (b) jalan. Alasan kegagalan (a) dicatat di `failed`.
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

## 2. Selesai

- Pastikan ketiga `O:\Work\Tender Bot\kerja\full\<TGL>\part-<n>.json` ada dan JSON-nya sah. Bila ada part yang belum ada setelah `spawn_sub_agents` kembali, jangan membuatnya sendiri dan jangan menunggu lama: skrip pukul 07.15 akan mencatat kelompok itu "agen riset gagal".
- JANGAN menggabung part, menulis `inbox/`, menjalankan git, push, atau `gh workflow run`. Semua itu tugas skrip `tenderbot_full_submit.py`. Bila sesi ini ikut push, GitHub bisa menerima dua kiriman untuk hari yang sama.
- Bila ketiga part ada: akhiri dengan `nothing_to_do`.
- Bila agen riset gagal atau part tidak ada: kirim satu `send_message(session="telegram")` ke Arif berisi kelompok yang gagal dan alasannya, lalu berhenti. Jangan sertakan URL webhook atau token.
- Pesan ini notifikasi teks biasa, BUKAN laporan. Jangan membuat PDF dan jangan mendelegasikan ke crew "yang-nulis". Aturan ini menggantikan aturan umum yang mewajibkan laporan PDF.
- Batas: gateway mematikan sesi ini sekitar 20 menit setelah agen riset pertama selesai. Jangan mengerjakan apa pun setelah ketiga part ada.
