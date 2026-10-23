"""Smoke run deterministik pengayaan detail (tanpa jaringan, tanpa webhook).

Menjalankan pipeline nyata (saring -> dedup -> enrich -> status -> kartu) atas
dua kandidat: pengumuman Smart EDC Bank Sumut (halaman detail menaut lampiran
PDF asli) dan market sounding Bank Jatim (lampiran Mei 2026, tanpa tanggal
tutup). Output pesan Google Chat dicetak sebagai JSON (dry-run); state ditulis
ke folder sementara, BUKAN ke state/ repo.

Pakai:
  python kerja/smoke/smoke_enrich.py --today 2026-10-23
  python kerja/smoke/smoke_enrich.py --today 2026-10-26
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tenderbot import gchat  # noqa: E402
from tenderbot.config import Keywords, load_keywords  # noqa: E402
from tenderbot.http_client import FetchResult  # noqa: E402
from tenderbot.models import Item  # noqa: E402
from tenderbot.pipeline import RunReport, process_candidates  # noqa: E402
from tenderbot.state import State  # noqa: E402

VENDOR_PDF = ROOT / "kerja" / "riset" / "vendor" / "lampiran-banksumut-smart-edc-005-2026.pdf"

SUMUT_DETAIL = "https://www.banksumut.co.id/jasa_barang/pekerjaan-pengadaan-sewa-beli-mesin-smart-electronic-data-capture-smart-edc-pt-bank-sumut-perseroda/"
SUMUT_PDF = "https://www.banksumut.co.id/files/pengumuman/2026/oktober/lampiran-smart-edc-005-2026.pdf"
JATIM_DETAIL = "https://www.bankjatim.co.id/id/informasi/lelang-pengadaan/market-sounding-pengadaan-penyedia-jasa-managed-service-perangkat-electronic-data-capture-edc-soundb"
JATIM_PDF = "https://www.bankjatim.co.id/files/pengumuman/2026/mei/market-sounding-managed-service-edc.pdf"


class SmokeFetcher:
    """Fetcher deterministik: HTML detail + byte PDF asli. Tanpa jaringan."""

    def __init__(self):
        self.calls: list[str] = []
        sumut_html = (
            f'<html><body><h1>Pengumuman Pelelangan Smart EDC Bank Sumut</h1>'
            f'<a href="{SUMUT_PDF}">Unduh lampiran pengumuman pelelangan (PDF)</a>'
            f'</body></html>'
        )
        # Market sounding: halaman detail tanpa tanggal tutup; lampiran Mei 2026
        # yang (di dunia nyata) kedaluwarsa. PDF di sini kosong -> tak ada field
        # tutup, jadi item jatuh ke status tidak_diketahui.
        jatim_html = (
            f'<html><body><h1>Market Sounding Managed Service EDC Soundbox</h1>'
            f'<p>Undangan market sounding penyedia jasa managed service.</p>'
            f'<a href="{JATIM_PDF}">Materi market sounding (PDF)</a>'
            f'</body></html>'
        )
        self._html = {SUMUT_DETAIL: sumut_html, JATIM_DETAIL: jatim_html}
        self._pdf = {SUMUT_PDF: VENDOR_PDF.read_bytes(), JATIM_PDF: b""}

    def fetch(self, url: str) -> FetchResult:
        self.calls.append(url)
        if url in self._pdf:
            return FetchResult(url=url, status=200, text="", content=self._pdf[url],
                               content_type="application/pdf")
        if url in self._html:
            html = self._html[url]
            return FetchResult(url=url, status=200, text=html,
                               content=html.encode("utf-8"), content_type="text/html")
        from tenderbot.http_client import AccessError
        raise AccessError("smoke: tidak ada rute")

    def allowed_by_robots(self, url: str) -> bool:
        return True


def _candidates() -> list[Item]:
    return [
        Item(
            bank="Bank Sumut",
            title="Pekerjaan Pengadaan Sewa Beli Mesin Smart Electronic Data Capture (Smart EDC) PT Bank Sumut (Perseroda)",
            url=SUMUT_DETAIL,
            source_type="portal",
            evidence="pengadaan sewa beli mesin smart edc",
        ),
        Item(
            bank="Bank Jatim",
            title="Market Sounding Pengadaan Penyedia Jasa Managed Service Perangkat Electronic Data Capture (EDC) Soundbox",
            url=JATIM_DETAIL,
            source_type="portal",
            evidence="managed service perangkat electronic data capture edc",
            attachment_url=JATIM_PDF,
        ),
    ]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", required=True)
    args = ap.parse_args(argv)
    today = date.fromisoformat(args.today)

    kw = load_keywords()
    fetcher = SmokeFetcher()
    with tempfile.TemporaryDirectory() as tmp:
        state = State.load(Path(tmp))  # state sementara; state/ repo tak disentuh
        report = RunReport(run_date=today.isoformat(), mode="light")
        process_candidates(_candidates(), kw, state, today, today.isoformat(),
                           report, fetcher=fetcher)

    print(f"=== SMOKE ENRICH --today {args.today} ===")
    print(f"kandidat: {report.candidates} | lolos saringan: {report.passed_filter} | "
          f"baru di laporan: {len(report.new_items)} "
          f"(berjalan {report.ongoing_count}, akan dibuka {report.upcoming_count})")
    print("--- dibuang ---")
    if report.dropped:
        for bank, title, reason in report.dropped:
            print(f"  [{bank}] {title[:70]} -> {reason}")
    else:
        print("  (tidak ada)")
    print("--- status item baru ---")
    for it in report.new_items:
        print(f"  [{it.bank}] status={it.status}")
    print("--- payload Google Chat (dry-run, TIDAK dikirim) ---")
    payload = gchat.build_message(report.new_items, report.candidates, report.failed)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
