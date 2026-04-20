#!/usr/bin/env python3
"""
Optimize PNG screenshots in docs/assets/images/ (Story 3.5, AR12).

- oxipng: lossless recompression in place (optional; must be on PATH).
- Per-chapter byte budget: warns if a subfolder exceeds 3 MB total (NFR-P6; warn-only).

WebP generation for the built site is handled in hooks.py (cwebp at mkdocs build time).

Usage:
  python3 scripts/optimize_images.py [--dry-run] [--budget-warn]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
IMAGES = _REPO / "docs" / "assets" / "images"

# NFR-P6 — warn thresholds (bytes)
CHAPTER_BUDGET = 3 * 1024 * 1024


def _run_oxipng(png: Path, dry_run: bool) -> bool:
    ox = shutil.which("oxipng")
    if not ox:
        return False
    args = [ox, "-o", "4", "--strip", "safe", str(png)]
    if dry_run:
        print("would run:", " ".join(args))
        return True
    subprocess.run(args, check=False)
    return True


def _chapter_bytes() -> list[tuple[Path, int]]:
    """Sum file sizes per immediate subdir of images/ (e.g. mermaid/, chapter folders)."""
    if not IMAGES.is_dir():
        return []
    out: list[tuple[Path, int]] = []
    for sub in sorted(IMAGES.iterdir()):
        if not sub.is_dir():
            continue
        total = sum(f.stat().st_size for f in sub.rglob("*") if f.is_file())
        out.append((sub, total))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Optimize PNGs with oxipng; optional budget warnings.")
    ap.add_argument("--dry-run", action="store_true", help="Print oxipng commands only.")
    ap.add_argument("--budget-warn", action="store_true", help="Warn on per-subfolder size > 3 MB.")
    args = ap.parse_args()

    if not IMAGES.is_dir():
        print("No docs/assets/images/", file=sys.stderr)
        return 0

    oxipng_any = False
    for png in sorted(IMAGES.rglob("*.png")):
        if _run_oxipng(png, args.dry_run):
            oxipng_any = True
    if not oxipng_any and not args.dry_run:
        print(
            "Note: oxipng not on PATH — skipped in-place PNG optimization.",
            file=sys.stderr,
        )

    if args.budget_warn:
        for folder, total in _chapter_bytes():
            if total > CHAPTER_BUDGET:
                print(
                    f"[image budget] {folder.relative_to(_REPO)}: {total} bytes "
                    f"(>{CHAPTER_BUDGET} warn threshold)",
                    file=sys.stderr,
                )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
