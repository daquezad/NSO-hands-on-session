#!/usr/bin/env python3
"""
Extract embedded raster images from a workbook PDF (pypdf).

Default output: build/workbook-pdf-media/ (override with --out).

Example:
  python3 scripts/extract_workbook_pdf_images.py Workbook.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


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
        help="Path to PDF (default: ./Workbook.pdf)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: build/workbook-pdf-media)",
    )
    args = ap.parse_args()
    pdf = args.pdf.resolve()
    if not pdf.is_file():
        print(f"ERROR: not a file: {pdf}", file=sys.stderr)
        return 1

    out = args.out
    if out is None:
        out = Path("build/workbook-pdf-media")
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    r = PdfReader(str(pdf))
    n = 0
    for pi, page in enumerate(r.pages):
        for ii, img in enumerate(page.images):
            ext = img.name.split(".")[-1] if "." in img.name else "bin"
            name = f"page{pi + 1:02d}_img{ii + 1:02d}.{ext}"
            data = img.data
            if data:
                (out / name).write_bytes(data)
                n += 1

    print(f"Extracted {n} image(s) → {out}", file=sys.stderr)
    return 0 if n else 2


if __name__ == "__main__":
    raise SystemExit(main())
