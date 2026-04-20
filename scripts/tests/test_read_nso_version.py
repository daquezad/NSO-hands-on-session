"""Smoke tests for scripts/read_nso_version.py (Story 6.2)."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


class TestReadNsoVersion(unittest.TestCase):
    def test_script_prints_version(self) -> None:
        out = subprocess.check_output(
            [sys.executable, str(_ROOT / "scripts" / "read_nso_version.py")],
            cwd=_ROOT,
            text=True,
        ).strip()
        self.assertTrue(out)
        self.assertRegex(out, r"^[\d.]+$|^[\w.-]+$")


if __name__ == "__main__":
    unittest.main()
