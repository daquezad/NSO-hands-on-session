#!/usr/bin/env python3
"""
Story 6.5 — Assert PDF bookmark count >= number of nav entries that point to `.md` pages in mkdocs.yml.

Uses pypdf outline tree (nested lists) to count all bookmark entries.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parents[2]


def count_mkdocs_nav_md_leaves(mkdocs_yml: Path) -> int:
    """Count `*.md` targets under `nav:` (Home + Lab Guide leaves, etc.)."""
    text = mkdocs_yml.read_text(encoding="utf-8")
    lines = text.splitlines()
    nav_start: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == "nav:":
            nav_start = i + 1
            break
    if nav_start is None:
        return 0
    count = 0
    for line in lines[nav_start:]:
        if line.strip().startswith("extra:") and not line.startswith(" "):
            break
        if re.search(r":\s*[\w./-]+\.md\s*$", line):
            count += 1
    return count


def count_bookmarks(reader: PdfReader) -> int:
    """Total outline items (recursive), matching Story 6.4 finalize output."""

    def walk(outline: object) -> int:
        total = 0
        for o in outline or []:
            if isinstance(o, list):
                total += walk(o)
            else:
                total += 1
        return total

    return walk(getattr(reader, "outline", None))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate PDF bookmarks vs mkdocs nav (Story 6.5).")
    p.add_argument("pdf", type=Path, help="Path to PDF")
    p.add_argument(
        "--mkdocs-yml",
        type=Path,
        default=REPO_ROOT / "mkdocs.yml",
        help="mkdocs.yml path",
    )
    p.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Write human-readable report here",
    )
    args = p.parse_args(argv)

    pdf = args.pdf
    if not pdf.is_file():
        print(f"validate-pdf-bookmarks: missing PDF {pdf}", file=sys.stderr)
        return 1

    reader = PdfReader(str(pdf))
    bm = count_bookmarks(reader)
    nav = count_mkdocs_nav_md_leaves(args.mkdocs_yml)

    lines = [
        f"PDF: {pdf}",
        f"Bookmark count (recursive): {bm}",
        f"Nav .md leaf count: {nav}",
        f"Check: bookmarks >= nav_leaves → {bm >= nav} ({bm} >= {nav})",
    ]
    report_body = "\n".join(lines) + "\n"

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report_body, encoding="utf-8")

    print(report_body, end="")

    if bm < nav:
        print(
            f"validate-pdf-bookmarks: FAIL — need at least {nav} bookmarks, got {bm}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
