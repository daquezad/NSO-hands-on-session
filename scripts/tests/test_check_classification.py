"""Tests for scripts/ci/check-classification.py (Story 6.6)."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[2]


def _load():
    p = _ROOT / "scripts" / "ci" / "check-classification.py"
    spec = importlib.util.spec_from_file_location("check_classification", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestScanHtml(unittest.TestCase):
    def test_passes_with_banner_class(self) -> None:
        mod = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.html").write_text(
                '<div class="css-classification-banner md-typeset">Cisco Confidential</div>',
                encoding="utf-8",
            )
            bad = mod.scan_html(root)
        self.assertEqual(bad, [])

    def test_passes_with_phrase_only(self) -> None:
        mod = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "b.html").write_text(
                "<html><body><footer>Cisco Confidential</footer></body></html>",
                encoding="utf-8",
            )
            bad = mod.scan_html(root)
        self.assertEqual(bad, [])

    def test_fails_when_missing(self) -> None:
        mod = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "bad.html").write_text("<html><body>no marker here</body></html>", encoding="utf-8")
            bad = mod.scan_html(root)
        self.assertEqual(len(bad), 1)
        self.assertIn("bad.html", bad[0])


class TestScanPdf(unittest.TestCase):
    def test_skip_cover_allows_empty_cover(self) -> None:
        mod = _load()
        mock_reader = MagicMock()
        p0 = MagicMock()
        p0.extract_text.return_value = ""
        p1 = MagicMock()
        p1.extract_text.return_value = "Lab content — Cisco Confidential — footer"
        mock_reader.pages = [p0, p1]

        with patch.object(mod, "PdfReader", return_value=mock_reader):
            bad = mod.scan_pdf(Path("dummy.pdf"), skip_cover=True)
        self.assertEqual(bad, [])

    def test_body_page_missing_phrase_fails(self) -> None:
        mod = _load()
        mock_reader = MagicMock()
        p0 = MagicMock()
        p0.extract_text.return_value = "cover"
        p1 = MagicMock()
        p1.extract_text.return_value = "unclassified body text"
        mock_reader.pages = [p0, p1]

        with patch.object(mod, "PdfReader", return_value=mock_reader):
            bad = mod.scan_pdf(Path("dummy.pdf"), skip_cover=True)
        self.assertTrue(any("page 2" in x and "missing" in x for x in bad))

    def test_no_skip_cover_checks_page_one(self) -> None:
        mod = _load()
        mock_reader = MagicMock()
        p0 = MagicMock()
        p0.extract_text.return_value = "no phrase on cover"
        mock_reader.pages = [p0]

        with patch.object(mod, "PdfReader", return_value=mock_reader):
            bad = mod.scan_pdf(Path("dummy.pdf"), skip_cover=False)
        self.assertTrue(any("page 1" in x for x in bad))


if __name__ == "__main__":
    unittest.main()
