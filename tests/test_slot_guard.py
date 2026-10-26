"""Uji penjaga slot (--once-per-slot) dan penulisan laporan di jalur dilewati.

Slot: pagi (<12.00 WIB) / sore (>=12.00 WIB). Bila state sudah mencatat run
NON-dry-run di tanggal + slot yang sama, run keluar 0 tanpa kirim dengan
skipped="slot sudah terisi". Dry-run tidak pernah menandai slot.
"""

import json

import tenderbot.cli as cli
from tenderbot.gchat import SendOutcome
from tenderbot.state import State


def _run(argv, monkeypatch, state_dir, hour_wib, send_outcome=None):
    monkeypatch.setattr(cli, "_now_hour_wib", lambda: hour_wib)
    # Hindari jaringan: pipeline light dikosongkan.
    monkeypatch.setattr(
        cli, "run_light",
        lambda *a, **k: cli.RunReport(run_date="2026-10-26", mode="light"),
    )
    if send_outcome is not None:
        if callable(send_outcome):
            monkeypatch.setattr(cli.gchat, "send", send_outcome)
        else:
            monkeypatch.setattr(cli.gchat, "send",
                                lambda payload, dry_run: send_outcome)
    parser = cli.build_parser()
    args = parser.parse_args(argv + ["--state-dir", str(state_dir)])
    return args.func(args)


def test_slot_terisi_keluar_tanpa_kirim(monkeypatch, tmp_path, capsys):
    state_dir = tmp_path / "state"
    # Catat run light pagi (jam 7) 2026-10-26.
    st = State.load(state_dir)
    st.record_run("2026-10-26", "light", 43, 0, 0, hour_wib=7)
    st.save()

    sent = {"called": False}

    def _send(payload, dry_run):
        sent["called"] = True
        return SendOutcome(sent=True, dry_run=dry_run, message="terkirim")

    report_dir = tmp_path / "report"
    # Run lagi di slot pagi (jam 8) hari yang sama -> harus berhenti tanpa kirim.
    rc = _run(["run", "--mode", "light", "--once-per-slot",
               "--today", "2026-10-26", "--report-out", str(report_dir)],
              monkeypatch, state_dir, hour_wib=8, send_outcome=_send)
    assert rc == 0
    assert sent["called"] is False
    err = capsys.readouterr().err
    assert "slot pagi sudah terisi" in err
    # Laporan tetap ditulis dengan skipped="slot sudah terisi".
    j = json.loads((report_dir / "report.json").read_text(encoding="utf-8"))
    assert j["skipped"] == "slot sudah terisi"


def test_slot_sore_berbeda_dari_pagi(monkeypatch, tmp_path):
    state_dir = tmp_path / "state"
    # Run pagi tercatat; run sore (jam 17) di hari yang sama TETAP boleh kirim.
    st = State.load(state_dir)
    st.record_run("2026-10-26", "light", 43, 0, 0, hour_wib=7)
    st.save()

    ok = SendOutcome(sent=True, dry_run=False, status=200, message="terkirim")
    rc = _run(["run", "--mode", "light", "--once-per-slot",
               "--today", "2026-10-26"],
              monkeypatch, state_dir, hour_wib=17, send_outcome=ok)
    assert rc == 0
    # Slot sore tercatat terpisah.
    st2 = State.load(state_dir)
    slots = sorted(r.get("slot") for r in st2.runs)
    assert slots == ["pagi", "sore"]


def test_dry_run_tidak_mengisi_slot(monkeypatch, tmp_path):
    state_dir = tmp_path / "state"
    dry = SendOutcome(sent=False, dry_run=True, message="dry-run")
    # Dua kali dry-run slot pagi: keduanya jalan (tidak pernah mengisi slot).
    for _ in range(2):
        rc = _run(["run", "--mode", "light", "--once-per-slot", "--dry-run",
                   "--today", "2026-10-26"],
                  monkeypatch, state_dir, hour_wib=8, send_outcome=dry)
        assert rc == 0
    st = State.load(state_dir)
    assert st.runs == []  # dry-run tidak menyimpan run


def _run_slot_with_legacy(monkeypatch, tmp_path, legacy_mode, hour):
    state_dir = tmp_path / "state"
    # Entri lama TANPA hour_wib/slot.
    st = State.load(state_dir)
    st.runs.append({"date": "2026-10-26", "mode": legacy_mode, "checked": 43,
                    "failed": 0, "new_items": 0, "status": "ok"})
    st.save()

    sent = {"called": False}

    def _send(payload, dry_run):
        sent["called"] = True
        return SendOutcome(sent=True, dry_run=dry_run, message="terkirim")

    monkeypatch.setattr(cli.gchat, "send", _send)
    monkeypatch.setattr(cli, "_now_hour_wib", lambda: hour)
    monkeypatch.setattr(
        cli, "run_light",
        lambda *a, **k: cli.RunReport(run_date="2026-10-26", mode="light"),
    )
    parser = cli.build_parser()
    args = parser.parse_args(["run", "--mode", "light", "--once-per-slot",
                              "--today", "2026-10-26",
                              "--state-dir", str(state_dir)])
    rc = args.func(args)
    assert rc == 0
    return sent["called"]


def test_slot_kompat_entri_full_lama_mengisi_pagi(monkeypatch, tmp_path, capsys):
    assert _run_slot_with_legacy(monkeypatch, tmp_path, "full", 8) is False


def test_slot_kompat_entri_full_lama_tidak_mengisi_sore(monkeypatch, tmp_path, capsys):
    assert _run_slot_with_legacy(monkeypatch, tmp_path, "full", 17) is True


def test_slot_kompat_entri_light_lama_tidak_memblokir(monkeypatch, tmp_path, capsys):
    assert _run_slot_with_legacy(monkeypatch, tmp_path, "light", 8) is True
