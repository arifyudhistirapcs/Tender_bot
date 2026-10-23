# Tender Bot

Bot pemantau tender EDC bank Indonesia. Pada hari kerja, bot mencari info tender
terbuka untuk pengadaan dan managed service EDC di bank-bank besar (BUMN, swasta
KBMI 3-4, dan seluruh BPD), lalu melaporkannya ke Space Google Chat perusahaan.

- Tender yang sudah pernah dilaporkan tidak dikirim lagi (dedup).
- Bila tidak ada yang baru, bot tetap mengirim pesan "tidak ada yang baru".
- Repo ini publik: tidak ada secret di kode. URL webhook ada di secret repo
  `GCHAT_WEBHOOK_URL`, dan hanya dibaca saat run di GitHub Actions.

Desain lengkap ada di [docs/DESIGN.md](docs/DESIGN.md).

## Jadwal

Jadwal di GitHub Actions memakai UTC; jam di bawah ditulis WIB (UTC+7). Cron
disetel sedikit lebih awal karena Actions bisa terlambat 5-30 menit.

| Slot | Cron (UTC) | WIB | Mode |
|---|---|---|---|
| Pagi | `40 0 * * 1-5` | 07.40 Sen-Jum | light (Senin & Rabu sebagai cadangan riset penuh) |
| Sore | `40 9 * * 1-5` | 16.40 Sen-Jum | light |
| Riset penuh | `workflow_dispatch` dari KiroCrew | Senin & Rabu pagi | full |

Akhir pekan dan hari libur nasional (`data/holidays.yaml`) dilewati.

Mode `full` memakai hasil riset agen AI KiroCrew yang dikirim lewat file inbox
(`inbox/full-YYYY-MM-DD.json`) ke branch, lalu dipicu dengan `workflow_dispatch`.
Bila riset penuh tidak berjalan, run light cadangan pagi Senin/Rabu mengambil
alih dan laporannya diberi catatan "riset penuh tidak berjalan hari ini".

## Menjalankan dry-run manual

Dry-run mencetak pesan ke log tanpa mengirim ke Google Chat dan tanpa menyimpan
state:

```bash
gh workflow run tender-bot.yml -f mode=light -f dry_run=true
```

Secara lokal (butuh Python 3.12):

```bash
pip install -r requirements.txt
python -m tenderbot run --mode light --dry-run
```

Opsi uji berguna:

- `--today YYYY-MM-DD` memaksa tanggal (dihitung WIB bila tidak diisi).
- `--fallback-full-check` mengaktifkan logika cadangan Senin/Rabu.
- `--state-dir PATH` memakai folder state lain (uji).

Mode full lokal butuh file inbox:

```bash
python -m tenderbot run --mode full --inbox path/ke/full-2026-10-26.json --dry-run
```

## Data dan state

- `data/` — konfigurasi: `banks.yaml`, `keywords.yaml`, `holidays.yaml`,
  `news_feeds.yaml`.
- `state/` — status tersimpan yang di-commit oleh workflow:
  `seen.json` (fingerprint tender yang sudah dilaporkan), `runs.json` (riwayat
  run), `source_health.json` (kesehatan sumber). Hanya berisi data tender publik.

Kode ada di `src/tenderbot/`, uji di `tests/` (jalankan `python -m pytest -q`).
