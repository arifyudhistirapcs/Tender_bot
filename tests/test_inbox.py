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


def test_inbox_dengan_bom_diterima(tmp_path):
    """File inbox yang dibuat PowerShell diawali BOM UTF-8 (EF BB BF).
    Loader harus menerimanya (utf-8-sig), bukan menolaknya sebagai rusak."""
    data = {
        "run_date": "2026-10-26",
        "mode": "full",
        "items": [{"bank": "Bank Sumut", "title": "Tender EDC",
                   "url": "https://x.example/1"}],
    }
    p = tmp_path / "full-bom.json"
    # Tulis byte mentah DENGAN BOM di depan.
    raw = b"\xef\xbb\xbf" + json.dumps(data).encode("utf-8")
    p.write_bytes(raw)
    res = load_inbox(p)
    assert res.run_date == "2026-10-26"
    assert len(res.items) == 1
    assert res.items[0].bank == "Bank Sumut"


def test_inbox_tanpa_bom_tetap_diterima(tmp_path):
    """utf-8-sig juga membaca file TANPA BOM apa adanya."""
    data = {"run_date": "2026-10-26", "mode": "full",
            "items": [{"bank": "B", "title": "t", "url": "https://x.example/1"}]}
    p = tmp_path / "full-nobom.json"
    p.write_bytes(json.dumps(data).encode("utf-8"))  # tanpa BOM
    res = load_inbox(p)
    assert len(res.items) == 1


def test_json_rusak_tetap_ditolak(tmp_path):
    """JSON benar-benar rusak (meski ber-BOM) tetap memunculkan InboxError."""
    p = tmp_path / "rusak.json"
    p.write_bytes(b"\xef\xbb\xbf{ ini bukan json }")
    with pytest.raises(InboxError):
        load_inbox(p)
