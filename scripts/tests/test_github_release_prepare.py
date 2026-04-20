"""Tests for scripts/ci/github_release_prepare.py (Story 6.9)."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def _load():
    p = _ROOT / "scripts" / "ci" / "github_release_prepare.py"
    spec = importlib.util.spec_from_file_location("github_release_prepare", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestChangelogInsert(unittest.TestCase):
    def test_insert_is_idempotent(self) -> None:
        mod = _load()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "CHANGELOG.md"
            path.write_text(
                "## [Unreleased]\n\n"
                "<!-- release-anchor: -->\n",
                encoding="utf-8",
            )
            mod.CHANGELOG = path
            mod.insert_changelog_section("v1.0.0", "### Changes\n\n- a\n")
            t1 = path.read_text(encoding="utf-8")
            self.assertIn("## [v1.0.0]", t1)
            mod.insert_changelog_section("v1.0.0", "### Changes\n\n- b\n")
            t2 = path.read_text(encoding="utf-8")
            self.assertEqual(t1, t2)


if __name__ == "__main__":
    unittest.main()
