"""Uji kategori opsional dalam inbox mode full."""

import json
from datetime import date

from tenderbot.config import load_keywords
from tenderbot.filters import evaluate
from tenderbot.inbox import load_inbox


def _write(tmp_path, item):
    path = tmp_path / "full.json"
    path.write_text(json.dumps({"run_date": "2026-11-09", "mode": "full", "items": [item]}), encoding="utf-8")
    return path


def test_inbox_full_non_portal_alih_category_dinilai_ulang(tmp_path):
    result = load_inbox(_write(tmp_path, {
        "bank": "Bank Contoh",
        "title": "Pengadaan Jasa Khusus",
        "url": "https://example.test/1",
        "source_type": "berita",
        "category": "alih_data",
    }))

    item = result.items[0]
    assert item.category == "alih_data"
    assert not evaluate(item, load_keywords(), date(2026, 11, 9)).passed
    assert item.category is None


def test_inbox_full_category_tidak_sah_dihitung_ulang_dan_boleh_ditolak(tmp_path):
    result = load_inbox(_write(tmp_path, {
        "bank": "Bank Contoh",
        "title": "Pengadaan Lisensi Firewall Checkpoint",
        "url": "https://example.test/2",
        "category": "lainnya",
    }))

    item = result.items[0]
    assert item.category is None
    assert not evaluate(item, load_keywords(), date(2026, 11, 9)).passed