#!/usr/bin/env python3
"""Print canonical NSO version for Make / docs (Story 6.2 — `_data/versions.yaml` with mkdocs.yml fallback)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    vf = root / "_data" / "versions.yaml"
    if vf.is_file():
        data = yaml.safe_load(vf.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("nso_version"):
            print(str(data["nso_version"]).strip())
            return
    mk = (root / "mkdocs.yml").read_text(encoding="utf-8")
    m = re.search(r"nso_version:\s*[\"']?([^\"'\\s]+)", mk)
    if m:
        print(m.group(1).strip())
        return
    print("unknown", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
