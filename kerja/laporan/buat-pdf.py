"""Buat PDF laporan riset Tender Bot dari Markdown gabungan.

Sumber tunggal: ..\\riset\\riset-eproc-bank-edc.md. Skrip ini mengubah Markdown
(subset kecil: judul, paragraf, daftar, tabel, tautan, kode) menjadi HTML di
folder ini, lalu merender PDF A4 dengan Chromium Playwright (page.pdf) dan nomor
halaman di footer. Baris "<!-- class: x -->" di Markdown memberi kelas CSS pada
blok sesudahnya.

Folder sementara Chromium diarahkan ke .tmp di folder ini (bukan drive C) dan
dihapus setelah selesai. Sisa proses chrome yang dimatikan hanya milik
ms-playwright, supaya browser lain milik pengguna tidak tersentuh.
Jalankan: python buat-pdf.py
"""
import asyncio
import html
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MD = HERE.parent / "riset" / "riset-eproc-bank-edc.md"
HTML = HERE / "laporan-riset-eproc-bank-edc.html"
PDF = HERE / "laporan-riset-eproc-bank-edc.pdf"
TMP = HERE / ".tmp"
# Path Chromium Playwright; atur lewat env CHROME_PATH bila lokasinya berbeda.
CHROME = os.environ.get(
    "CHROME_PATH",
    str(Path.home() / "AppData/Local/ms-playwright/chromium-1247/chrome-win64/chrome.exe"),
)

TAG_RE = re.compile(r"\[(KOORDINATOR|PORTAL|BERITA|SNIPPET|INFERENSI|TERBATAS)\]")
INLINE_RE = re.compile(
    r"`(?P<code>[^`]+)`"
    r"|<(?P<auto>https?://[^>\s]+)>"
    r"|\[(?P<ltext>[^\]]+)\]\((?P<lurl>https?://[^)\s]+)\)"
)


def esc_text(s: str) -> str:
    s = html.escape(s, quote=False)
    return TAG_RE.sub(lambda m: f'<span class="tag">[{m.group(1)}]</span>', s)


def soft_breaks(s: str) -> str:
    """Izinkan pindah baris sesudah titik dan garis miring pada domain/path."""
    return re.sub(r"([./])(?=[^\s])", r"\1<wbr>", s)


def inline(s: str, desc_span: bool = False) -> str:
    out, pos, first_auto = [], 0, True
    for m in INLINE_RE.finditer(s):
        text = s[pos:m.start()]
        if desc_span and first_auto and m.group("auto"):
            out.append(f'<span class="desc">{esc_text(text)}</span>')
        else:
            out.append(esc_text(text))
        if m.group("code") is not None:
            out.append(f"<code>{soft_breaks(html.escape(m.group('code'), quote=False))}</code>")
        elif m.group("auto") is not None:
            u = m.group("auto")
            out.append(f'<a class="url" href="{html.escape(u)}">{html.escape(u, quote=False)}</a>')
            first_auto = False
        else:
            u = m.group("lurl")
            lt = esc_text(m.group("ltext"))
            if " " not in lt and "." in lt:
                lt = soft_breaks(lt)
            out.append(f'<a href="{html.escape(u)}">{lt}</a>')
        pos = m.end()
    out.append(esc_text(s[pos:]))
    return "".join(out)


def is_special(line: str) -> bool:
    return bool(
        re.match(r"#{1,4}\s", line)
        or line.startswith("|")
        or line.startswith("- ")
        or re.match(r"\d+\.\s", line)
        or line.strip().startswith("<!--")
    )


