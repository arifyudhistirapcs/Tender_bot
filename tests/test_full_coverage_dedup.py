"""Uji dedup cakupan mode full: jumlah bank dicek = gabungan UNIK, dan bank
gagal tidak tercantum dua kali (alasan digabung bila keduanya gagal).

Regression untuk bug: coverage.checked inbox dijumlahkan dengan bank kolektor
light tanpa dedup, sehingga "Dicek 45 bank" padahal hanya 43 unik.
"""

from datetime import date

import tenderbot.pipeline as pipeline
from tenderbot.config import Bank
from tenderbot.inbox import InboxLoadResult
from tenderbot.pipeline import run_full, _build_alias_map, _canon_bank
from tenderbot.state import State
from tenderbot.config import load_keywords

TODAY = date(2026, 10, 23)
KW = load_keywords()


def _banks():
    """Daftar bank uji: termasuk pasangan alias yang harus dihitung satu."""
    return [
        Bank(name="BRI", aliases=["Bank Rakyat Indonesia", "BRI", "BBRI"],
             group="bumn", access="vendor_login"),
        Bank(name="Bank Sumut", aliases=["Bank Sumut"], group="bpd",
             access="public"),
        # Pasangan 1: satu entri dengan alias syariah.
        Bank(name="Bank Aceh",
             aliases=["Bank Aceh", "Bank Aceh Syariah",
                      "Bank Pembangunan Daerah Aceh"],
             group="bpd", access="not_found"),
        # Pasangan 2: dua entri yang sengaja dipisah di banks.yaml tapi berbagi
        # alias "Bank DKI" -> harus digabung jadi satu identitas.
        Bank(name="Bank Jakarta", aliases=["Bank Jakarta", "Bank DKI"],
             group="bpd", access="blocked"),
        Bank(name="Bank DKI", aliases=["Bank DKI"], group="bpd",
             access="blocked"),
    ]


def _no_collect(monkeypatch, failed=None):
    """Stub collect_light: tidak menyentuh jaringan, kembalikan [] kandidat.

    `failed` (opsional): daftar (nama_berhias, alasan) yang ditulis kolektor ke
    report.failed, untuk menguji dedup terhadap coverage.failed inbox.
    """
    def _fake(fetcher, banks, feeds, keywords, state, run_date, report,
              gdelt_sleep=None, skip_news=False):
        # Kolektor light menghitung tiap bank sebagai "dicek".
        report.checked = len(banks)
        for name, reason in (failed or []):
            report.failed.append((name, reason))
        return []
    monkeypatch.setattr(pipeline, "collect_light", _fake)


# ---- Peta alias menyatukan pasangan ----

def test_alias_map_menyatukan_aceh_dan_dki():
    banks = _banks()
    amap = _build_alias_map(banks)
    # Bank Aceh & Bank Aceh Syariah -> satu kanonik.
    assert _canon_bank("Bank Aceh", amap) == _canon_bank("Bank Aceh Syariah", amap)
    # Bank DKI & Bank Jakarta -> satu kanonik (dua entri yaml yang berbagi alias).
    assert _canon_bank("Bank DKI", amap) == _canon_bank("Bank Jakarta", amap)
    # Bank berbeda tetap berbeda.
    assert _canon_bank("BRI", amap) != _canon_bank("Bank Sumut", amap)


def test_nama_tak_dikenal_jadi_identitas_sendiri():
    amap = _build_alias_map(_banks())
    assert _canon_bank("Bank Antah Berantah", amap) == "Bank Antah Berantah"


# ---- Jumlah dicek = gabungan unik ----

