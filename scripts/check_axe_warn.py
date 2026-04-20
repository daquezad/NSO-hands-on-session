#!/usr/bin/env python3
"""
NFR-A8 — run axe-core CLI against key URLs; emit GitHub warnings if violation count exceeds
committed baseline. Always exits 0 (warn-only gate in Story 3.11).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "scripts" / "ci" / "a11y_baseline.yaml"
_AXE_LOCAL = ROOT / "node_modules" / ".bin" / "axe"


def _count_violations(report: object) -> int:
    if isinstance(report, dict):
        v = report.get("violations")
        if isinstance(v, list):
            return len(v)
    if isinstance(report, list):
        return len(report)
    return 0


def _page_url(base_url: str, url_path: str) -> str:
    b = base_url.rstrip("/")
    if url_path in ("/", ""):
        return b + "/"
    p = url_path if url_path.startswith("/") else "/" + url_path
    return b + p


def _run_axe(base_url: str, url_path: str, axe_cmd: list[str]) -> tuple[int, str]:
    u = _page_url(base_url, url_path)
    cmd = axe_cmd + [u, "--stdout", "--timeout", "120000"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    out = (r.stdout or "").strip()
    if r.returncode != 0 and not out:
        return -1, (r.stderr or "axe failed")[:2000]
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return -1, f"invalid JSON from axe (first 500 chars): {out[:500]!r}"
    return _count_violations(data), ""


def main() -> int:
    base = os.environ.get("QUALITY_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    if _AXE_LOCAL.is_file():
        axe_cmd = [str(_AXE_LOCAL)]
    else:
        axe_cmd = ["npx", "--yes", "@axe-core/cli@4.10.2"]

    pages = [
        ("/", "home"),
        ("/01-connect-workstation/", "lab1"),
        ("/08-create-service/", "lab8"),
    ]

    maxv: dict[str, int] = {}
    if BASELINE.is_file() and yaml is not None:
        raw = yaml.safe_load(BASELINE.read_text(encoding="utf-8")) or {}
        maxv = dict(raw.get("violations_max") or {})

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    summary_lines: list[str] = ["### Axe (warn-only, Story 3.11)\n"]

    for path, key in pages:
        n, err = _run_axe(base, path, axe_cmd)
        label = f"{path} ({key})"
        if n < 0:
            print(f"::warning::axe could not run for {label}: {err}")
            summary_lines.append(f"- **{label}**: error — {err[:200]}\n")
            continue
        ceiling = maxv.get(key, maxv.get(path, 999))
        summary_lines.append(f"- **{label}**: {n} violations (ceiling {ceiling})\n")
        print(f"axe {label}: {n} violations (ceiling {ceiling})")
        if n > ceiling:
            print(
                f"::warning::Axe violations on {label}: {n} > baseline ceiling {ceiling}. "
                "Update scripts/ci/a11y_baseline.yaml after fixing or accepting."
            )

    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.writelines(summary_lines)
        except OSError:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
