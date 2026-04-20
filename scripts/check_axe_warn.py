#!/usr/bin/env python3
"""
NFR-A8 / Story 6.10 — run axe-core CLI against URLs from scripts/ci/axe-pages.yaml.

- AXE_MODE=warn (default): compare violation counts to a11y_baseline.yaml; always exit 0.
- AXE_MODE=fail: exit non-zero if any violation has impact serious or critical.
Writes merged JSON report (axe-report-{GITHUB_RUN_ID}.json when GITHUB_RUN_ID is set).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "scripts" / "ci" / "a11y_baseline.yaml"
PAGES_YAML = ROOT / "scripts" / "ci" / "axe-pages.yaml"
_AXE_LOCAL = ROOT / "node_modules" / ".bin" / "axe"


def _count_violations(report: object) -> int:
    if isinstance(report, dict):
        v = report.get("violations")
        if isinstance(v, list):
            return len(v)
    if isinstance(report, list):
        return len(report)
    return 0


def _serious_critical_count(report: object) -> int:
    if not isinstance(report, dict):
        return 0
    viol = report.get("violations")
    if not isinstance(viol, list):
        return 0
    n = 0
    for item in viol:
        if isinstance(item, dict) and item.get("impact") in ("critical", "serious"):
            n += 1
    return n


def _page_url(base_url: str, url_path: str) -> str:
    b = base_url.rstrip("/")
    if url_path in ("/", ""):
        return b + "/"
    p = url_path if url_path.startswith("/") else "/" + url_path
    return b + p


def _run_axe(base_url: str, url_path: str, axe_cmd: list[str]) -> tuple[dict[str, Any] | None, str]:
    u = _page_url(base_url, url_path)
    cmd = axe_cmd + [u, "--stdout", "--timeout", "120000"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    out = (r.stdout or "").strip()
    if r.returncode != 0 and not out:
        return None, (r.stderr or "axe failed")[:2000]
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None, f"invalid JSON from axe (first 500 chars): {out[:500]!r}"
    if not isinstance(data, dict):
        return None, f"unexpected axe JSON type: {type(data).__name__}"
    return data, ""


def _load_pages() -> list[tuple[str, str]]:
    if yaml is not None and PAGES_YAML.is_file():
        raw = yaml.safe_load(PAGES_YAML.read_text(encoding="utf-8")) or {}
        pages_raw = raw.get("pages") or []
        out: list[tuple[str, str]] = []
        for p in pages_raw:
            if not isinstance(p, dict):
                continue
            path = p.get("path")
            key = p.get("key") or path
            if isinstance(path, str):
                out.append((path, str(key)))
        if out:
            return out
    return [
        ("/", "home"),
        ("/01-connect-workstation/", "lab1"),
        ("/08-create-service/", "lab8"),
    ]


def _report_path() -> Path:
    p = os.environ.get("AXE_REPORT_PATH", "").strip()
    if p:
        return Path(p)
    rid = os.environ.get("GITHUB_RUN_ID", "").strip()
    name = f"axe-report-{rid}.json" if rid else "axe-report.json"
    return ROOT / name


def main() -> int:
    base = os.environ.get("QUALITY_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    mode = (os.environ.get("AXE_MODE") or "warn").strip().lower()
    if mode not in ("warn", "fail"):
        print(f"::error::AXE_MODE must be warn or fail, got {mode!r}", file=sys.stderr)
        return 2

    if _AXE_LOCAL.is_file():
        axe_cmd = [str(_AXE_LOCAL)]
    else:
        axe_cmd = ["npx", "--yes", "@axe-core/cli@4.10.2"]

    pages = _load_pages()

    maxv: dict[str, int] = {}
    if BASELINE.is_file() and yaml is not None:
        raw = yaml.safe_load(BASELINE.read_text(encoding="utf-8")) or {}
        maxv = dict(raw.get("violations_max") or {})

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    title = "### Axe (Story 6.10)\n"
    if mode == "fail":
        title += f"- **Mode:** `fail` (serious/critical block merge)\n"
    else:
        title += f"- **Mode:** `warn` (baseline ceilings only; exit 0)\n"
    summary_lines: list[str] = [title]

    merged: dict[str, Any] = {
        "meta": {
            "axe_mode": mode,
            "quality_base_url": base,
            "pages_file": str(PAGES_YAML.relative_to(ROOT)) if PAGES_YAML.is_file() else None,
        },
        "pages": [],
        "totals": {"violations": 0, "serious_or_critical": 0},
    }

    total_sc = 0
    total_v = 0
    any_axe_error = False

    for path, key in pages:
        report, err = _run_axe(base, path, axe_cmd)
        label = f"{path} ({key})"
        n = _count_violations(report) if report is not None else -1
        sc = _serious_critical_count(report) if report is not None else 0

        if report is None:
            any_axe_error = True
            print(f"::warning::axe could not run for {label}: {err}")
            summary_lines.append(f"- **{label}**: error — {err[:200]}\n")
            merged["pages"].append(
                {
                    "path": path,
                    "key": key,
                    "error": err,
                    "violation_count": None,
                    "serious_or_critical": None,
                    "report": None,
                }
            )
            continue

        total_v += n
        total_sc += sc
        ceiling = maxv.get(key, maxv.get(path, 999))
        summary_lines.append(
            f"- **{label}**: {n} violations, {sc} serious/critical (ceiling {ceiling})\n"
        )
        print(f"axe {label}: {n} violations, {sc} serious/critical (ceiling {ceiling})")
        if mode == "warn" and n > ceiling:
            print(
                f"::warning::Axe violations on {label}: {n} > baseline ceiling {ceiling}. "
                "Update scripts/ci/a11y_baseline.yaml after fixing or accepting."
            )
        if mode == "fail" and sc > 0:
            print(
                f"::error::Axe serious/critical on {label}: {sc}. "
                "Fix or document exception; see docs/_internal/accessibility.md."
            )

        merged["pages"].append(
            {
                "path": path,
                "key": key,
                "violation_count": n,
                "serious_or_critical": sc,
                "report": report,
            }
        )

    merged["totals"]["violations"] = total_v
    merged["totals"]["serious_or_critical"] = total_sc

    out_path = _report_path()
    try:
        out_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
        print(f"Wrote merged axe report: {out_path}")
    except OSError as e:
        print(f"::warning::Could not write axe report {out_path}: {e}")

    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.writelines(summary_lines)
        except OSError:
            pass

    if mode == "fail":
        if any_axe_error:
            print("::error::AXE_MODE=fail: one or more pages failed axe (parse/run).")
            return 1
        if total_sc > 0:
            print("::error::AXE_MODE=fail: serious/critical violations present.")
            return 1
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
