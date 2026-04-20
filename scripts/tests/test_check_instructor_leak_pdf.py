"""PDF mode for check_instructor_leak (Story 6.2)."""

from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "check_instructor_leak",
    _ROOT / "scripts" / "check_instructor_leak.py",
)
assert _SPEC and _SPEC.loader
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


class TestCheckInstructorLeakPdf(unittest.TestCase):
    def test_pdf_missing_file_exits_1(self) -> None:
        with unittest.mock.patch.object(sys, "stderr", io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                _MOD.main(["--pdf", str(_ROOT / "nonexistent-no-pdf-here.pdf")])
            self.assertEqual(ctx.exception.code, _MOD.EXIT_SCRIPT_ERROR)

    def test_scan_pdf_respects_pypdf_reader(self) -> None:
        from pypdf import PdfWriter

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            p = Path(tmp.name)
        try:
            w = PdfWriter()
            w.add_blank_page(width=612, height=792)
            with open(p, "wb") as f:
                w.write(f)

            class _Page:
                def extract_text(self) -> str:
                    return "No instructor markers here."

            class _R:
                pages = [_Page()]

            with unittest.mock.patch("pypdf.PdfReader", return_value=_R()):
                hits = _MOD._scan_pdf(p)
            self.assertEqual(hits, [])
        finally:
            p.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
