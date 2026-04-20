"""Tests for scripts/ci/check-external-resources.py (Story 6.6)."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def _load():
    p = _ROOT / "scripts" / "ci" / "check-external-resources.py"
    spec = importlib.util.spec_from_file_location("check_external_resources", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestHostAllowed(unittest.TestCase):
    def test_exact_and_subdomain(self) -> None:
        mod = _load()
        allowed = {"github.com", "cisco.com"}
        self.assertTrue(mod._host_allowed("github.com", allowed))
        self.assertTrue(mod._host_allowed("api.github.com", allowed))
        self.assertFalse(mod._host_allowed("evil.com", allowed))


class TestCheckUrl(unittest.TestCase):
    def test_blocked_wins_over_allow(self) -> None:
        mod = _load()
        violations: list[str] = []
        mod._check_url(
            "f",
            "link",
            "href",
            "https://fonts.googleapis.com/css",
            allowed={"fonts.googleapis.com"},
            blocked={"fonts.googleapis.com"},
            violations=violations,
        )
        self.assertEqual(len(violations), 1)
        self.assertIn("blocked", violations[0])

    def test_non_allowlisted(self) -> None:
        mod = _load()
        violations: list[str] = []
        mod._check_url(
            "f",
            "a",
            "href",
            "https://unknown.example/foo",
            allowed={"github.com"},
            blocked=set(),
            violations=violations,
        )
        self.assertEqual(len(violations), 1)
        self.assertIn("non-allowlisted", violations[0])


class TestScanHtmlDir(unittest.TestCase):
    def test_detects_blocked_fonts(self) -> None:
        mod = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "p.html").write_text(
                '<!DOCTYPE html><html><head>'
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=X"/>'
                "</head><body></body></html>",
                encoding="utf-8",
            )
            v = mod.scan_html_dir(
                root,
                allowed={"example.com"},
                blocked={"fonts.googleapis.com"},
            )
        self.assertTrue(any("fonts.googleapis.com" in s for s in v))


class TestMain(unittest.TestCase):
    def test_ok_minimal_site(self) -> None:
        mod = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "ok.html").write_text(
                "<!DOCTYPE html><html><body>"
                '<p class="css-classification-banner">Cisco Confidential</p>'
                "</body></html>",
                encoding="utf-8",
            )
            rc = mod.main([str(root)])
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
