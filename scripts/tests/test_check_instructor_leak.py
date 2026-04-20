"""Tests for scripts/check_instructor_leak.py (Story 5.6)."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

# Import module under test
import importlib.util

_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "check_instructor_leak",
    _ROOT / "scripts" / "check_instructor_leak.py",
)
assert _SPEC and _SPEC.loader
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


class TestCheckInstructorLeak(unittest.TestCase):
    def test_clean_site_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            root.mkdir()
            (root / "index.html").write_text("<!DOCTYPE html><html><body><p>ok</p></body></html>", encoding="utf-8")
            buf_out = io.StringIO()
            buf_err = io.StringIO()
            with unittest.mock.patch.object(sys, "stdout", buf_out), unittest.mock.patch.object(sys, "stderr", buf_err):
                code = _MOD.main([str(root)])
            self.assertEqual(code, 0)
            self.assertIn("no leakage detected", buf_out.getvalue())

    def test_leak_instructor_notes_class_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            root.mkdir()
            (root / "bad.html").write_text(
                '<div class="instructor-notes instructor-notes--generic">x</div>',
                encoding="utf-8",
            )
            buf_err = io.StringIO()
            with unittest.mock.patch.object(sys, "stdout", io.StringIO()), unittest.mock.patch.object(
                sys, "stderr", buf_err
            ):
                with self.assertRaises(SystemExit) as ctx:
                    _MOD.main([str(root)])
                self.assertEqual(ctx.exception.code, _MOD.EXIT_LEAK)
            self.assertIn("LEAK", buf_err.getvalue())

    def test_code_fence_hides_path_strings(self) -> None:
        """Authoring-style table: paths only inside <code> must not leak."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            root.mkdir()
            (root / "authoring.html").write_text(
                "<p><code>docs/instructor-artifacts/**</code> and <code>*-instructor-notes.md</code></p>",
                encoding="utf-8",
            )
            buf_out = io.StringIO()
            with unittest.mock.patch.object(sys, "stdout", buf_out), unittest.mock.patch.object(sys, "stderr", io.StringIO()):
                code = _MOD.main([str(root)])
            self.assertEqual(code, 0)

    def test_slug_outside_code_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            root.mkdir()
            (root / "leak.html").write_text(
                "<p>See companion file 01-connect-workstation-instructor-notes.md</p>",
                encoding="utf-8",
            )
            with unittest.mock.patch.object(sys, "stdout", io.StringIO()), unittest.mock.patch.object(
                sys, "stderr", io.StringIO()
            ):
                with self.assertRaises(SystemExit) as ctx:
                    _MOD.main([str(root)])
                self.assertEqual(ctx.exception.code, _MOD.EXIT_LEAK)

    def test_missing_site_exits_1(self) -> None:
        buf_err = io.StringIO()
        with unittest.mock.patch.object(sys, "stderr", buf_err):
            with self.assertRaises(SystemExit) as ctx:
                _MOD.main(["/nonexistent/site/path/zzzz"])
            self.assertEqual(ctx.exception.code, _MOD.EXIT_SCRIPT_ERROR)


if __name__ == "__main__":
    unittest.main()
