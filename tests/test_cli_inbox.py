"""Uji perilaku CLI untuk inbox mode full: BOM, JSON rusak, items kosong.

Regression untuk bug "inbox ber-BOM ditolak tapi job tetap hijau":
  - inbox ber-BOM diterima (run sukses, exit 0);
  - inbox JSON rusak / tidak ada -> exit BUKAN nol, state TIDAK disimpan;
  - inbox items kosong -> pesan "Tidak ada informasi tender baru" dengan bank
    gagal dari coverage.failed inbox tercantum beserta alasannya.

Jaringan dimatikan: collect_light di-stub mengembalikan [] dan gchat.send
di-stub (dry-run juga tidak menyentuh webhook).
"""

import json

import pytest

import tenderbot.cli as cli
import tenderbot.pipeline as pipeline
from tenderbot.gchat import SendOutcome, build_message
from tenderbot.state import State


def _run(argv, monkeypatch, tmp_path, send_outcome=None):
    parser = cli.build_parser()
    args = parser.parse_args(argv + ["--state-dir", str(tmp_path / "state")])
    if send_outcome is not None:
        monkeypatch.setattr(cli.gchat, "send", lambda payload, dry_run: send_outcome)
    return args.func(args)


def _no_network(monkeypatch):
    """Matikan kolektor publik + berita supaya run_full deterministik."""
    monkeypatch.setattr(pipeline, "collect_light", lambda *a, **k: [])


def _write_bytes(tmp_path, name, raw):
    p = tmp_path / name
    p.write_bytes(raw)
    return p


# ---- inbox ber-BOM diterima: run sukses, exit 0 ----

def test_inbox_bom_diterima_exit_nol(monkeypatch, tmp_path, capsys):
    _no_network(monkeypatch)
    data = {
        "run_date": "2026-10-23",
        "mode": "full",
        "items": [],
        "coverage": {
            "checked": ["BRI", "BNI", "BTN"],
            "failed": [{"bank": "BRI", "reason": "portal diblokir WAF"}],
        },
    }
    raw = b"\xef\xbb\xbf" + json.dumps(data).encode("utf-8")
    inbox = _write_bytes(tmp_path, "full-2026-10-23.json", raw)

    ok = SendOutcome(sent=False, dry_run=True, message="dry-run: tidak dikirim")
    rc = _run(["run", "--mode", "full", "--inbox", str(inbox), "--dry-run",
               "--today", "2026-10-23"], monkeypatch, tmp_path, send_outcome=ok)
    assert rc == 0
    out = capsys.readouterr()
    # Tidak ada "inbox tidak sah" di stderr -> BOM diterima.
    assert "inbox tidak sah" not in out.err


# ---- JSON rusak -> exit bukan nol, state tidak disimpan ----

def test_inbox_json_rusak_exit_bukan_nol(monkeypatch, tmp_path, capsys):
    _no_network(monkeypatch)
    inbox = _write_bytes(tmp_path, "rusak.json", b"\xef\xbb\xbf{ bukan json }")
    rc = _run(["run", "--mode", "full", "--inbox", str(inbox), "--dry-run",
               "--today", "2026-10-23"], monkeypatch, tmp_path)
    assert rc != 0
    err = capsys.readouterr().err
    assert "inbox tidak sah" in err
    # State tidak disimpan (folder state belum punya runs terisi).
    state = State.load(tmp_path / "state")
    assert state.runs == []


def test_inbox_tidak_ada_exit_bukan_nol(monkeypatch, tmp_path):
    _no_network(monkeypatch)
    rc = _run(["run", "--mode", "full", "--inbox",
               str(tmp_path / "hilang.json"), "--dry-run",
               "--today", "2026-10-23"], monkeypatch, tmp_path)
    assert rc != 0


# ---- items kosong -> "Tidak ada informasi tender baru" + bank gagal inbox ----

def test_inbox_items_kosong_pesan_dan_bank_gagal(monkeypatch, tmp_path):
    _no_network(monkeypatch)
    long_reason = (
        "portal eproc.bri.co.id diblokir WAF Incapsula (Request unsuccessful) "
        "untuk alat otomatis; tidak diakali. Dicek lewat berita dan tidak ada "
        "pengumuman tender EDC dalam 60 hari terakhir sama sekali di mana pun."
    )
    data = {
        "run_date": "2026-10-23",
        "mode": "full",
        "items": [],
        "coverage": {
            "checked": ["BRI", "BNI", "BTN", "BSI"],
            "failed": [
                {"bank": "BRI", "reason": long_reason},
                {"bank": "BNI", "reason": "portal HTTP 503"},
            ],
        },
    }
    inbox = _write_bytes(tmp_path, "full-2026-10-23.json",
                         json.dumps(data).encode("utf-8"))

    captured = {}

    def _fake_send(payload, dry_run):
        captured["payload"] = payload
        return SendOutcome(sent=False, dry_run=True, message="dry-run")

    monkeypatch.setattr(cli.gchat, "send", _fake_send)

    report_dir = tmp_path / "report"
    rc = _run(["run", "--mode", "full", "--inbox", str(inbox), "--dry-run",
               "--today", "2026-10-23", "--report-out", str(report_dir)],
              monkeypatch, tmp_path)
    assert rc == 0
    # Pesan Google Chat: VERSI BISNIS, satu kalimat, TANPA detail teknis.
    text = captured["payload"]["text"]
    assert text.startswith("Tidak ada info tender EDC baru.")
    for larang in ("BRI", "BNI", "HTTP 503", "WAF", "Incapsula"):
        assert larang not in text, f"detail teknis '{larang}' bocor ke pesan bisnis"
    # Detail bank gagal pindah ke laporan Telegram (report.md).
    md = (report_dir / "report.md").read_text(encoding="utf-8")
    assert "BRI" in md
    assert "BNI" in md
    assert "HTTP 503" in md
    # Alasan panjang dipotong (~120 char) di report.json failures.
    j = json.loads((report_dir / "report.json").read_text(encoding="utf-8"))
    bri_fail = next(f for f in j["failures"] if f["source"] == "BRI")
    assert long_reason not in bri_fail["reason"]
    assert bri_fail["reason"].endswith("...")


def test_build_message_kosong_adalah_pesan_bisnis_singkat():
    """build_message tanpa item: satu kalimat bisnis, TANPA daftar bank gagal."""
    payload = build_message(
        [], 41, [("BRI", "portal diblokir"), ("BNI", "HTTP 503")]
    )
    text = payload["text"]
    assert text == "Tidak ada info tender EDC baru. (41 bank dipantau)"
    assert "BRI" not in text and "BNI" not in text
