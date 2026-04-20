"""Story 6.3 — print.css + PDF metadata wiring smoke tests."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[2]


class TestPrintCssSmoke(unittest.TestCase):
    def test_print_css_exists(self) -> None:
        p = _ROOT / "docs" / "assets" / "css" / "print.css"
        self.assertTrue(p.is_file(), f"missing {p}")

    def test_mkdocs_yml_lists_print_css(self) -> None:
        raw = (_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn("assets/css/print.css", raw)

    def test_mkdocs_yml_print_site_cover(self) -> None:
        raw = (_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn("add_cover_page:", raw)
        self.assertIn("cover_page_template:", raw)

    def test_mkdocs_yml_mike_versioning_story_6_8(self) -> None:
        raw = (_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn("site_url:", raw)
        self.assertIn("!ENV [SITE_URL", raw)
        self.assertIn("provider: mike", raw)
        self.assertIn("- mike:", raw)
        self.assertIn("- print-site:", raw)
        # print-site must remain after mike so the print page sees final nav
        self.assertLess(raw.index("- mike:"), raw.index("- print-site:"))

    def test_site_yaml_has_bug_report_url(self) -> None:
        p = _ROOT / "_data" / "site.yaml"
        self.assertTrue(p.is_file())
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict)
        assert isinstance(data, dict)
        self.assertIn("bug_report_url", data)
        self.assertIn("http", str(data["bug_report_url"]))


if __name__ == "__main__":
    unittest.main()
