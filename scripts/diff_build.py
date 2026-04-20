#!/usr/bin/env python3
"""Structural diff helper for two MkDocs `site/` build outputs.

Purpose
-------
Story 1.2 / NFR-R1 / FR35: two builds of the same commit SHA 24 hours apart
must produce structurally-identical site artifacts. This script compares two
build directory trees and exits 0 when they are structurally identical
modulo a documented allow-list of known non-determinism sources.

Allow-listed (known) non-determinism sources
--------------------------------------------
1. File mtimes — filesystem timestamps (compared as content, not metadata,
   so mtimes are inherently ignored by sha256-of-contents).
2. ``sitemap.xml`` and ``sitemap.xml.gz`` ``<lastmod>`` element text —
   MkDocs writes a fresh timestamp on every build. For the gzipped variant,
   gzip metadata timestamps are ignored by comparing decompressed XML.
3. ``site/search/search_index.json`` field/key ordering — MkDocs uses dict
   insertion order; the *contents* must match, only key order may differ.
4. HTML comment whitespace variations within ``<head>`` where Material may
   inject build-time data. Specifically: HTML comments that match the
   pattern ``<!--\\s*(.*?)\\s*-->`` are normalized to
   ``<!-- <collapsed-content> -->`` before comparison. Normalization is
   applied only to the ``<head>`` section.

Anything not in this allow-list is compared by ``sha256(file_contents)`` and
reported as DIVERGED on mismatch.

CLI usage
---------
    python scripts/diff_build.py [--help] <dir_a> <dir_b>

Exit codes
----------
    0 — structurally identical (allow-list applied)
    1 — divergence detected outside the allow-list
    2 — usage error (missing/invalid arguments, unreadable directories)

Stdlib-only by design (Story 1.2 AC8 forbids new deps): ``os``, ``sys``,
``pathlib``, ``hashlib``, ``gzip``, ``argparse``, ``json``, ``re``, and
``xml.etree.ElementTree``.

Security note (codeguard-0-xml-and-serialization)
-------------------------------------------------
``xml.etree.ElementTree`` is used here to parse ``sitemap.xml`` files
produced by MkDocs itself from controlled inputs (the contents of
``mkdocs.yml`` and the project's own Markdown files). MkDocs' sitemap
output does not contain DOCTYPE declarations or external entity references,
so XXE / billion-laughs exposure for this specific use case is not a
practical risk.

**However**, if this script is ever extended to parse XML from an external
or untrusted source, migrate to ``defusedxml.ElementTree`` (drop-in
replacement) before merging that change. Treat that as a hard requirement;
``defusedxml`` disables DTDs and external entities by default and is the
correct posture for any XML input that is not 100% under our control.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET  # noqa: N817 - stdlib alias is conventional
from pathlib import Path

EXIT_OK = 0
EXIT_DIVERGED = 1
EXIT_USAGE = 2

SITEMAP_NAMES = {"sitemap.xml"}
SITEMAP_GZ_NAMES = {"sitemap.xml.gz"}
SEARCH_INDEX_RELATIVE = Path("search") / "search_index.json"
HTML_SUFFIXES = {".html", ".htm"}

_HTML_COMMENT_RE = re.compile(rb"<!--\s*(.*?)\s*-->", re.DOTALL)
_HTML_HEAD_RE = re.compile(rb"(<head\b[^>]*>)(.*?)(</head>)", re.IGNORECASE | re.DOTALL)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_html_head_comments(data: bytes) -> bytes:
    """Collapse comment whitespace to a single space inside ``<head>`` only.

    Material may emit ``<!--   foo   -->`` vs ``<!-- foo -->`` between
    builds. We keep the comment delimiter visible so that *removing* a
    comment is still detected as a divergence.
    """
    def normalize_comment(match: re.Match[bytes]) -> bytes:
        collapsed = b" ".join(match.group(1).split())
        return b"<!-- " + collapsed + b" -->"

    def normalize_head(match: re.Match[bytes]) -> bytes:
        return (
            match.group(1)
            + _HTML_COMMENT_RE.sub(normalize_comment, match.group(2))
            + match.group(3)
        )

    return _HTML_HEAD_RE.sub(normalize_head, data, count=1)


def _compare_html(path_a: Path, path_b: Path) -> bool:
    """Return True when two HTML files are equal after head-comment normalization."""
    a = _normalize_html_head_comments(path_a.read_bytes())
    b = _normalize_html_head_comments(path_b.read_bytes())
    return _sha256_bytes(a) == _sha256_bytes(b)


def _compare_sitemap_xml(path_a: Path, path_b: Path) -> bool:
    """Compare two ``sitemap.xml`` files ignoring ``<lastmod>`` text content.

    Structure (element tree, tags, attributes, and all non-``lastmod`` text)
    must match. ``<lastmod>`` text is intentionally ignored because MkDocs
    stamps it with build time on every run.
    """
    try:
        tree_a = ET.parse(str(path_a))
        tree_b = ET.parse(str(path_b))
    except ET.ParseError:
        # If either file is unparseable, fall back to byte-equal sha256 so
        # we surface the corruption instead of silently passing.
        return _sha256_file(path_a) == _sha256_file(path_b)

    return _xml_equal_ignoring_lastmod(tree_a.getroot(), tree_b.getroot())


def _compare_sitemap_xml_gz(path_a: Path, path_b: Path) -> bool:
    """Compare gzipped sitemap XML files ignoring gzip mtime and ``<lastmod>``."""
    try:
        with gzip.open(path_a, "rb") as fh_a:
            raw_a = fh_a.read()
        with gzip.open(path_b, "rb") as fh_b:
            raw_b = fh_b.read()
    except (OSError, EOFError):
        return _sha256_file(path_a) == _sha256_file(path_b)

    try:
        root_a = ET.fromstring(raw_a)
        root_b = ET.fromstring(raw_b)
    except ET.ParseError:
        return _sha256_bytes(raw_a) == _sha256_bytes(raw_b)

    return _xml_equal_ignoring_lastmod(root_a, root_b)


def _xml_equal_ignoring_lastmod(node_a: ET.Element, node_b: ET.Element) -> bool:
    if _local_tag(node_a.tag) != _local_tag(node_b.tag):
        return False
    if node_a.attrib != node_b.attrib:
        return False

    if _local_tag(node_a.tag) != "lastmod":
        if (node_a.text or "").strip() != (node_b.text or "").strip():
            return False

    if (node_a.tail or "").strip() != (node_b.tail or "").strip():
        return False

    children_a = _children_for_compare(node_a)
    children_b = _children_for_compare(node_b)
    if len(children_a) != len(children_b):
        return False
    return all(
        _xml_equal_ignoring_lastmod(ca, cb)
        for ca, cb in zip(children_a, children_b)
    )


def _local_tag(tag: str) -> str:
    """Strip XML namespace prefix from an ElementTree tag."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _children_for_compare(node: ET.Element) -> list[ET.Element]:
    """Return children in deterministic order for XML comparison.

    Sitemap ``urlset`` entries are sorted by ``<loc>`` text so URL ordering
    differences do not trigger false divergences.
    """
    children = list(node)
    if _local_tag(node.tag) != "urlset":
        return children

    def sitemap_sort_key(child: ET.Element) -> tuple[str, str]:
        if _local_tag(child.tag) != "url":
            return ("", _local_tag(child.tag))
        loc_text = ""
        for grandchild in child:
            if _local_tag(grandchild.tag) == "loc":
                loc_text = (grandchild.text or "").strip()
                break
        return (loc_text, "url")

    return sorted(children, key=sitemap_sort_key)


