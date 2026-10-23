"""Uji loader inbox mode full: validasi skema, item tanpa url ditolak."""

import json

import pytest

from tenderbot.inbox import InboxError, load_inbox


def _write(tmp_path, data):
    p = tmp_path / "full-2026-10-26.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_item_tanpa_url_ditolak(tmp_path):
    data = {
        "run_date": "2026-10-26",
        "mode": "full",
        "items": [
            {"bank": "Bank Sumut", "title": "Tender Smart EDC",
             "url": "https://x.example/1", "published": "2026-10-13"},
            {"bank": "Bank X", "title": "Tanpa url"},  # ditolak
        ],
    }
    res = load_inbox(_write(tmp_path, data))
    assert len(res.items) == 1
    assert len(res.rejected) == 1
    assert "tanpa url" in res.rejected[0]


def test_item_tanpa_bank_ditolak(tmp_path):
    data = {"run_date": "2026-10-26", "items": [
        {"title": "x", "url": "https://x.example/1"}]}
    res = load_inbox(_write(tmp_path, data))
    assert not res.items
    assert "tanpa bank" in res.rejected[0]


def test_run_date_wajib(tmp_path):
    p = _write(tmp_path, {"mode": "full", "items": []})
    with pytest.raises(InboxError):
        load_inbox(p)


def test_items_harus_daftar(tmp_path):
    p = _write(tmp_path, {"run_date": "2026-10-26", "items": {}})
    with pytest.raises(InboxError):
        load_inbox(p)


def test_file_tidak_ada(tmp_path):
    with pytest.raises(InboxError):
        load_inbox(tmp_path / "hilang.json")


def test_coverage_terbaca(tmp_path):
    data = {
        "run_date": "2026-10-26",
        "items": [{"bank": "B", "title": "t", "url": "https://x.example/1"}],
        "coverage": {"checked": ["BRI", "BNI"],
                     "failed": [{"bank": "PermataBank", "reason": "HTTP 403"}]},
    }
    res = load_inbox(_write(tmp_path, data))
    assert res.coverage_checked == ["BRI", "BNI"]
    assert res.coverage_failed[0]["reason"] == "HTTP 403"
