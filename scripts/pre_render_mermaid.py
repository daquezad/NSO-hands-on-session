#!/usr/bin/env python3
"""
Pre-render Mermaid sources to SVG + PNG under docs/assets/images/mermaid/ (AR11, Story 3.5).

Sources: docs/assets/mermaid-sources/<chapter>/<diagram-id>.mmd
Outputs: docs/assets/images/mermaid/<chapter>/<diagram-id>.{svg,png,alt.txt}

Requires @mermaid-js/mermaid-cli (`mmdc` or `npx @mermaid-js/mermaid-cli`).
Chromium/Puppeteer must be able to launch (not sandboxed in some CI — use a runner with a display or CI chrome).

Usage:
  python3 scripts/pre_render_mermaid.py [--check]
  --check   Exit 0 if mmdc unavailable (CI skip); else render and exit non-zero on failure.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
DOCS = _REPO / "docs"
SOURCES = DOCS / "assets" / "mermaid-sources"
OUT_ROOT = DOCS / "assets" / "images" / "mermaid"


def _which_mmdc() -> list[str] | None:
    mmdc = shutil.which("mmdc")
    if mmdc:
        return [mmdc]
    npx = shutil.which("npx")
    if npx:
        return [npx, "--yes", "@mermaid-js/mermaid-cli"]
    return None


def _run_mmdc(cmd_base: list[str], in_path: Path, out_path: Path, extra: list[str]) -> None:
    args = [*cmd_base, "-i", str(in_path), "-o", str(out_path), *extra]
    subprocess.run(args, check=True, cwd=str(_REPO))


def _read_alt(alt_path: Path) -> tuple[str, str]:
    text = alt_path.read_text(encoding="utf-8").strip()
    if not text:
        return "Topology", "Diagram"
    first = text.split(".")[0].strip()
    title = first[:120] if len(first) <= 120 else first[:117] + "…"
    return title, text


def _inject_svg_a11y(svg_path: Path, title: str, desc: str) -> None:
    raw = svg_path.read_text(encoding="utf-8")
    if "<title>" in raw.lower() and "<desc>" in raw.lower():
        return
    t = html.escape(title)
    d = html.escape(desc)
    block = f"<title>{t}</title><desc>{d}</desc>"
    m = re.match(r"(<svg\b[^>]*>)", raw, re.I)
    if not m:
        return
    insert_at = m.end()
    new_raw = raw[:insert_at] + block + raw[insert_at:]
    svg_path.write_text(new_raw, encoding="utf-8")


def render_one(mmd: Path, cmd_base: list[str]) -> None:
    rel = mmd.relative_to(SOURCES)
    out_dir = OUT_ROOT / rel.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = mmd.stem
    alt_src = mmd.with_suffix(".alt.txt")
    if not alt_src.is_file():
        raise FileNotFoundError(f"Missing alt file: {alt_src}")

    svg_out = out_dir / f"{stem}.svg"
    png_out = out_dir / f"{stem}.png"

    _run_mmdc(cmd_base, mmd, svg_out, ["-b", "transparent"])
    _run_mmdc(cmd_base, mmd, png_out, ["-b", "white", "-s", "2"])

    title, desc = _read_alt(alt_src)
    _inject_svg_a11y(svg_out, title, desc)

    alt_dst = out_dir / f"{stem}.alt.txt"
    shutil.copyfile(alt_src, alt_dst)


def main() -> int:
    ap = argparse.ArgumentParser(description="Pre-render Mermaid .mmd files to SVG/PNG.")
    ap.add_argument(
        "--check",
        action="store_true",
        help="If mmdc/npx unavailable, exit 0; otherwise render.",
    )
    args = ap.parse_args()

    if not SOURCES.is_dir():
        print("No mermaid-sources directory; nothing to do.", file=sys.stderr)
        return 0

    mmds = sorted(SOURCES.rglob("*.mmd"))
    if not mmds:
        print("No .mmd files under mermaid-sources.", file=sys.stderr)
        return 0

    cmd_base = _which_mmdc()
    if cmd_base is None:
        msg = "mmdc / npx not found — install Node or `@mermaid-js/mermaid-cli`."
        if args.check:
            print(msg, file=sys.stderr)
            return 0
        print(msg, file=sys.stderr)
        return 2

    for mmd in mmds:
        print(f"Rendering {mmd.relative_to(_REPO)} …")
        try:
            render_one(mmd, cmd_base)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: mmdc failed for {mmd}: {e}", file=sys.stderr)
            return 1
        except OSError as e:
            print(f"ERROR: {mmd}: {e}", file=sys.stderr)
            return 1

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
