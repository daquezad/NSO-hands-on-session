"""Unit tests for scripts/check_axe_warn.py — Story 6.10."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AXE_SCRIPT = REPO_ROOT / "scripts" / "check_axe_warn.py"


def _load_axe_module():
    spec = importlib.util.spec_from_file_location("check_axe_warn_tested", AXE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestAxeHelpers(unittest.TestCase):
    def test_serious_critical_empty(self) -> None:
        mod = _load_axe_module()
        self.assertEqual(mod._serious_critical_count({}), 0)

    def test_serious_critical_moderate_only(self) -> None:
        mod = _load_axe_module()
        r = {"violations": [{"impact": "moderate", "id": "x"}]}
        self.assertEqual(mod._serious_critical_count(r), 0)

    def test_serious_critical_counts(self) -> None:
        mod = _load_axe_module()
        r = {
            "violations": [
                {"impact": "critical"},
                {"impact": "serious"},
                {"impact": "minor"},
            ]
        }
        self.assertEqual(mod._serious_critical_count(r), 2)

    def test_count_violations_dict(self) -> None:
        mod = _load_axe_module()
        self.assertEqual(mod._count_violations({"violations": [{}, {}]}), 2)


if __name__ == "__main__":
    unittest.main()
