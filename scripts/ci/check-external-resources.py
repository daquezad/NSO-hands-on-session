#!/usr/bin/env python3
"""
Story 6.6 — Fail if built HTML or PDF references an external https?:// host not in external-allowlist.yaml,
or if a blocked host (e.g. Google Fonts) appears.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml
from bs4 import BeautifulSoup
from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALLOWLIST = REPO_ROOT / "scripts" / "ci" / "external-allowlist.yaml"


def _host_allowed(host: str, allowed: set[str]) -> bool:
    h = host.lower().rstrip(".")
    if h in allowed:
        return True
    for a in allowed:
        if h == a or h.endswith("." + a):
            return True
    return False


def load_allowlist(path: Path) -> tuple[set[str], set[str]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid allowlist YAML: {path}")
    hosts = {str(x).lower().strip() for x in (data.get("hosts") or []) if x}
    blocked = {str(x).lower().strip() for x in (data.get("blocked_hosts") or []) if x}
    return hosts, blocked


def _check_url(
    source: str,
    tag: str,
    attr: str,
    url: str,
    *,
    allowed: set[str],
    blocked: set[str],
    violations: list[str],
) -> None:
    if not url or not url.startswith(("http://", "https://")):
        return
    try:
        netloc = urlparse(url).netloc.split("@")[-1]
    except ValueError:
        violations.append(f"{source}: invalid URL {url!r}")
        return
    host = netloc.split(":")[0].lower()
    if not host:
        return
    if host in blocked or any(host == b or host.endswith("." + b) for b in blocked):
        violations.append(f"{source}: blocked host {host!r} in {tag} {attr}={url!r}")
        return
    if not _host_allowed(host, allowed):
        violations.append(f"{source}: non-allowlisted host {host!r} in {tag} {attr}={url!r}")


def scan_html_dir(site_dir: Path, *, allowed: set[str], blocked: set[str]) -> list[str]:
    violations: list[str] = []
    for html_path in sorted(site_dir.rglob("*.html")):
        if "/assets/" in str(html_path).replace("\\", "/") and "index.html" not in html_path.name:
            # Skip static asset HTML fragments if any; still scan index pages under assets
            pass
        try:
            raw = html_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            violations.append(f"{html_path}: read error {e}")
            continue
        soup = BeautifulSoup(raw, "html.parser")
        rel = html_path.relative_to(site_dir)

        for tag, attr in (
            ("script", "src"),
            ("link", "href"),
            ("img", "src"),
            ("iframe", "src"),
            ("source", "src"),
            ("video", "poster"),
            ("a", "href"),
        ):
            for el in soup.find_all(tag):
                val = el.get(attr)
                if val:
                    _check_url(str(rel), tag, attr, val.strip(), allowed=allowed, blocked=blocked, violations=violations)

        # Inline SVG xlink:href / href on <image> inside svg
        for el in soup.find_all(["image", "use"]):
            for a in ("href", "xlink:href"):
                val = el.get(a)
                if val:
                    _check_url(str(rel), el.name, a, val.strip(), allowed=allowed, blocked=blocked, violations=violations)

    return violations


def iter_pdf_uri_strings(reader: PdfReader) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for pi, page in enumerate(reader.pages):
        for ind in page.get("/Annots") or []:
            a = ind.get_object()
            if a.get("/Subtype") != "/Link":
                continue
            aa = a.get("/A")
            if not aa:
                continue
            ao = aa.get_object() if hasattr(aa, "get_object") else aa
            if not hasattr(ao, "get"):
                continue
            uri = ao.get("/URI")
            if uri:
                out.append((pi, str(uri)))
    return out


def scan_pdf(pdf_path: Path, *, allowed: set[str], blocked: set[str]) -> list[str]:
    violations: list[str] = []
    reader = PdfReader(str(pdf_path))
    for pi, uri in iter_pdf_uri_strings(reader):
        _check_url(f"{pdf_path.name}:page{pi}", "pdf", "URI", uri, allowed=allowed, blocked=blocked, violations=violations)
    return violations


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Check external resource hosts (Story 6.6).")
    p.add_argument("site_dir", type=Path, help="Built site directory (e.g. site/)")
    p.add_argument("pdf", type=Path, nargs="?", help="Learner PDF path")
    p.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    args = p.parse_args(argv)

    allowed, blocked = load_allowlist(args.allowlist)
    all_v: list[str] = []

    if args.site_dir.is_dir():
        all_v.extend(scan_html_dir(args.site_dir, allowed=allowed, blocked=blocked))
    else:
        print(f"check-external-resources: missing site dir {args.site_dir}", file=sys.stderr)
        return 1

    if args.pdf and args.pdf.is_file():
        all_v.extend(scan_pdf(args.pdf, allowed=allowed, blocked=blocked))
    elif args.pdf:
        print(f"check-external-resources: skip missing PDF {args.pdf}", file=sys.stderr)

    if all_v:
        print("External resource violations:", file=sys.stderr)
        for line in all_v:
            print(line, file=sys.stderr)
        return 1
    print("check-external-resources: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
