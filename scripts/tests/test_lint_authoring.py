"""Tests for scripts/lint_authoring.py — AR13 rules 1–7."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LINT_SCRIPT = REPO_ROOT / "scripts" / "lint_authoring.py"
FIXTURES = REPO_ROOT / "scripts" / "tests" / "fixtures" / "lint_docs"
FIXTURE_MKDOCS = REPO_ROOT / "scripts" / "tests" / "fixtures" / "mkdocs.yml"


def _load_lint_module():
    spec = importlib.util.spec_from_file_location("lint_authoring_tested", LINT_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_WARN_ALL = {
    "LINT_RULES_1_3_MODE": "warn",
    "LINT_RULES_4_7_MODE": "warn",
    "LINT_RULES_5_6_MODE": "warn",
    "LINT_RULES_8_11_MODE": "warn",
}


class TestLintAuthoring(unittest.TestCase):
    def _run(self, docs_dir: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, **(env or {})}
        return subprocess.run(
            [sys.executable, str(LINT_SCRIPT), str(docs_dir)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_fixtures_warn_mode_exits_zero_with_violations(self) -> None:
        r = self._run(FIXTURES, env=_WARN_ALL)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn("[rule 1]", r.stdout)
        self.assertIn("[rule 2]", r.stdout)
        self.assertIn("[rule 3]", r.stdout)
        self.assertIn("[rule 4a]", r.stdout)
        self.assertIn("[rule 7]", r.stdout)

    def test_fixtures_fail_mode_exits_nonzero(self) -> None:
        r = self._run(
            FIXTURES,
            env={**_WARN_ALL, "LINT_RULES_1_3_MODE": "fail"},
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("violation", r.stdout)

    def test_fixtures_fail_mode_rules_47_exits_nonzero(self) -> None:
        r = self._run(
            FIXTURES,
            env={**_WARN_ALL, "LINT_RULES_4_7_MODE": "fail"},
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("[rule 4a]", r.stdout)

    def test_good_chapter_only_passes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "proj"
            root.mkdir()
            shutil.copy(FIXTURE_MKDOCS, root / "mkdocs.yml")
            shutil.copytree(REPO_ROOT / "macros", root / "macros")
            docs = root / "docs"
            docs.mkdir()
            shutil.copytree(FIXTURES / "_template", docs / "_template")
            shutil.copy(FIXTURES / "01-good.md", docs / "01-good.md")
            shutil.copytree(REPO_ROOT / "overrides", root / "overrides")
            mk = root / "mkdocs.yml"
            t = mk.read_text(encoding="utf-8")
            if "LAB_SAFETY_MESSAGE" not in t:
                mk.write_text(
                    t.replace(
                        "generator: false",
                        "generator: false\n  LAB_SAFETY_MESSAGE: \"test lab safety\"",
                    ),
                    encoding="utf-8",
                )
            r = self._run(
                docs,
                env={
                    "LINT_RULES_1_3_MODE": "fail",
                    "LINT_RULES_4_7_MODE": "fail",
                    "LINT_RULES_5_6_MODE": "fail",
                    "LINT_RULES_8_11_MODE": "fail",
                    "LINT_RULES_12_MODE": "fail",
                },
            )
            self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
            self.assertIn("OK", r.stdout)

    def test_schema_missing_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "proj"
            root.mkdir()
            shutil.copy(FIXTURE_MKDOCS, root / "mkdocs.yml")
            docs = root / "docs"
            docs.mkdir()
            shutil.copy(FIXTURES / "01-good.md", docs / "01-good.md")
            r = self._run(docs)
            self.assertEqual(r.returncode, 2)
            self.assertIn("schema not found", r.stderr)

    def test_rule5_empty_alt_fails_without_decorative_marker(self) -> None:
        lint = _load_lint_module()
        text = "---\nx: y\n---\n\n![](pic.png)\n"
        v = lint.lint_rule5_images_and_mermaid(Path("01-lab.md"), text)
        self.assertTrue(any("empty alt" in x for x in v), msg=v)

    def test_rule5_decorative_marker_allows_empty_alt(self) -> None:
        lint = _load_lint_module()
        text = "---\nx: y\n---\n\n<!-- lint-allow-decorative -->\n![](pic.png)\n"
        v = lint.lint_rule5_images_and_mermaid(Path("01-lab.md"), text)
        self.assertEqual(v, [])

    def test_rule6a_broken_relative_link(self) -> None:
        lint = _load_lint_module()
        with tempfile.TemporaryDirectory() as td:
            docs = Path(td) / "docs"
            docs.mkdir()
            md = docs / "01-lab.md"
            md.write_text(
                "---\ntitle: t\nchapter: 1\nnso_version: \"6.5\"\n"
                'ned_versions: ["cisco-ios-cli-6.x"]\nestimated_duration: "45 min"\n'
                'prerequisites: ["None"]\nlearning_objectives: ["x"]\n'
                'idempotent: true\nclassification: "Cisco Confidential"\n'
                "---\n# L\n\n## Learning Objectives\nx\n## Time Budget\nx\n## Prerequisites\n"
                "## Procedure\n\n[broken](./missing.md)\n\n## Verification\nx\n## Common Errors\nx\n",
                encoding="utf-8",
            )
            mapped = lint._iter_lines_outside_fences(md.read_text(encoding="utf-8"))
            v = lint.lint_rule6a_internal_links(md, docs, mapped)
        self.assertTrue(any("broken link" in x for x in v), msg=v)

    def test_rule6b_unknown_host(self) -> None:
        lint = _load_lint_module()
        text = "---\nx: y\n---\n\nSee [evil](https://not-in-allowlist.example.com/x).\n"
        mapped = lint._iter_lines_outside_fences(text)
        v = lint.lint_rule6b_external_urls(
            Path("01-lab.md"),
            mapped,
            {"github.com"},
        )
        self.assertTrue(any("not-in-allowlist.example.com" in x or "not in scripts/url_allowlist" in x for x in v), msg=v)

    def test_repo_root_for_lint_finds_project_from_fixture_docs_path(self) -> None:
        lint = _load_lint_module()
        root = lint._repo_root_for_lint(FIXTURES)
        self.assertTrue((root / "scripts" / "lint_authoring.py").is_file())
        hosts = lint.load_url_allowlist(root)
        self.assertIn("localhost", hosts)

    def test_rule10_requires_classification_when_fm_ok(self) -> None:
        lint = _load_lint_module()
        text = "---\ntitle: x\n---\n\n# Hi\n"
        v = lint.lint_rule10_classification(Path("index.md"), text)
        self.assertTrue(any("classification" in x for x in v))

    def test_rule11_wiring_present_in_repo(self) -> None:
        lint = _load_lint_module()
        v = lint.lint_rule11_lab_safety(REPO_ROOT, REPO_ROOT / "docs")
        self.assertEqual(v, [], msg=v)

    def test_ar15_requires_rollback_when_not_idempotent(self) -> None:
        lint = _load_lint_module()
        text = (
            "---\nidempotent: false\nclassification: \"Cisco Confidential\"\n"
            "title: t\nchapter: 1\nnso_version: \"6.5\"\nned_versions: [x]\n"
            'estimated_duration: "1 min"\nprerequisites: [n]\nlearning_objectives: [o]\n---\n'
            "# L\n\n## Learning Objectives\nx\n## Time Budget\nx\n## Prerequisites\nx\n"
            "## Procedure\n\nnoop\n\n## Verification\nx\n## Common Errors\nx\n"
        )
        v = lint.lint_rule_ar15_rollback(Path("01-x.md"), text)
        self.assertTrue(any("AR15 rollback" in x for x in v), msg=v)


if __name__ == "__main__":
    unittest.main()
