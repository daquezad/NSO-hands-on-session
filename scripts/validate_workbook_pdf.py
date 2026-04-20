#!/usr/bin/env python3
"""
Cross-check Workbook.pdf against the Markdown workbook (same role as validating DOCX).

- Extracts full text and counts embedded images (pypdf).
- Optionally compares image count to Workbook-HT-v02.docx (zip media count).
- Flags IP / addressing differences: PDF uses legacy lab examples (198.18.x.x in HT v02);
  Markdown uses RFC 5737 documentation addresses (198.51.100.x) per scrub logs.

Usage:
  python3 scripts/validate_workbook_pdf.py [Workbook.pdf]
  python3 scripts/validate_workbook_pdf.py Workbook.pdf --docx Workbook-HT-v02.docx

Exit 0 always (report-only); use grep/CI on output if you need a hard gate.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path


def _docx_media_count(docx: Path) -> int:
    with zipfile.ZipFile(docx) as z:
        return sum(1 for n in z.namelist() if n.startswith("word/media/") and not n.endswith("/"))


def main() -> int:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("ERROR: pypdf required (pip install -r requirements.txt)", file=sys.stderr)
        return 2

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "pdf",
        type=Path,
        nargs="?",
        default=Path("Workbook.pdf"),
        help="Path to Workbook.pdf (default: ./Workbook.pdf)",
    )
    ap.add_argument(
        "--docx",
        type=Path,
        default=None,
        help="Optional .docx path to compare embedded image counts",
    )
    args = ap.parse_args()
    pdf_path = args.pdf.resolve()
    if not pdf_path.is_file():
        print(f"ERROR: PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    r = PdfReader(str(pdf_path))
    pages = len(r.pages)
    img_count = sum(len(p.images) for p in r.pages)
    blob = "\n".join((p.extract_text() or "") for p in r.pages)

    # --- Report ---
    print("## Workbook PDF validation\n")
    print(f"- **File:** `{pdf_path}`")
    print(f"- **Pages:** {pages}")
    print(f"- **Embedded images (pypdf):** {img_count}\n")

    if args.docx:
        dx = args.docx.resolve()
        if dx.is_file():
            mc = _docx_media_count(dx)
            print(f"- **DOCX `word/media` files:** {mc} (`{dx.name}`)")
            if mc != img_count:
                print(
                    f"  - **Note:** Count differs (PDF {img_count} vs DOCX media {mc}). "
                    "Normal if one export omits a logo or uses vector graphics differently."
                )
            else:
                print("  - **Match:** Image counts align.")
        else:
            print(f"- **DOCX:** not found ({dx}), skipped.\n")

    print("### Section labels (PDF uses 1.1, 1.2, … — not `Lab 2` / `Lab 4`)\n")
    print(
        "| PDF section | Typical Markdown chapter |\n"
        "|-------------|-----------------------------|\n"
        "| 1.1 Install NSO and NEDs | `docs/02-install-nso-neds.md` |\n"
        "| 1.2 Registering XRd routers | `docs/03-register-xrd-routers.md` |\n"
        "| 1.3 Configure Devices using NSO | `docs/04-configure-devices.md` |\n"
    )

    print("### Text presence (procedural keywords)\n")
    keys = [
        ("server-alias / Web UI access", lambda t: "server-alias" in t.lower() and ("webui" in t.lower() or "web ui" in t.lower())),
        ("sync-from", lambda t: "sync-from" in t.lower()),
        ("IPv4 change 10.1.1.3 → 10.1.1.30 (strings)", lambda t: "10.1.1.3" in t and "10.1.1.30" in t),
        ("Listen 0.0.0.0 (lab)", lambda t: "0.0.0.0" in t),
    ]
    for label, fn in keys:
        ok = fn(blob)
        print(f"- {'✓' if ok else '✗'} {label}")

    print("\n### IP addressing: PDF vs Markdown (scrub)\n")
    pdf_198 = sorted(set(re.findall(r"198(?:\.\d+){3}", blob)))
    md_doc_ips = ("198.51.100.27", "198.51.100.2")  # docs/02 + docs/04 examples
    print(f"- **198.x addresses found in PDF text:** {pdf_198 or '(none)'}")
    print(f"- **Markdown documentation examples:** `{md_doc_ips[0]}` (NSO host / `server-alias`), `{md_doc_ips[1]}` (xr-1 mgmt SSH)")
    overlap = [x for x in pdf_198 if x in md_doc_ips]
    if not overlap and pdf_198:
        print(
            "  - **INFO:** PDF uses different example IPs than the scrubbed Markdown. "
            "That is expected if the DOCX/PDF predates `docs/scrub-logs/` — keep lab sheets authoritative for live classes."
        )
    elif overlap:
        print("  - **INFO:** At least one PDF IP matches Markdown examples.")

    print("\nDone (report-only, exit 0).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
