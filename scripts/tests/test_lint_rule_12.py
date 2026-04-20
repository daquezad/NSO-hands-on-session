"""Tests for scripts/lint_authoring.py rule 12 (UX-DR30 instructor_block)."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LINT_SCRIPT = REPO_ROOT / "scripts" / "lint_authoring.py"


def _load_lint_module():
    spec = importlib.util.spec_from_file_location("lint_authoring_r12", LINT_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_FM_BASE = """---
title: "Lab fixture"
chapter: {chapter}
nso_version: "6.3"
ned_versions: ["cisco-ios-cli-6.x"]
estimated_duration: "45 min"
prerequisites: ["None"]
learning_objectives: ["x"]
idempotent: true
classification: "Cisco Confidential"
---
# Lab

## Learning Objectives
x
## Time Budget
x
## Prerequisites
x
## Procedure
x
## Verification
x
## Common Errors
x

{extra}
"""


class TestLintRule12(unittest.TestCase):
    def test_valid_generic_emits_no_violations(self) -> None:
        lint = _load_lint_module()
        body = r'{{ instructor_block(variant="generic", body="### FAQs\n- a\n- b\n\n### What breaks\n- c\n") }}'
        text = _FM_BASE.format(chapter=3, extra=body)
        v = lint.lint_rule12_ux_dr30(Path("03-lab.md"), text)
        self.assertEqual(v, [], msg=v)

    def test_missing_block_warns(self) -> None:
        lint = _load_lint_module()
        text = _FM_BASE.format(chapter=2, extra="")
        v = lint.lint_rule12_ux_dr30(Path("02-lab.md"), text)
        self.assertTrue(any("missing instructor_block" in x for x in v), msg=v)

    def test_generic_missing_faqs_heading_warns(self) -> None:
        lint = _load_lint_module()
        body = r'{{ instructor_block(variant="generic", body="### What breaks\n- only this\n") }}'
        text = _FM_BASE.format(chapter=2, extra=body)
        v = lint.lint_rule12_ux_dr30(Path("02-lab.md"), text)
        self.assertTrue(any("FAQs" in x for x in v), msg=v)

    def test_lab8_missing_choreography_warns(self) -> None:
        lint = _load_lint_module()
        body = (
            r'{{ instructor_block(variant="generic", body="### FAQs\n- a\n- b\n\n### What breaks\n- c\n") }}'
        )
        text = _FM_BASE.format(chapter=8, extra=body)
        v = lint.lint_rule12_ux_dr30(Path("08-lab.md"), text)
        self.assertTrue(any("choreography" in x.lower() for x in v), msg=v)

    def test_lab8_both_blocks_complete_no_violations(self) -> None:
        lint = _load_lint_module()
        body = (
            r'{{ instructor_block(variant="generic", body="### FAQs\n- a\n- b\n\n### What breaks\n- c\n") }}'
            r'\n\n{{ instructor_block(variant="choreography", body="### Pause points\n- p\n\n'
            r'### Narrating check-sync\n- n\n\n### Red-to-green flip\n- r\n") }}'
        )
        text = _FM_BASE.format(chapter=8, extra=body)
        v = lint.lint_rule12_ux_dr30(Path("08-lab.md"), text)
        self.assertEqual(v, [], msg=v)


if __name__ == "__main__":
    unittest.main()