def _compare_search_index(path_a: Path, path_b: Path) -> bool:
    """Compare two ``search_index.json`` files ignoring key/insertion order.

    json.loads + deep equality on the resulting dict/list trees compares
    by value, not by key order, satisfying AC5 item 3.
    """
    try:
        data_a = json.loads(path_a.read_text(encoding="utf-8"))
        data_b = json.loads(path_b.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _sha256_file(path_a) == _sha256_file(path_b)
    return data_a == data_b


def _classify(rel: Path) -> str:
    """Return the comparator key for a given relative path inside the build."""
    name = rel.name
    if name in SITEMAP_NAMES:
        return "sitemap"
    if name in SITEMAP_GZ_NAMES:
        return "sitemap_gz"
    if rel == SEARCH_INDEX_RELATIVE or rel.as_posix().endswith(
        SEARCH_INDEX_RELATIVE.as_posix()
    ):
        return "search_index"
    if rel.suffix.lower() in HTML_SUFFIXES:
        return "html"
    return "default"


def _walk_files(root: Path) -> set[Path]:
    files: set[Path] = set()
    for path in root.rglob("*"):
        if path.is_file():
            files.add(path.relative_to(root))
    return files


def _compare_one(rel: Path, full_a: Path, full_b: Path) -> tuple[str, str]:
    """Return (status, reason) for a single relative path."""
    kind = _classify(rel)
    if kind == "sitemap":
        ok = _compare_sitemap_xml(full_a, full_b)
        return ("ALLOWED", "sitemap.xml lastmod normalized") if ok else (
            "DIVERGED",
            "sitemap.xml structure differs beyond lastmod",
        )
    if kind == "sitemap_gz":
        ok = _compare_sitemap_xml_gz(full_a, full_b)
        return ("ALLOWED", "sitemap.xml.gz normalized (gzip mtime + lastmod)") if ok else (
            "DIVERGED",
            "sitemap.xml.gz structure differs beyond normalized fields",
        )
    if kind == "search_index":
        ok = _compare_search_index(full_a, full_b)
        return ("ALLOWED", "search_index.json key order normalized") if ok else (
            "DIVERGED",
            "search_index.json contents differ",
        )
    if kind == "html":
        ok = _compare_html(full_a, full_b)
        return ("ALLOWED", "<head> comment whitespace normalized") if ok else (
            "DIVERGED",
            "HTML contents differ after comment normalization",
        )
    ok = _sha256_file(full_a) == _sha256_file(full_b)
    return ("IDENTICAL", "sha256 match") if ok else ("DIVERGED", "sha256 mismatch")


def _run_self_test() -> int:
    """Minimal in-process self-test of allow-list comparators (AC5 'good practice')."""
    import tempfile

    failures: list[str] = []

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # search_index.json key order independence
        a = td_path / "a.json"
        b = td_path / "b.json"
        a.write_text(json.dumps({"x": 1, "y": 2}), encoding="utf-8")
        b.write_text(json.dumps({"y": 2, "x": 1}), encoding="utf-8")
        if not _compare_search_index(a, b):
            failures.append("search_index key-order independence failed")

        c = td_path / "c.json"
        c.write_text(json.dumps({"x": 1, "y": 99}), encoding="utf-8")
        if _compare_search_index(a, c):
            failures.append("search_index value-difference not detected")

        # sitemap.xml lastmod ignored
        sitemap_a = td_path / "sitemap_a.xml"
        sitemap_b = td_path / "sitemap_b.xml"
        sitemap_a.write_text(
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
            "<url><loc>https://example.test/</loc>"
            "<lastmod>2026-04-17</lastmod></url></urlset>",
            encoding="utf-8",
        )
        sitemap_b.write_text(
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
            "<url><loc>https://example.test/</loc>"
            "<lastmod>2099-01-01</lastmod></url></urlset>",
            encoding="utf-8",
        )
        if not _compare_sitemap_xml(sitemap_a, sitemap_b):
            failures.append("sitemap lastmod-ignored comparison failed")

        # sitemap URL order independence
        sitemap_c = td_path / "sitemap_c.xml"
        sitemap_c.write_text(
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
            "<url><loc>https://example.test/second</loc><lastmod>2030-01-01</lastmod></url>"
            "<url><loc>https://example.test/</loc><lastmod>2030-01-01</lastmod></url>"
            "</urlset>",
            encoding="utf-8",
        )
        sitemap_d = td_path / "sitemap_d.xml"
        sitemap_d.write_text(
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
            "<url><loc>https://example.test/</loc><lastmod>2026-04-17</lastmod></url>"
            "<url><loc>https://example.test/second</loc><lastmod>2026-04-17</lastmod></url>"
            "</urlset>",
            encoding="utf-8",
        )
        if not _compare_sitemap_xml(sitemap_c, sitemap_d):
            failures.append("sitemap url-order independence failed")

        # sitemap structural diff still detected
        sitemap_e = td_path / "sitemap_e.xml"
        sitemap_e.write_text(
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
            "<url><loc>https://example.test/changed</loc>"
            "<lastmod>2026-04-17</lastmod></url></urlset>",
            encoding="utf-8",
        )
        if _compare_sitemap_xml(sitemap_a, sitemap_e):
            failures.append("sitemap structural-diff not detected")

        # sitemap.xml.gz gzip mtime + lastmod normalization
        sitemap_gz_a = td_path / "sitemap_a.xml.gz"
        sitemap_gz_b = td_path / "sitemap_b.xml.gz"
        raw_sitemap_a = (
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
            "<url><loc>https://example.test/</loc><lastmod>2026-04-17</lastmod></url>"
            "</urlset>"
        )
        raw_sitemap_b = (
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
            "<url><loc>https://example.test/</loc><lastmod>2099-01-01</lastmod></url>"
            "</urlset>"
        )
        with gzip.GzipFile(filename="", mode="wb", fileobj=sitemap_gz_a.open("wb"), mtime=1) as fh:
            fh.write(raw_sitemap_a.encode("utf-8"))
        with gzip.GzipFile(filename="", mode="wb", fileobj=sitemap_gz_b.open("wb"), mtime=2) as fh:
            fh.write(raw_sitemap_b.encode("utf-8"))
        if not _compare_sitemap_xml_gz(sitemap_gz_a, sitemap_gz_b):
            failures.append("sitemap.xml.gz normalization failed")

        # html head-comment whitespace normalization
        html_a = td_path / "a.html"
        html_b = td_path / "b.html"
        html_a.write_bytes(b"<html><head><!--   built   --></head></html>")
        html_b.write_bytes(b"<html><head><!-- built --></head></html>")
        if not _compare_html(html_a, html_b):
            failures.append("html comment-whitespace normalization failed")

        # html semantic difference still detected
        html_c = td_path / "c.html"
        html_c.write_bytes(b"<html><head><!-- different --></head></html>")
        if _compare_html(html_a, html_c):
            failures.append("html content-difference not detected")

        # body comments are not normalized (head-only scope)
        html_d = td_path / "d.html"
        html_e = td_path / "e.html"
        html_d.write_bytes(b"<html><body><!--   body note --></body></html>")
        html_e.write_bytes(b"<html><body><!-- body note --></body></html>")
        if _compare_html(html_d, html_e):
            failures.append("body comment normalization incorrectly applied")

    if failures:
        for f in failures:
            print(f"SELFTEST FAIL: {f}", file=sys.stderr)
        return EXIT_DIVERGED
    print("SELFTEST OK: 9 comparator assertions passed")
    return EXIT_OK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diff_build.py",
        description=(
            "Structural diff for two MkDocs `site/` build outputs. "
            "Exits 0 when the two trees are equivalent modulo the documented "
            "allow-list of known non-determinism sources (mtimes, sitemap "
            "lastmod + sitemap.xml.gz gzip timestamps, search_index key order, "
            "HTML head-comment whitespace)."
        ),
    )
    parser.add_argument(
        "dir_a",
        nargs="?",
        help="First build directory (e.g., /tmp/build_a).",
    )
    parser.add_argument(
        "dir_b",
        nargs="?",
        help="Second build directory (e.g., /tmp/build_b).",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run in-process comparator self-tests and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.self_test:
        return _run_self_test()

    if not args.dir_a or not args.dir_b:
        parser.print_usage(sys.stderr)
        print(
            "diff_build.py: error: <dir_a> and <dir_b> are required (or use --self-test)",
            file=sys.stderr,
        )
        return EXIT_USAGE

    dir_a = Path(args.dir_a)
    dir_b = Path(args.dir_b)
    for d in (dir_a, dir_b):
        if not d.is_dir():
            print(f"diff_build.py: error: not a directory: {d}", file=sys.stderr)
            return EXIT_USAGE

    files_a = _walk_files(dir_a)
    files_b = _walk_files(dir_b)

    only_in_a = sorted(files_a - files_b)
    only_in_b = sorted(files_b - files_a)
    in_both = sorted(files_a & files_b)

    diverged: list[tuple[Path, str]] = []
    for rel in in_both:
        status, reason = _compare_one(rel, dir_a / rel, dir_b / rel)
        if status == "DIVERGED":
            diverged.append((rel, reason))
            print(f"DIVERGED  {rel}  ({reason})")
        elif status == "ALLOWED":
            print(f"ALLOWED   {rel}  ({reason})")
        else:
            print(f"IDENTICAL {rel}")

    for rel in only_in_a:
        print(f"DIVERGED  {rel}  (only in {dir_a})")
    for rel in only_in_b:
        print(f"DIVERGED  {rel}  (only in {dir_b})")

    total_divergences = len(diverged) + len(only_in_a) + len(only_in_b)
    if total_divergences:
        print(
            f"\nFAIL: {total_divergences} divergence(s) outside the allow-list.",
            file=sys.stderr,
        )
        return EXIT_DIVERGED

    print(f"\nOK: {len(in_both)} file(s) compared, all structurally identical.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
