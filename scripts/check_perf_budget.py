#!/usr/bin/env python3
"""
NFR-P5 — per-page weight: HTML + linked CSS + linked JS (and fonts/preloads), excluding images, ≤ 500 KB.
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

MAX_BYTES = 500 * 1024
IMAGE_EXT = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp"})


def _is_probably_image(url: str) -> bool:
    path = urlparse(url).path.lower()
    for ext in IMAGE_EXT:
        if path.endswith(ext):
            return True
    return False


def _resolve_file(site_root: Path, page_file: Path, raw: str) -> Path | None:
    raw = (raw or "").strip()
    if not raw or raw.startswith("#") or raw.startswith("data:") or raw.startswith("mailto:"):
        return None
    if raw.startswith("javascript:"):
        return None
    u = urlparse(urljoin(page_file.as_uri(), raw))
    if u.scheme not in ("file", ""):
        return None
    path = Path(unquote(u.path))
    if not path.is_absolute():
        rel = Path(raw.split("#")[0].split("?")[0])
        if rel.is_absolute():
            return None
        target = (page_file.parent / rel).resolve()
    else:
        target = path
    try:
        target.relative_to(site_root.resolve())
    except ValueError:
        return None
    return target


def _page_weight(site_root: Path, html_path: Path) -> tuple[int, list[str]]:
    raw_html = html_path.read_bytes()
    total = len(raw_html)
    soup = BeautifulSoup(raw_html.decode("utf-8", errors="replace"), "html.parser")
    touched: list[str] = []

    for tag in soup.find_all("link"):
        rel = tag.get("rel")
        if isinstance(rel, list):
            rel_s = " ".join(rel).lower()
        else:
            rel_s = (rel or "").lower()
        href = tag.get("href")
        if not href:
            continue
        if "stylesheet" in rel_s or "preload" in rel_s:
            if _is_probably_image(href):
                continue
            t = _resolve_file(site_root, html_path, href)
            if t and t.is_file():
                sz = t.stat().st_size
                total += sz
                touched.append(f"{t.relative_to(site_root)} ({sz} B)")

    for tag in soup.find_all("script"):
        src = tag.get("src")
        if not src:
            continue
        if _is_probably_image(src):
            continue
        t = _resolve_file(site_root, html_path, src)
        if t and t.is_file():
            sz = t.stat().st_size
            total += sz
            touched.append(f"{t.relative_to(site_root)} ({sz} B)")

    return total, touched


def main() -> int:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
    if not site.is_dir():
        print(f"ERROR: not a directory: {site}", file=sys.stderr)
        return 1

    bad: list[tuple[str, int]] = []
    for html in sorted(site.rglob("*.html")):
        total, _ = _page_weight(site, html)
        if total > MAX_BYTES:
            rel = html.relative_to(site)
            bad.append((str(rel), total))

    if bad:
        print("ERROR: pages exceeding 500 KB (HTML + CSS + JS, images excluded) (NFR-P5):", file=sys.stderr)
        for path, total in bad:
            print(f"  {path}: {total} bytes ({total / 1024:.1f} KB)", file=sys.stderr)
        return 1

    n = len(list(site.rglob("*.html")))
    print(f"OK: perf budget passed ({n} HTML pages, max {MAX_BYTES} bytes each).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
