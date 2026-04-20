#!/usr/bin/env python3
"""Post-build guard for NFR-S8 / FR47 — every HTML page must carry noindex,nofollow; no sitemap.xml."""

from __future__ import annotations

import sys
from pathlib import Path


def _html_has_robots_noindex(html: str) -> bool:
    lower = html.lower()
    if 'name="robots"' not in lower and "name='robots'" not in lower:
        return False
    if "noindex" not in lower:
        return False
    if "nofollow" not in lower:
        return False
    return True


def main() -> int:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
    if not site.is_dir():
        print(f"ERROR: site directory not found: {site}", file=sys.stderr)
        return 1

    sitemap = site / "sitemap.xml"
    if sitemap.is_file():
        print(f"ERROR: {sitemap} must not exist (NFR-S8).", file=sys.stderr)
        return 1

    bad: list[Path] = []
    for html in sorted(site.rglob("*.html")):
        try:
            text = html.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"ERROR: cannot read {html}: {e}", file=sys.stderr)
            return 1
        if not _html_has_robots_noindex(text):
            bad.append(html)

    if bad:
        print("ERROR: missing noindex/nofollow robots meta on:", file=sys.stderr)
        for p in bad:
            print(f"  {p.relative_to(site)}", file=sys.stderr)
        return 1

    print(f"OK: noindex sweep passed ({len(list(site.rglob('*.html')))} HTML files under {site}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
