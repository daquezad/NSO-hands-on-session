#!/usr/bin/env python3
"""
NFR-R4 — fail on broken internal links or missing assets referenced from built HTML under site/.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

try:
    from bs4 import BeautifulSoup
except ImportError as e:  # pragma: no cover
    print("ERROR: beautifulsoup4 required.", file=sys.stderr)
    raise SystemExit(2) from e


def _resolve_target(site_root: Path, page_file: Path, raw: str) -> Path | None:
    raw = (raw or "").strip()
    if not raw or raw.startswith("#") or raw.startswith("data:") or raw.startswith("mailto:"):
        return None
    if raw.startswith("javascript:"):
        return None
    u = urlparse(urljoin(page_file.as_uri(), raw))
    if u.scheme not in ("file", ""):
        return None
    rel = Path(raw.split("#")[0].split("?")[0])
    if rel.is_absolute():
        return None
    target = (page_file.parent / rel).resolve()
    try:
        target.relative_to(site_root.resolve())
    except ValueError:
        return None
    return target


def _target_is_valid_page(site_root: Path, target: Path) -> bool:
    """MkDocs emits directory URLs; a chapter is valid if index.html exists there or at target."""
    if target.is_file():
        return True
    if target.is_dir() and (target / "index.html").is_file():
        return True
    return False


def _check_file(site_root: Path, page_file: Path, attr: str, tag) -> list[str]:
    raw = tag.get(attr)
    if not raw:
        return []
    target = _resolve_target(site_root, page_file, raw)
    if target is None:
        return []
    if _target_is_valid_page(site_root, target):
        return []
    rel_page = page_file.relative_to(site_root)
    return [f"{rel_page}: missing {attr}={raw!r} -> {target.relative_to(site_root)}"]


def main() -> int:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
    if not site.is_dir():
        print(f"ERROR: not a directory: {site}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for html in sorted(site.rglob("*.html")):
        try:
            text = html.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            errors.append(f"{html}: read error: {e}")
            continue
        soup = BeautifulSoup(text, "html.parser")

        for a in soup.find_all("a"):
            href = a.get("href")
            if not href:
                continue
            if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
                continue
            u = urlparse(href)
            if u.scheme and u.scheme not in ("http", "https", ""):
                continue
            if u.scheme in ("http", "https"):
                continue  # external — not checked here (NFR-S3 expects none at runtime)
            t = _resolve_target(site, html, href)
            if t is None:
                continue
            if not _target_is_valid_page(site, t):
                errors.append(
                    f"{html.relative_to(site)}: broken link href={href!r} -> {t.relative_to(site)}"
                )

        for tag_name, attr in (
            ("img", "src"),
            ("script", "src"),
            ("source", "src"),
        ):
            for tag in soup.find_all(tag_name):
                errors.extend(_check_file(site, html, attr, tag))

        for tag in soup.find_all("link"):
            href = tag.get("href")
            if not href:
                continue
            errors.extend(_check_file(site, html, "href", tag))

    if errors:
        print("ERROR: broken internal references:", file=sys.stderr)
        for e in errors[:200]:
            print(f"  {e}", file=sys.stderr)
        if len(errors) > 200:
            print(f"  ... and {len(errors) - 200} more", file=sys.stderr)
        return 1

    print(f"OK: internal link check passed ({len(list(site.rglob('*.html')))} HTML files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
