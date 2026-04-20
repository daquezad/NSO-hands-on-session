#!/usr/bin/env python3
"""
Story 6.6 — Cisco Confidential classification:
  - HTML: every page under site_dir must include the classification banner marker.
  - PDF: every non-cover page must contain the phrase in extracted text (footer margin).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader

MARKER_HTML = "css-classification-banner"
PHRASE = "cisco confidential"


def scan_html(site_dir: Path) -> list[str]:
    bad: list[str] = []
    for html_path in sorted(site_dir.rglob("*.html")):
        rel = html_path.relative_to(site_dir)
        try:
            text = html_path.read_text(encoding="utf-8", errors="replace").lower()
        except OSError as e:
            bad.append(f"{rel}: read error {e}")
            continue
        if MARKER_HTML not in text and PHRASE not in text:
            bad.append(f"{rel}: missing classification banner / '{PHRASE}'")
    return bad


def scan_pdf(pdf_path: Path, *, skip_cover: bool = True) -> list[str]:
    bad: list[str] = []
    reader = PdfReader(str(pdf_path))
    for i, page in enumerate(reader.pages):
        if skip_cover and i == 0:
            continue
        t = (page.extract_text() or "").lower()
        if PHRASE not in t:
            bad.append(f"{pdf_path.name}: page {i + 1}: missing '{PHRASE}' in text")
    return bad


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Classification banner check (Story 6.6).")
    p.add_argument("site_dir", type=Path)
    p.add_argument("pdf", type=Path, nargs="?", help="Learner PDF")
    p.add_argument("--no-skip-cover", action="store_true", help="Require phrase on every PDF page including cover")
    args = p.parse_args(argv)

    bad = scan_html(args.site_dir)
    if args.pdf and args.pdf.is_file():
        bad.extend(scan_pdf(args.pdf, skip_cover=not args.no_skip_cover))
    elif args.pdf:
        print(f"check-classification: skip missing PDF {args.pdf}", file=sys.stderr)

    if bad:
        print("Classification check failures:", file=sys.stderr)
        for line in bad:
            print(line, file=sys.stderr)
        return 1
    print("check-classification: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
