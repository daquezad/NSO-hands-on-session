"""Unit tests for scripts/pdf_finalize_accessibility.py (Story 6.4)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter

_ROOT = Path(__file__).resolve().parents[2]
_MOD = _ROOT / "scripts" / "pdf_finalize_accessibility.py"


def _load_mod():
    import importlib.util

    spec = importlib.util.spec_from_file_location("pdf_finalize_accessibility", _MOD)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestPdfFinalizeHelpers(unittest.TestCase):
    def test_norm_collapses_whitespace(self) -> None:
        mod = _load_mod()
        self.assertEqual(mod._norm("  a\tb\n"), "a b")

    def test_needle_variants(self) -> None:
        mod = _load_mod()
        v = mod._needle_variants("Lab 1: Connect to the Workstation")
        self.assertTrue(any("Lab 1:" in x for x in v))
        self.assertTrue(any("Connect" in x for x in v))

    def test_load_site_title_from_mkdocs(self) -> None:
        mod = _load_mod()
        t = mod.load_site_title(_ROOT / "mkdocs.yml")
        self.assertIn("NSO", t)

    def test_finalize_preserves_markinfo_and_adds_outlines(self) -> None:
        mod = _load_mod()
        src = _ROOT / "dist" / "cisco-secure-services-nso-6.3.pdf"
        html = _ROOT / "site" / "print_page" / "index.html"
        if not src.is_file() or not html.is_file():
            self.skipTest("requires built site + PDF (mkdocs build && make pdf)")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tpath = Path(tmp.name)
        try:
            tpath.write_bytes(src.read_bytes())
            mod.finalize_print_pdf(tpath, print_html=html, mkdocs_yml=_ROOT / "mkdocs.yml")
            r = PdfReader(str(tpath))
            root = r.trailer["/Root"]
            self.assertTrue(root["/MarkInfo"]["/Marked"])
            self.assertIsNotNone(root.get("/StructTreeRoot"))
            self.assertIsNotNone(root.get("/Outlines"))
            self.assertEqual(str(root.get("/Lang")), "en-US")
        finally:
            tpath.unlink(missing_ok=True)

    def test_clone_writer_preserves_tags(self) -> None:
        """Regression: never use PdfWriter.append() for finalize — it strips /StructTreeRoot."""
        src = _ROOT / "dist" / "cisco-secure-services-nso-6.3.pdf"
        if not src.is_file():
            self.skipTest("requires dist PDF")
        reader = PdfReader(str(src))
        writer = PdfWriter(clone_from=reader)
        writer.add_outline_item("smoke", 0)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tpath = Path(tmp.name)
        try:
            with open(tpath, "wb") as f:
                writer.write(f)
            r2 = PdfReader(str(tpath))
            root = r2.trailer["/Root"]
            self.assertIsNotNone(root.get("/StructTreeRoot"))
            self.assertIsNotNone(root.get("/MarkInfo"))
        finally:
            tpath.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
