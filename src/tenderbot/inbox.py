"""Loader inbox mode full: baca inbox/full-YYYY-MM-DD.json, validasi skema.

Item tanpa url DITOLAK (sesuai DESIGN: "item tanpa url ditolak"). Validasi
mengembalikan item yang sah plus daftar alasan penolakan, bukan diam-diam
membuang, supaya koordinator bisa melihat apa yang ditolak.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .models import Item


class InboxError(Exception):
    """Inbox tidak sah secara struktur (bukan sekadar satu item buruk)."""


@dataclass
class InboxLoadResult:
    run_date: str
    mode: str
    items: list[Item] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)  # alasan per item ditolak
    coverage_checked: list[str] = field(default_factory=list)
    coverage_failed: list[dict] = field(default_factory=list)


def load_inbox(path: Path) -> InboxLoadResult:
    path = Path(path)
    if not path.exists():
        raise InboxError(f"file inbox tidak ditemukan: {path.name}")
    try:
        # utf-8-sig menerima file DENGAN atau TANPA BOM: file inbox sering
        # dibuat lewat PowerShell yang mengawali dengan BOM UTF-8 (EF BB BF).
        # JSON yang benar-benar rusak tetap memunculkan InboxError di bawah.
        with path.open("r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InboxError(f"JSON tidak valid: {exc}") from exc

    if not isinstance(data, dict):
        raise InboxError("akar inbox harus objek JSON")

    run_date = data.get("run_date")
    if not run_date:
        raise InboxError("field 'run_date' wajib ada")
    mode = data.get("mode", "full")

    raw_items = data.get("items")
    if not isinstance(raw_items, list):
        raise InboxError("field 'items' harus berupa daftar")

    result = InboxLoadResult(run_date=str(run_date), mode=str(mode))

    for idx, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            result.rejected.append(f"item #{idx}: bukan objek")
            continue
        url = raw.get("url")
        if not url or not str(url).strip():
            title = raw.get("title", "(tanpa judul)")
            result.rejected.append(f"item #{idx} ({title}): tanpa url, ditolak")
            continue
        bank = raw.get("bank")
        if not bank or not str(bank).strip():
            result.rejected.append(f"item #{idx} ({url}): tanpa bank, ditolak")
            continue
        value = raw.get("value_idr")
        if value is not None:
            try:
                value = int(value)
            except (TypeError, ValueError):
                value = None
        result.items.append(
            Item(
                bank=str(bank),
                title=str(raw.get("title", "")),
                url=str(url),
                published=raw.get("published"),
                deadline=raw.get("deadline"),
                value_idr=value,
                source_type=str(raw.get("source_type", "berita")),
                evidence=str(raw.get("evidence", "")),
            )
        )

    coverage = data.get("coverage") or {}
    if isinstance(coverage, dict):
        result.coverage_checked = list(coverage.get("checked") or [])
        result.coverage_failed = list(coverage.get("failed") or [])

    return result
