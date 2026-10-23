"""Gerbang pemeriksaan laporan riset Tender Bot.

1. Teks: em dash, en dash, kutip lengkung, emoji di Markdown dan HTML harus 0.
2. impeccable detect --json pada HTML: hasil JSON harus [] (exit code dicatat).
3. Kontras semua pasangan warna teks dan latar yang dipakai CSS.
4. PDF lewat PyMuPDF: jumlah halaman, font ter-embed (tanpa Type3), teks bisa
   diekstrak, tidak ada halaman kosong, tidak ada teks di luar area cetak.
5. Render tiap halaman ke PNG (zoom 1.5) di folder preview.
Jalankan: python periksa.py
"""
import json
import os
import re
import subprocess
from pathlib import Path

import fitz  # PyMuPDF

HERE = Path(__file__).resolve().parent
MD = HERE.parent / "riset" / "riset-eproc-bank-edc.md"
HTML = HERE / "laporan-riset-eproc-bank-edc.html"
PDF = HERE / "laporan-riset-eproc-bank-edc.pdf"
PREVIEW = HERE / "preview"
TMP = HERE / ".tmp"
DETECT = r"C:\Users\arify\.claude\skills\impeccable\scripts\impeccable.cmd"

EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]")


def gate_text():
    print("== Gerbang 1: teks")
    for path in (MD, HTML):
        t = path.read_text(encoding="utf-8")
        counts = {
            "em dash": t.count("\u2014"),
            "en dash": t.count("\u2013"),
            "kutip lengkung": sum(t.count(ch) for ch in "\u201c\u201d\u2018\u2019"),
            "emoji": len(EMOJI_RE.findall(t)),
        }
        print(f"  {path.name}: {counts}")


def gate_detect():
    print("== Gerbang 2: impeccable detect")
    TMP.mkdir(exist_ok=True)
    env = dict(os.environ, TEMP=str(TMP), TMP=str(TMP))
    r = subprocess.run([DETECT, "detect", "--json", str(HTML)], capture_output=True,
                       text=True, encoding="utf-8", env=env, cwd=HERE, timeout=300)
    out = r.stdout.strip()
    try:
        data = json.loads(out) if out else None
    except json.JSONDecodeError:
        data = None
    print(f"  exit code: {r.returncode}")
    if data is None:
        print("  stdout bukan JSON:", out[:300])
        print("  stderr:", r.stderr[:300])
        return
    print(f"  jumlah temuan: {len(data)}")
    seen = {}
    for f in data:
        key = (f.get("antipattern"), f.get("snippet"))
        seen[key] = seen.get(key, 0) + 1
    for (ap, snip), n in sorted(seen.items(), key=lambda kv: -kv[1])[:25]:
        print(f"   {n:3d}x {ap}: {snip}")
    if not data:
        print("  hasil: []")


def lum(hexc):
    hexc = hexc.lstrip("#")
    rgb = [int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def gate_contrast():
    print("== Gerbang 3: kontras (minimal 4,5:1)")
    pairs = [
        ("teks isi --ink", "#1f2326", "#ffffff"),
        ("teks sekunder --ink-muted", "#474e54", "#ffffff"),
        ("label/catatan --ink-faint", "#5a6268", "#ffffff"),
        ("judul seksi/tautan --accent", "#6c2718", "#ffffff"),
        ("header tabel --ink di --panel", "#1f2326", "#f1f3f4"),
        ("tag di --panel", "#5a6268", "#f1f3f4"),
        ("footer #5a6268", "#5a6268", "#ffffff"),
        ("seleksi teks", "#1f2326", "#ead7d2"),
    ]
    for name, fg, bg in pairs:
        r = ratio(fg, bg)
        print(f"  {name}: {r:.2f}:1 {'lolos' if r >= 4.5 else 'GAGAL'}")


def gate_pdf():
    print("== Gerbang 4: PDF")
    doc = fitz.open(PDF)
    print(f"  halaman: {doc.page_count}")
    fonts = {}
    problems = []
    for i, page in enumerate(doc, start=1):
        for f in page.get_fonts(full=True):
            # (xref, ext, type, basefont, name, encoding, referencer)
            fonts.setdefault(f[3], set()).add(f[2])
            if f[2] == "Type3":
                problems.append(f"hal {i}: font Type3 {f[3]!r}")
        text = page.get_text("text").strip()
        if len(text) < 40:
            problems.append(f"hal {i}: teks sangat sedikit ({len(text)} karakter)")
        rect = page.rect
        for b in page.get_text("blocks"):
            x0, y0, x1, y1 = b[:4]
            if x0 < 20 or y0 < 20 or x1 > rect.width - 20 or y1 > rect.height - 10:
                problems.append(f"hal {i}: blok teks dekat/di luar tepi {tuple(round(v) for v in b[:4])}")
        print(f"  hal {i}: {len(text)} karakter teks, {len(page.get_text('words'))} kata")
    for name, types in sorted(fonts.items()):
        print(f"  font: {name} {sorted(types)}")
    print("  masalah:", problems if problems else "tidak ada")
    return doc


def render(doc):
    print("== Gerbang 5: render PNG")
    PREVIEW.mkdir(exist_ok=True)
    for old in PREVIEW.glob("halaman-*.png"):
        old.unlink()
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        out = PREVIEW / f"halaman-{i:02d}.png"
        pix.save(out)
        print(f"  {out}")


if __name__ == "__main__":
    gate_text()
    gate_contrast()
    gate_detect()
    d = gate_pdf()
    render(d)
    import shutil
    shutil.rmtree(TMP, ignore_errors=True)