def test_checked_gabungan_unik_tanpa_dobel(monkeypatch, tmp_path):
    banks = _banks()  # 5 entri, tapi 4 identitas unik (DKI==Jakarta)
    _no_collect(monkeypatch)
    state = State.load(tmp_path)
    # Inbox menyebut bank yang SAMA dengan yaml (termasuk via alias) + 1 unknown.
    inbox = InboxLoadResult(
        run_date="2026-10-23", mode="full",
        coverage_checked=["BRI", "Bank Sumut", "Bank Aceh Syariah",
                          "Bank DKI", "Koperasi Antah"],
    )
    report = run_full(None, banks, KW, state, TODAY, inbox)
    # Identitas unik: BRI, Bank Sumut, Bank Aceh, Bank Jakarta(=DKI) = 4 dari yaml
    # + "Koperasi Antah" (unknown, 1x) = 5. BUKAN 5 yaml + 5 inbox = 10.
    assert report.checked == 5


def test_checked_hanya_yaml_tanpa_inbox_coverage(monkeypatch, tmp_path):
    banks = _banks()
    _no_collect(monkeypatch)
    state = State.load(tmp_path)
    inbox = InboxLoadResult(run_date="2026-10-23", mode="full",
                            coverage_checked=[])
    report = run_full(None, banks, KW, state, TODAY, inbox)
    # 5 entri yaml -> 4 identitas unik.
    assert report.checked == 4


# ---- Bank gagal tidak dobel; alasan digabung ----

def test_failed_tidak_dobel_alasan_digabung(monkeypatch, tmp_path):
    banks = _banks()
    # Kolektor melaporkan BRI gagal lewat berita (nama berhias).
    _no_collect(monkeypatch, failed=[("BRI (berita)", "GDELT tidak mencakup")])
    state = State.load(tmp_path)
    # Inbox JUGA melaporkan BRI gagal (portal) + BNI unik.
    inbox = InboxLoadResult(
        run_date="2026-10-23", mode="full",
        coverage_checked=["BRI"],
        coverage_failed=[
            {"bank": "BRI", "reason": "portal diblokir WAF Incapsula"},
            {"bank": "BNI", "reason": "portal HTTP 503"},
        ],
    )
    report = run_full(None, banks, KW, state, TODAY, inbox)
    names = [n for n, _ in report.failed]
    # BRI hanya SEKALI (meski gagal di kolektor DAN inbox).
    bri_entries = [n for n in names if n.lower().startswith("bri")]
    assert len(bri_entries) == 1
    # Alasan BRI menggabungkan kedua sumber.
    bri_reason = next(r for n, r in report.failed if n.lower().startswith("bri"))
    assert "GDELT" in bri_reason
    assert "WAF" in bri_reason or "Incapsula" in bri_reason
    # BNI tetap tercantum (unik).
    assert any(n == "BNI" for n in names)


def test_failed_alasan_panjang_dipotong(monkeypatch, tmp_path):
    banks = _banks()
    _no_collect(monkeypatch)
    state = State.load(tmp_path)
    long_reason = "x" * 300
    inbox = InboxLoadResult(
        run_date="2026-10-23", mode="full",
        coverage_failed=[{"bank": "BRI", "reason": long_reason}],
    )
    report = run_full(None, banks, KW, state, TODAY, inbox)
    reason = next(r for n, r in report.failed if n == "BRI")
    assert len(reason) <= 120
    assert reason.endswith("...")


def test_failed_dki_dan_jakarta_digabung(monkeypatch, tmp_path):
    """Bila inbox melaporkan 'Bank DKI' gagal dan kolektor 'Bank Jakarta'
    gagal, keduanya satu identitas -> satu entri."""
    banks = _banks()
    _no_collect(monkeypatch,
                failed=[("Bank Jakarta (berita)", "HTTP 403 domain baru")])
    state = State.load(tmp_path)
    inbox = InboxLoadResult(
        run_date="2026-10-23", mode="full",
        coverage_failed=[{"bank": "Bank DKI", "reason": "HTTP 403 domain lama"}],
    )
    report = run_full(None, banks, KW, state, TODAY, inbox)
    jakarta_like = [(n, r) for n, r in report.failed
                    if "jakarta" in n.lower() or "dki" in n.lower()]
    assert len(jakarta_like) == 1
    _, reason = jakarta_like[0]
    assert "domain baru" in reason and "domain lama" in reason