def parse(md: str):
    lines = md.replace("\r\n", "\n").split("\n")
    blocks, i, cls = [], 0, None
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"<!--\s*class:\s*([\w-]+)\s*-->", line.strip())
        if m:
            cls = m.group(1)
            i += 1
            continue
        m = re.match(r"(#{1,4})\s+(.*)", line)
        if m:
            blocks.append(("h", len(m.group(1)), m.group(2), None))
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            blocks.append(("table", rows, None, cls))
            cls = None
            continue
        if line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:].strip())
                i += 1
            blocks.append(("ul", items, None, cls))
            cls = None
            continue
        if re.match(r"\d+\.\s", line):
            items = []
            while i < len(lines) and re.match(r"\d+\.\s", lines[i]):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i]).strip())
                i += 1
            blocks.append(("ol", items, None, cls))
            cls = None
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not is_special(lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append(("p", " ".join(para), None, cls))
        cls = None
    return blocks


def render_table(rows, cls):
    head, body = rows[0], rows[2:]
    classes = "data" + (f" {cls}" if cls else "")
    out = [f'<table class="{classes}">', "<colgroup>"]
    out += [f'<col class="c{n + 1}">' for n in range(len(head))]
    out += ["</colgroup>", "<thead><tr>"]
    out += [f'<th scope="col">{inline(c)}</th>' for c in head]
    out += ["</tr></thead>", "<tbody>"]
    for r in body:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
    out += ["</tbody>", "</table>"]
    return "\n".join(out)


def to_html(md: str) -> str:
    blocks = parse(md)
    title = next(b[2] for b in blocks if b[0] == "h" and b[1] == 1)
    body, in_section, header_open, meta_done = [], False, False, False
    for kind, a, b, cls in blocks:
        if kind == "h":
            level, text = a, b
            if level == 1:
                body.append("<header>")
                body.append(f"<h1>{inline(text)}</h1>")
                header_open = True
                continue
            if level == 2:
                if header_open:
                    body.append("</header>")
                    header_open = False
                if in_section:
                    body.append("</section>")
                sec_cls = ' class="appendix"' if text.lower().startswith("daftar sumber") else ""
                body.append(f"<section{sec_cls}>")
                in_section = True
            body.append(f"<h{level}>{inline(text)}</h{level}>")
        elif kind == "p":
            if header_open and not meta_done:
                body.append(f'<p class="meta">{inline(a)}</p>')
                meta_done = True
            else:
                c = f' class="{cls}"' if cls else ""
                body.append(f"<p{c}>{inline(a)}</p>")
        elif kind in ("ul", "ol"):
            c = f' class="{cls}"' if cls else ""
            desc = cls == "sources"
            items = "\n".join(f"<li>{inline(x, desc_span=desc)}</li>" for x in a)
            body.append(f"<{kind}{c}>\n{items}\n</{kind}>")
        elif kind == "table":
            body.append(render_table(a, cls))
    if header_open:
        body.append("</header>")
    if in_section:
        body.append("</section>")
    return (
        '<!DOCTYPE html>\n<html lang="id">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{html.escape(title, quote=False)}</title>\n"
        '<link rel="stylesheet" href="laporan.css">\n</head>\n<body>\n<main>\n'
        + "\n".join(body)
        + "\n</main>\n</body>\n</html>\n"
    )


FOOTER = (
    '<div style="width:100%;font-family:\'Segoe UI\',sans-serif;font-size:9px;'
    'color:#5a6268;padding:0 16mm;display:flex;justify-content:space-between;">'
    "<span>Tender Bot &middot; Peta portal e-procurement bank dan tender EDC &middot; 23 Oktober 2026</span>"
    '<span>Halaman <span class="pageNumber"></span> dari <span class="totalPages"></span></span>'
    "</div>"
)
HEADER = "<div></div>"


async def build_pdf():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROME)
        try:
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(HTML.as_uri(), wait_until="networkidle")
            await page.emulate_media(media="print")
            await page.evaluate("document.fonts.ready")
            await page.pdf(
                path=str(PDF),
                prefer_css_page_size=True,
                print_background=True,
                display_header_footer=True,
                header_template=HEADER,
                footer_template=FOOTER,
                margin={"top": "18mm", "bottom": "16mm", "left": "16mm", "right": "16mm"},
            )
            await page.close()
            await context.close()
        finally:
            await browser.close()


def kill_leftover_chrome():
    """Matikan sisa chrome ms-playwright saja (Windows), dibatasi waktu."""
    if sys.platform != "win32":
        return
    ps = (
        "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
        "Where-Object { $_.ExecutablePath -like '*ms-playwright*' } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, timeout=20)
    except Exception as exc:  # pembersihan bersifat best effort
        print("cleanup note:", exc)


if __name__ == "__main__":
    HTML.write_text(to_html(MD.read_text(encoding="utf-8")), encoding="utf-8")
    print("HTML:", HTML)
    if "--html-only" in sys.argv:
        sys.exit(0)
    TMP.mkdir(exist_ok=True)
    os.environ["TEMP"] = str(TMP)
    os.environ["TMP"] = str(TMP)
    try:
        asyncio.run(build_pdf())
        print("PDF:", PDF)
    finally:
        kill_leftover_chrome()
        shutil.rmtree(TMP, ignore_errors=True)
