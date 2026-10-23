"""State tersimpan: seen.json, runs.json, source_health.json.

Semua di bawah folder state/. Hanya memuat data tender publik (aman untuk
repo publik). Ditulis dengan JSON stabil (indent, sort_keys) supaya diff
di Git rapi dan commit-nya kecil.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from .models import Item

SOURCE_HEALTH_WARN_THRESHOLD = 3  # gagal berturut-turut sebelum diberi peringatan


def _read_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


@dataclass
class State:
    """Pembungkus folder state/."""

    root: Path
    seen: dict = field(default_factory=dict)  # fingerprint -> {bank,title,published,first_seen}
    runs: list = field(default_factory=list)  # daftar record run
    source_health: dict = field(default_factory=dict)  # url -> {consecutive_failures,last_ok,last_error}

    @classmethod
    def load(cls, root: Path) -> "State":
        root = Path(root)
        return cls(
            root=root,
            seen=_read_json(root / "seen.json", {}),
            runs=_read_json(root / "runs.json", []),
            source_health=_read_json(root / "source_health.json", {}),
        )

    def save(self) -> None:
        _write_json(self.root / "seen.json", self.seen)
        _write_json(self.root / "runs.json", self.runs)
        _write_json(self.root / "source_health.json", self.source_health)

    # ---- seen ----
    def is_seen(self, fingerprint: str) -> bool:
        return fingerprint in self.seen

    def seen_titles(self) -> list[tuple[str, str, str]]:
        """(bank, judul, tanggal_iso) untuk cek near-duplicate."""
        out = []
        for rec in self.seen.values():
            out.append((rec.get("bank", ""), rec.get("title", ""), rec.get("published") or ""))
        return out

    def mark_seen(self, item: Item, run_date: str) -> None:
        self.seen[item.fingerprint] = {
            "bank": item.bank,
            "title": item.title,
            "url": item.url,
            "published": item.published,
            "first_seen": run_date,
        }

    # ---- runs ----
    def has_full_run_on(self, run_date: str) -> bool:
        return any(
            r.get("date") == run_date and r.get("mode") == "full" for r in self.runs
        )

    def record_run(
        self,
        run_date: str,
        mode: str,
        checked: int,
        failed: int,
        new_items: int,
        status: str = "ok",
    ) -> None:
        self.runs.append(
            {
                "date": run_date,
                "mode": mode,
                "checked": checked,
                "failed": failed,
                "new_items": new_items,
                "status": status,
            }
        )

    # ---- source health ----
    def record_source_ok(self, url: str, run_date: str) -> None:
        self.source_health[url] = {
            "consecutive_failures": 0,
            "last_ok": run_date,
            "last_error": None,
        }

    def record_source_failure(self, url: str, reason: str, run_date: str) -> int:
        rec = self.source_health.get(url, {"consecutive_failures": 0, "last_ok": None})
        rec["consecutive_failures"] = int(rec.get("consecutive_failures", 0)) + 1
        rec["last_error"] = f"{run_date}: {reason}"
        self.source_health[url] = rec
        return rec["consecutive_failures"]

    def unhealthy_sources(self) -> list[tuple[str, int, Optional[str]]]:
        """Sumber yang gagal >= ambang berturut-turut."""
        out = []
        for url, rec in self.source_health.items():
            fails = int(rec.get("consecutive_failures", 0))
            if fails >= SOURCE_HEALTH_WARN_THRESHOLD:
                out.append((url, fails, rec.get("last_error")))
        return out
