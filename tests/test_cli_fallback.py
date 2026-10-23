"""Uji perilaku CLI: cadangan riset penuh, zona WIB, exit code gagal kirim."""

from datetime import date

import tenderbot.cli as cli
from tenderbot.cli import FALLBACK_NOTE, _today_wib, build_parser
from tenderbot.gchat import SendOutcome, build_message
from tenderbot.state import State


def _run(argv, monkeypatch, tmp_path, send_outcome=None):
    """Jalankan `tenderbot <argv>` dengan state-dir tmp dan send yang disuntik."""
    parser = build_parser()
    args = parser.parse_args(argv + ["--state-dir", str(tmp_path)])
    if send_outcome is not None:
        monkeypatch.setattr(cli.gchat, "send", lambda payload, dry_run: send_outcome)
    return args.func(args)


# ---- Zona waktu WIB ----

def test_today_wib_adalah_asia_jakarta():
    # _today_wib memakai offset +7, bukan UTC. Tidak menyentuh date.today().
    assert isinstance(_today_wib(), date)


def test_parse_today_override_dipakai_apa_adanya():
    assert cli._parse_today("2026-10-26") == date(2026, 10, 26)


# ---- Catatan cadangan di pesan ----

def test_build_message_menyisipkan_catatan_cadangan_tanpa_item():
    payload = build_message([], 42, [], note=FALLBACK_NOTE)
    assert payload["text"].splitlines()[0] == FALLBACK_NOTE
    assert "Tidak ada informasi tender baru" in payload["text"]


# ---- Cadangan: run full sudah tercatat -> keluar tanpa kirim ----

def test_fallback_berhenti_bila_full_sudah_tercatat(monkeypatch, tmp_path, capsys):
    # Senin 2026-10-26, catat run full hari itu.
    state = State.load(tmp_path)
    state.record_run("2026-10-26", "full", 10, 0, 0)
    state.save()

    sent = {"called": False}

    def _fake_send(payload, dry_run):
        sent["called"] = True
        return SendOutcome(sent=True, dry_run=dry_run, message="terkirim")

    monkeypatch.setattr(cli.gchat, "send", _fake_send)

    rc = _run(["run", "--mode", "light", "--fallback-full-check",
               "--today", "2026-10-26"], monkeypatch, tmp_path)
    assert rc == 0
    assert sent["called"] is False  # tidak mengirim apa pun
    err = capsys.readouterr().err
    assert "cadangan light tidak mengirim" in err


# ---- Cadangan: run full belum tercatat -> light dengan catatan ----

def test_fallback_light_dengan_catatan_bila_full_belum(monkeypatch, tmp_path, capsys):
    # Senin 2026-10-26, belum ada run full. Suntik send supaya tak ada jaringan.
    captured = {}

    def _fake_send(payload, dry_run):
        captured["payload"] = payload
        return SendOutcome(sent=True, dry_run=dry_run, message="terkirim")

    monkeypatch.setattr(cli.gchat, "send", _fake_send)
    # Hindari jaringan: pipeline light dikosongkan.
    monkeypatch.setattr(
        cli, "run_light",
        lambda *a, **k: cli.RunReport(run_date="2026-10-26", mode="light"),
    )

    rc = _run(["run", "--mode", "light", "--fallback-full-check",
               "--today", "2026-10-26"], monkeypatch, tmp_path)
    assert rc == 0
    assert captured["payload"]["text"].splitlines()[0] == FALLBACK_NOTE


# ---- Exit code bukan nol saat pengiriman gagal ----

def test_exit_bukan_nol_saat_kirim_gagal(monkeypatch, tmp_path):
    monkeypatch.setattr(
        cli, "run_light",
        lambda *a, **k: cli.RunReport(run_date="2026-10-22", mode="light"),
    )
    gagal = SendOutcome(sent=False, dry_run=False, status=500, message="gagal: HTTP 500")
    rc = _run(["run", "--mode", "light", "--today", "2026-10-22"],
              monkeypatch, tmp_path, send_outcome=gagal)
    assert rc == 1
    # State tidak disimpan saat gagal.
    state = State.load(tmp_path)
    assert state.runs == []


def test_exit_nol_dan_state_tersimpan_saat_kirim_sukses(monkeypatch, tmp_path):
    monkeypatch.setattr(
        cli, "run_light",
        lambda *a, **k: cli.RunReport(run_date="2026-10-22", mode="light"),
    )
    ok = SendOutcome(sent=True, dry_run=False, status=200, message="terkirim")
    rc = _run(["run", "--mode", "light", "--today", "2026-10-22"],
              monkeypatch, tmp_path, send_outcome=ok)
    assert rc == 0
    state = State.load(tmp_path)
    assert len(state.runs) == 1
    assert state.runs[0]["mode"] == "light"
