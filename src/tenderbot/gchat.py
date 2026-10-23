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

from .models import Item

WEBHOOK_ENV = "GCHAT_WEBHOOK_URL"
SEND_TIMEOUT = 20


def _format_idr(value: Optional[int]) -> str:
    if value is None:
        return "tidak tertera"
    return "Rp" + f"{value:,}".replace(",", ".")


def _item_card(item: Item) -> dict:
    """Satu kartu Google Chat per tender."""
    rows = [
        ("Bank", item.bank),
        ("Nilai", _format_idr(item.value_idr)),
        ("Terbit", item.published or "tidak tertera"),
        ("Batas waktu", item.deadline or "tidak tertera"),
    ]
    widgets = [
        {"decoratedText": {"topLabel": label, "text": val}} for label, val in rows
    ]
    widgets.append(
        {
            "buttonList": {
                "buttons": [
                    {
                        "text": "Buka sumber",
                        "onClick": {"openLink": {"url": item.url}},
                    }
                ]
            }
        }
    )
    return {
        "cardId": item.fingerprint[:16] or "tender",
        "card": {
            "header": {"title": "Tender EDC", "subtitle": item.title[:120]},
            "sections": [{"widgets": widgets}],
        },
    }


def build_message(
    new_items: list[Item],
    checked_count: int,
    failed: list[tuple[str, str]],
) -> dict:
    """Bangun payload Google Chat.

    failed: daftar (nama_bank_atau_sumber, alasan).
    """
    if new_items:
        text = f"Ada {len(new_items)} info tender EDC baru."
        return {
            "text": text,
            "cardsV2": [_item_card(it) for it in new_items],
        }

    # Tidak ada yang baru: wajib memuat jumlah bank dicek + daftar gagal.
    lines = [
        "Tidak ada informasi tender baru.",
        f"Dicek {checked_count} bank.",
    ]
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
