"""Pengirim Google Chat: bangun pesan, kirim lewat incoming webhook.

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

WEBHOOK_ENV = "GCHAT_WEBHOOK_URL"
SEND_TIMEOUT = 20

# Judul yang melebihi ambang ini ditaruh di widget teks sendiri (tidak dipotong),
# bukan di subtitle header kartu Google Chat yang akan terpangkas.
TITLE_SUBTITLE_MAX = 80

_STATUS_LABEL = {
    "akan_dibuka": "Akan dibuka",
    "berjalan": "Berjalan",
    "tutup": "Tutup",
    "tidak_diketahui": "Tanggal belum pasti",
}


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


def _registration_line(item: Item) -> Optional[str]:
    """Baris pendaftaran "buka - tutup" dari reg_open/reg_close; None bila kosong."""
    o = _fmt_date(item.reg_open)
    c = _fmt_date(item.reg_close)
    if o and c:
        return f"{o} - {c}"
    if o:
        return f"mulai {o}"
    if c:
        return f"sampai {c}"
    return None


def _item_card(item: Item) -> dict:
    """Satu kartu Google Chat per tender.

    Field None TIDAK ditampilkan sama sekali (tidak ada "tidak tertera").
    Judul utuh: bila panjang, taruh di widget teks sendiri agar tidak terpotong.
    """
    widgets: list[dict] = []

    # Judul utuh bila panjang (subtitle header memotong di ~sekian karakter).
    long_title = len(item.title) > TITLE_SUBTITLE_MAX
    if long_title:
        widgets.append({"textParagraph": {"text": f"<b>{item.title}</b>"}})

    status_label = _STATUS_LABEL.get(item.status or "", None)

    # Pasangan (label, nilai) hanya untuk nilai yang tidak None/kosong.
    rows: list[tuple[str, Optional[str]]] = [
        ("Bank", item.bank),
        ("Status", status_label),
        ("Tanggal posting", _fmt_date(item.posted)),
        ("Pendaftaran", _registration_line(item)),
        ("Batas penawaran", _fmt_date(item.submit_close)),
        ("Nilai/HPS", format_rupiah(item.value_idr)),
        ("Volume", item.volume),
        ("Durasi", item.duration),
        ("Metode", item.method),
        ("Tempat daftar", item.reg_place),
        ("Kontak", item.contact),
    ]
    # Untuk item berita, tampilkan nama media dan tandai bila tidak kredibel.
    if item.source_type == "berita" or item.media_name:
        media = item.media_name or "sumber tidak dikenal"
        if item.unverified_source:
            media += "  [unverified_source]"
        rows.append(("Media", media))

    # Catatan cara daftar vendor (bila ada).
    if item.vendor_registration_note:
        rows.append(("Daftar vendor", item.vendor_registration_note))

    for label, val in rows:
        if val is None or val == "":
            continue
        widgets.append({"decoratedText": {"topLabel": label, "text": val}})

    buttons = [
        {"text": "Buka sumber", "onClick": {"openLink": {"url": item.url}}}
    ]
    if item.attachment_url:
        buttons.append(
            {"text": "Lampiran", "onClick": {"openLink": {"url": item.attachment_url}}}
        )
    if item.vendor_registration_url:
        buttons.append(
            {"text": "Daftar vendor",
             "onClick": {"openLink": {"url": item.vendor_registration_url}}}
        )
    widgets.append({"buttonList": {"buttons": buttons}})

    # Subtitle header: judul pendek utuh, atau ringkas bila sudah di widget teks.
    subtitle = item.title if not long_title else (item.bank or "Tender EDC")
    return {
        "cardId": item.fingerprint[:16] or "tender",
        "card": {
            "header": {"title": "Tender EDC", "subtitle": subtitle},
            "sections": [{"widgets": widgets}],
        },
    }


def _opening_text(new_items: list[Item]) -> str:
    """Kalimat pembuka menyebut jumlah berjalan dan jumlah akan dibuka."""
    ongoing = sum(1 for i in new_items if i.status == "berjalan")
    upcoming = sum(1 for i in new_items if i.status == "akan_dibuka")
    other = len(new_items) - ongoing - upcoming
    parts = [f"{ongoing} tender berjalan", f"{upcoming} akan dibuka"]
    if other:
        parts.append(f"{other} lainnya")
    return "Info tender EDC: " + ", ".join(parts) + "."


def build_message(
    new_items: list[Item],
    checked_count: int,
    failed: list[tuple[str, str]],
    note: Optional[str] = None,
) -> dict:
    """Bangun payload Google Chat.

    failed: daftar (nama_bank_atau_sumber, alasan).
    note: catatan tambahan (mis. cadangan "riset penuh tidak berjalan hari ini")
          yang disisipkan di baris pertama pesan.
    """
    if new_items:
        text = _opening_text(new_items)
        if note:
            text = f"{note}\n{text}"
        return {
            "text": text,
            "cardsV2": [_item_card(it) for it in new_items],
        }

    # Tidak ada yang baru: wajib memuat jumlah bank dicek + daftar gagal.
    lines = []
    if note:
        lines.append(note)
    lines.extend([
        "Tidak ada informasi tender baru.",
        f"Dicek {checked_count} bank.",
    ])
    if failed:
        lines.append(f"{len(failed)} tidak bisa diakses:")
        for name, reason in failed:
            lines.append(f"- {name}: {reason}")
    else:
        lines.append("Semua sumber bisa diakses.")
    return {"text": "\n".join(lines)}


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
