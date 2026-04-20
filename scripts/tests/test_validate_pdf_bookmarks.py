"""Tests for scripts/ci/validate-pdf-bookmarks.py (Story 6.5)."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def _load():
    p = _ROOT / "scripts" / "ci" / "validate-pdf-bookmarks.py"
    spec = importlib.util.spec_from_file_location("validate_pdf_bookmarks", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestNavCount(unittest.TestCase):
    def test_mkdocs_nav_leaf_count(self) -> None:
        mod = _load()
        n = mod.count_mkdocs_nav_md_leaves(_ROOT / "mkdocs.yml")
        self.assertEqual(n, 15)  # Home + 14 under Lab Guide


if __name__ == "__main__":
    unittest.main()
