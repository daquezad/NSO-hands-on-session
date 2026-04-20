#!/usr/bin/env python3
"""
FR37 — scan the built learner site for instructor-only leakage markers (Story 5.6).
Story 6.2 — optional `--pdf` scans the learner PDF text layer with the same pattern set.

HTML path: stdlib + re only. PDF path: requires `pypdf` (see requirements.txt).

Exit 0 = clean, 1 = script error, 2 = leakage found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_SCRIPT_ERROR = 1
EXIT_LEAK = 2

# Strip fenced / inline code so authoring tables that *document* paths do not false-positive.
_CODE_BLOCK = re.compile(r"<code\b[^>]*>.*?</code>", re.DOTALL | re.IGNORECASE)
_PRE_BLOCK = re.compile(r"<pre\b[^>]*>.*?</pre>", re.DOTALL | re.IGNORECASE)

# Allow-listed leakage markers (epic 5.6) + Story 5.3 data attribute.
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("css_class_instructor_notes", re.compile(r"\binstructor-notes(?:--[\w-]+)?\b")),
    ("data_instructor_block", re.compile(r"data-instructor-block\s*=")),
    ("html_comment_instructor_only", re.compile(r"<!--\s*instructor-only\s*-->")),
    ("path_instructor_artifacts", re.compile(r"instructor-artifacts/")),
    # Companion / URL slug (does not match `instructor-notes--*` BEM modifiers — see tests).
    ("slug_instructor_notes", re.compile(r"-instructor-notes")),
    ("heading_instructor_notes", re.compile(r"<h[1-6][^>]*>[^<]{0,200}Instructor\s+notes", re.IGNORECASE)),
)


def _strip_code_regions(html: str) -> str:
    s = _CODE_BLOCK.sub(" ", html)
    return _PRE_BLOCK.sub(" ", s)


def _scan_pdf_text(text: str, page_1based: int) -> list[tuple[str, int, str]]:
    """Scan plain text (PDF extraction); line numbers approximate to page number."""
    hits: list[tuple[str, int, str]] = []
    for name, rx in _PATTERNS:
        for m in rx.finditer(text):
            snippet = m.group(0).strip()
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            hits.append((name, page_1based, snippet))
    return hits


def _scan_file(path: Path) -> list[tuple[str, int, str]]:
    """Return list of (pattern_name, line_no, snippet)."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"check_instructor_leak.py: cannot read {path}: {e}", file=sys.stderr)
        raise
    text = _strip_code_regions(raw)
    hits: list[tuple[str, int, str]] = []
    for name, rx in _PATTERNS:
        for m in rx.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            snippet = m.group(0).strip()
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            hits.append((name, line_no, snippet))
    return hits


def _validate_root(path: Path) -> Path:
    root = path.expanduser().resolve(strict=False)
    if not root.exists():
        print(f"check_instructor_leak.py: path does not exist: {path}", file=sys.stderr)
        sys.exit(EXIT_SCRIPT_ERROR)
    if not root.is_dir():
        print(f"check_instructor_leak.py: not a directory: {root}", file=sys.stderr)
        sys.exit(EXIT_SCRIPT_ERROR)
    return root


def _scan_pdf(path: Path) -> list[tuple[str, int, str]]:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("check_instructor_leak.py: PDF mode requires pypdf (pip install pypdf)", file=sys.stderr)
        sys.exit(EXIT_SCRIPT_ERROR)

    path = path.expanduser().resolve()
    if not path.is_file():
        print(f"check_instructor_leak.py: PDF not found: {path}", file=sys.stderr)
        sys.exit(EXIT_SCRIPT_ERROR)

    reader = PdfReader(str(path))
    all_hits: list[tuple[str, int, str]] = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        for name, line_no, snippet in _scan_pdf_text(text, i + 1):
            all_hits.append((name, line_no, snippet))
    return all_hits


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Fail if the learner HTML tree (or PDF text) contains instructor-only leakage markers (FR37)."
    )
    p.add_argument(
        "site_dir",
        nargs="?",
        default="site",
        help="Built learner site root (default: site); ignored when --pdf is set",
    )
    p.add_argument(
        "--pdf",
        metavar="FILE",
        default="",
        help="If set, scan this PDF's text layer instead of HTML under site_dir (Story 6.2)",
    )
    args = p.parse_args(argv)

    if args.pdf:
        leaked = False
        for name, page_no, snippet in _scan_pdf(Path(args.pdf)):
            leaked = True
            print(f"LEAK {name}: pdf:page{page_no}: {snippet!r}", file=sys.stderr)
        if leaked:
            print(
                "check_instructor_leak.py: instructor-only markers found in PDF text (exit 2).",
                file=sys.stderr,
            )
            sys.exit(EXIT_LEAK)
        print(f"check_instructor_leak.py: {args.pdf} — no PDF text leakage detected")
        return EXIT_OK

    root = _validate_root(Path(args.site_dir))

    html_files = sorted(root.rglob("*.html"))
    if not html_files:
        print("check_instructor_leak.py: no HTML files under site root", file=sys.stderr)
        sys.exit(EXIT_SCRIPT_ERROR)

    leaked = False
    try:
        for hf in html_files:
            rel = hf.relative_to(root)
            for name, line_no, snippet in _scan_file(hf):
                leaked = True
                print(
                    f"LEAK {name}: {rel}:{line_no}: {snippet!r}",
                    file=sys.stderr,
                )
    except OSError:
        sys.exit(EXIT_SCRIPT_ERROR)

    if leaked:
        print(
            "check_instructor_leak.py: instructor-only content detected in learner site (exit 2).",
            file=sys.stderr,
        )
        sys.exit(EXIT_LEAK)

    print(f"check_instructor_leak.py: {root.name}/ — no leakage detected")
    return EXIT_OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(EXIT_SCRIPT_ERROR) from None
