#!/usr/bin/env python3
"""
Extract embedded images from a .docx (Office Open XML) into a directory.

Usage:
  python3 scripts/extract_docx_media.py /path/to/Workbook-HT-v02.docx [--out dir]

.docx is a ZIP archive; images live under word/media/.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx", type=Path, help="Path to .docx file")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: <docx-stem>-media next to the file)",
    )
    args = ap.parse_args()
    docx = args.docx.resolve()
    if not docx.is_file():
        print(f"ERROR: not a file: {docx}", file=sys.stderr)
        return 1
    if docx.suffix.lower() != ".docx":
        print("ERROR: expected a .docx file", file=sys.stderr)
        return 1

    out = args.out
    if out is None:
        out = docx.parent / f"{docx.stem}-media"
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    prefix = "word/media/"
    count = 0
    with zipfile.ZipFile(docx, "r") as zf:
        for name in zf.namelist():
            if not name.startswith(prefix) or name.endswith("/"):
                continue
            data = zf.read(name)
            dest = out / Path(name).name
            dest.write_bytes(data)
            count += 1
            print(dest)

    if count == 0:
        print(f"No files under {prefix!r} (empty document or unusual packaging).", file=sys.stderr)
        return 2

    print(f"Extracted {count} file(s) → {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
