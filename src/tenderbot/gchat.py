"""Pengirim Google Chat: bangun pesan VERSI BISNIS, kirim lewat incoming webhook.

Keputusan Arif (2026-10-26): Space Google Chat dibaca tim bisnis non-teknis,
jadi pesannya SINGKAT dan UMUM. Semua detail teknis (sumber gagal, HTTP, GDELT,
robots, volume, metode, kontak, dll) pindah ke laporan detail Telegram
(lihat report.py), TIDAK masuk pesan Google Chat.

URL webhook dibaca dari env GCHAT_WEBHOOK_URL. Mode dry-run mencetak JSON
pesan ke stdout, tidak mengirim. Repo publik: URL webhook tidak pernah
masuk ke file maupun log.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

import requests

from .dates_id import format_rupiah
from .models import Item
from .status import STATUS_ONGOING, STATUS_UPCOMING

WEBHOOK_ENV = "GCHAT_WEBHOOK_URL"
SEND_TIMEOUT = 20

# Judul yang melebihi ambang ini ditaruh di widget teks sendiri (tidak dipotong),
# bukan di subtitle header kartu Google Chat yang akan terpangkas.
TITLE_SUBTITLE_MAX = 80


def _fmt_date(iso: Optional[str]) -> Optional[str]:
    """ISO "YYYY-MM-DD" -> "DD Mon YYYY" ringkas; None -> None."""
    if not iso:
        return None
    try:
        from datetime import date as _date
        d = _date.fromisoformat(iso[:10])
    except (ValueError, TypeError):
        return iso
    bulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
             "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    return f"{d.day} {bulan[d.month - 1]} {d.year}"


def _last_close_iso(item: Item) -> Optional[str]:
    """Tanggal tutup terakhir (reg_close / submit_close / deadline) sebagai ISO,
    untuk ditampilkan apa adanya di label status. None bila tak ada."""
    candidates = [item.submit_close, item.reg_close, item.deadline]
    isos = [c[:10] for c in candidates if c]
    return max(isos) if isos else None


def _status_label(item: Item) -> Optional[str]:
    """Label status versi bisnis, menyertakan tanggal bila ada.

    Contoh:
      - "Berjalan, tutup 23 Okt 2026"
      - "Akan dibuka 1 Nov 2026"
      - "Berjalan"
    None bila status tidak dikenal (tidak ditampilkan di kartu).
    """
    status = item.status
    if status == STATUS_ONGOING:
        close = _fmt_date(_last_close_iso(item))
        return f"Berjalan, tutup {close}" if close else "Berjalan"
    if status == STATUS_UPCOMING:
        opens = _fmt_date(item.reg_open)
        return f"Akan dibuka {opens}" if opens else "Akan dibuka"
    # tidak_diketahui / lainnya: tampilkan netral tanpa detail teknis.
    return "Berjalan"


def _item_card(item: Item) -> dict:
    """Satu kartu Google Chat per tender, VERSI BISNIS.

    Hanya memuat: Bank, Judul utuh, Status (dengan tanggal bila ada),
    Nilai/HPS bila ada, dan tombol (Lihat pengumuman / Lampiran / Daftar vendor)
    masing-masing HANYA bila URL-nya ada.

    TIDAK memuat: Volume, Durasi, Metode, Tempat, Kontak, Media, catatan teknis.
    Field None tidak ditampilkan sama sekali (tidak ada "tidak tertera").
    """
    widgets: list[dict] = []

    # Judul utuh bila panjang (subtitle header memotong di ~sekian karakter).
    long_title = len(item.title) > TITLE_SUBTITLE_MAX
    if long_title:
        widgets.append({"textParagraph": {"text": f"<b>{item.title}</b>"}})

    rows: list[tuple[str, Optional[str]]] = [
        ("Bank", item.bank),
        ("Status", _status_label(item)),
        ("Nilai/HPS", format_rupiah(item.value_idr)),
    ]
    for label, val in rows:
        if val is None or val == "":
            continue
        widgets.append({"decoratedText": {"topLabel": label, "text": val}})

    # Tombol: hanya bila URL-nya ada.
    buttons: list[dict] = []
    if item.url:
        buttons.append(
            {"text": "Lihat pengumuman", "onClick": {"openLink": {"url": item.url}}}
        )
    if item.attachment_url:
        buttons.append(
            {"text": "Lampiran", "onClick": {"openLink": {"url": item.attachment_url}}}
        )
    if item.vendor_registration_url:
        buttons.append(
            {"text": "Daftar vendor",
             "onClick": {"openLink": {"url": item.vendor_registration_url}}}
        )
    if buttons:
        widgets.append({"buttonList": {"buttons": buttons}})

    # Subtitle header: judul pendek utuh, atau nama bank bila judul sudah di widget.
    subtitle = item.title if not long_title else (item.bank or "Tender EDC")
    return {
        "cardId": item.fingerprint[:16] or "tender",
        "card": {
            "header": {"title": "Tender EDC", "subtitle": subtitle},
            "sections": [{"widgets": widgets}],
        },
    }


def _opening_text(new_items: list[Item]) -> str:
    """Pembuka versi bisnis: "Info tender EDC: N berjalan, M akan dibuka."."""
    ongoing = sum(1 for i in new_items if i.status == STATUS_ONGOING)
    upcoming = sum(1 for i in new_items if i.status == STATUS_UPCOMING)
    # Item berstatus lain (mis. tidak_diketahui yang lolos) dihitung sebagai
    # berjalan di label bisnis, supaya pembuka konsisten dengan kartu.
    other = len(new_items) - ongoing - upcoming
    ongoing += other
    return f"Info tender EDC: {ongoing} berjalan, {upcoming} akan dibuka."


def build_message(
    new_items: list[Item],
    checked_count: int,
    failed: Optional[list[tuple[str, str]]] = None,
    note: Optional[str] = None,
) -> dict:
    """Bangun payload Google Chat VERSI BISNIS.

    - Ada tender: pembuka ringkas + satu kartu per tender (bank, judul, status,
      nilai, tombol). Tidak ada daftar sumber gagal / HTTP / GDELT / catatan.
    - Tidak ada tender: satu kalimat memakai jumlah bank unik yang dipantau.

    Parameter `failed` dan `note` diterima untuk kompatibilitas pemanggil lama
    tetapi SENGAJA tidak ditampilkan di pesan bisnis (detail teknis ke Telegram).
    """
    if new_items:
        return {
            "text": _opening_text(new_items),
            "cardsV2": [_item_card(it) for it in new_items],
        }

    # Tidak ada tender: satu kalimat umum dengan jumlah bank dipantau.
    return {"text": f"Tidak ada info tender EDC baru. ({checked_count} bank dipantau)"}


@dataclass
class SendOutcome:
    sent: bool
    dry_run: bool
    status: Optional[int] = None
    message: str = ""


def send(
    payload: dict,
    dry_run: bool,
    webhook_url: Optional[str] = None,
) -> SendOutcome:
    """Kirim payload. Dry-run mencetak JSON dan tidak mengirim."""
    if dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return SendOutcome(sent=False, dry_run=True, message="dry-run: tidak dikirim")

    url = webhook_url or os.environ.get(WEBHOOK_ENV)
    if not url:
        raise RuntimeError(
            f"env {WEBHOOK_ENV} tidak diset; tidak bisa mengirim (pakai --dry-run)"
        )
    resp = requests.post(
        url,
        json=payload,
        timeout=SEND_TIMEOUT,
        headers={"Content-Type": "application/json; charset=UTF-8"},
    )
    return SendOutcome(
        sent=resp.ok,
        dry_run=False,
        status=resp.status_code,
        message="terkirim" if resp.ok else f"gagal: HTTP {resp.status_code}",
    )
