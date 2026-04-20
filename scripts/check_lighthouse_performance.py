#!/usr/bin/env python3
"""
NFR-P7 — fail if Lighthouse performance category score < threshold (default 0.9).
Logs LCP / CLS / INP (or TBT as proxy) to stdout for CI artifact review (NFR-P1–P4 informational).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _audit_num(report: dict, audit_id: str) -> str:
    audits = report.get("audits") or {}
    a = audits.get(audit_id) or {}
    v = a.get("numericValue")
    disp = a.get("displayValue")
    if disp:
        return str(disp)
    if v is not None:
        return f"{v:.2f}"
    return "—"


def main() -> int:
    p = argparse.ArgumentParser(description="Check Lighthouse performance JSON reports.")
    p.add_argument("reports", nargs="+", type=Path, help="Lighthouse JSON output files")
    p.add_argument("--min-score", type=float, default=0.9, help="Minimum performance score (0–1)")
    args = p.parse_args()

    failed = False
    for path in args.reports:
        if not path.is_file():
            print(f"ERROR: missing report: {path}", file=sys.stderr)
            failed = True
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        cat = (data.get("categories") or {}).get("performance") or {}
        score = cat.get("score")
        if score is None:
            print(f"ERROR: {path}: no performance score", file=sys.stderr)
            failed = True
            continue
        label = path.stem
        block = [
            f"#### Lighthouse — {label}\n",
            f"- Performance score: **{score:.4f}** (min {args.min_score})\n",
            f"- LCP: {_audit_num(data, 'largest-contentful-paint')}\n",
            f"- CLS: {_audit_num(data, 'cumulative-layout-shift')}\n",
            f"- TBT: {_audit_num(data, 'total-blocking-time')}\n",
            f"- Speed Index: {_audit_num(data, 'speed-index')}\n",
        ]
        print(f"--- {label} ---")
        print(f"  performance score: {score:.4f} (min {args.min_score})")
        print(f"  LCP: {_audit_num(data, 'largest-contentful-paint')}")
        print(f"  CLS: {_audit_num(data, 'cumulative-layout-shift')}")
        print(f"  TBT: {_audit_num(data, 'total-blocking-time')}")
        print(f"  Speed Index: {_audit_num(data, 'speed-index')}")
        gs = os.environ.get("GITHUB_STEP_SUMMARY")
        if gs:
            try:
                with open(gs, "a", encoding="utf-8") as f:
                    f.writelines(block + ["\n"])
            except OSError:
                pass
        if score < args.min_score:
            print(f"ERROR: {path}: performance {score:.4f} < {args.min_score}", file=sys.stderr)
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
