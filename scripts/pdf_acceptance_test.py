#!/usr/bin/env python3
"""
Story 6.2 — Compare regenerated spike-corpus Chromium PDF to tests/fixtures/pdf/acceptance-baseline.pdf (AC4).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE = REPO_ROOT / "tests" / "fixtures" / "pdf" / "acceptance-baseline.pdf"
SPIKE_HTML = REPO_ROOT / "scripts" / "spike" / "spike-corpus.html"


def find_chrome() -> str | None:
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        p = shutil.which(name)
        if p:
            return p
    mac = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if mac.is_file():
        return str(mac)
    return None


def main() -> int:
    if not BASELINE.is_file():
        print(f"pdf_acceptance_test: missing baseline {BASELINE}", file=sys.stderr)
        return 1
    if not SPIKE_HTML.is_file():
        print(f"pdf_acceptance_test: missing spike HTML {SPIKE_HTML}", file=sys.stderr)
        return 1
    chrome = find_chrome()
    if not chrome:
        print("pdf_acceptance_test: Chromium/Chrome not found — install Chrome for this check.", file=sys.stderr)
        return 1

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        fresh = Path(tmp.name)
    try:
        url = SPIKE_HTML.resolve().as_uri()
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={fresh}",
            url,
        ]
        r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr or r.stdout, file=sys.stderr)
            return 1
        if not fresh.is_file() or fresh.stat().st_size == 0:
            print("pdf_acceptance_test: Chromium produced empty PDF", file=sys.stderr)
            return 1

        b_reader = PdfReader(str(BASELINE))
        f_reader = PdfReader(str(fresh))
        bp = len(b_reader.pages)
        fp = len(f_reader.pages)
        if bp != fp:
            print(
                f"pdf_acceptance_test: page count mismatch baseline={bp} fresh={fp}",
                file=sys.stderr,
            )
            return 1
        print(f"pdf_acceptance_test: OK — spike corpus PDF page count matches baseline ({fp} page(s))")
        return 0
    finally:
        fresh.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
