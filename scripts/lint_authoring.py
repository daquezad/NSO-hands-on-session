#!/usr/bin/env python3
"""
Authoring lint — AR13 rules 1–11 + AR15 (Stories 2.3–2.6); rule 4d (Story 3.3); macro names include Story 3.5 `topology`.

Rules 1–3: frontmatter schema, filename, mandatory headings.
Rules 4a–4d: code-fence language, input/output pairing, bare commands (no $/> prompts), `expected_output` landmark.
Rule 7: macro / config variable references {{ name }} must exist in mkdocs extra or macros.
Rule 5: image alt text, Mermaid alt/title.
Rule 6a: internal links resolve; rule 6b: external URL host allowlist.
Rule 8: instructor inline vs companion coherence (warning only).
Rule 9: no hardcoded NSO/NED version strings outside fences (use macros).
Rule 10: classification must be exactly "Cisco Confidential".
Rule 11: lab-safety partial + LAB_SAFETY_MESSAGE + Story 3.4 macro placement (index + Lab 8 only).
Rule 12: instructor_block UX-DR30 minimums (generic FAQs + What breaks; Lab 8 + choreography) — Story 5.7.
Rule 3d: time_budget macro on every lab chapter (Story 3.4).
Rule 3f: home cover — index.md headline + home_subtitle + home_meta + lab_safety + topology + journey_table (Story 3.6).
AR15: idempotent: false requires Rollback admonition with code fence.

Default mode: WARN — prints violations, exits 0 (Epic 4 migration window).

Environment:
  LINT_RULES_1_3_MODE   warn|fail  (default warn)
  LINT_RULES_4_7_MODE   warn|fail  (default warn)
  LINT_RULES_5_6_MODE   warn|fail  (default warn)
  LINT_RULES_8_11_MODE  warn|fail  (default warn; rule 8 never fails exit — warnings only)
  LINT_RULES_12_MODE    warn|fail  (default warn; rule 12 UX-DR30 instructor_block)

Usage:
  python scripts/lint_authoring.py [DOCS_DIR]
"""

from __future__ import annotations

import codecs
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

try:
    import yaml
except ImportError as e:  # pragma: no cover
    print("ERROR: PyYAML is required. pip install pyyaml", file=sys.stderr)
    raise SystemExit(2) from e

# Rule 2: chapter filenames (labs only — top-level docs/NN-kebab.md)
CHAPTER_FILENAME_RE = re.compile(r"^\d{2}-[a-z][a-z0-9-]*\.md$")

# Rule 3: mandatory H2 sections in exact order (AR14 / Story 2.1)
MANDATORY_H2: list[str] = [
    "Learning Objectives",
    "Time Budget",
    "Prerequisites",
    "Procedure",
    "Verification",
    "Common Errors",
]

EXCLUDED_DIR_PARTS = frozenset({"_template", "instructor-artifacts"})
EXCLUDED_DIR_PREFIXES = ("_bmad",)

# Rules 4b–4c: command fence languages that require Expected output or lint-skip
CMD_FENCE_LANGS = frozenset({"bash", "shell", "cli"})

# Rule 7: well-known mkdocs-macros / Jinja names (avoid false positives)
MACRO_BUILTINS = frozenset({
    "config",
    "environment",
    "plugin",
    "include",
    "includes",
    "macros_info",
    "page",
    "pages",
    "navigation",
    "log",
    "expected_output",
    "time_budget",
    "lab_safety",
    "common_errors_start",
    "common_errors_end",
    "common_error",
    "topology",
    "home_subtitle",
    "home_meta",
    "journey_table",
    "instructor_block",
    "timing_sheet",
})

LINT_SKIP_COMMENT = "<!-- lint-skip: no-output -->"

def _is_expected_output_line(line: str) -> bool:
    s = line.strip()
    if "expected output" not in s.lower():
        return False
    return s.startswith("*") or s.startswith("_")


def _skip_path(path: Path, docs_root: Path) -> bool:
    try:
        rel = path.relative_to(docs_root)
    except ValueError:
        return True
    for part in rel.parts:
        if part in EXCLUDED_DIR_PARTS:
            return True
        if part.startswith(EXCLUDED_DIR_PREFIXES):
            return True
    return False


def _is_chapter_candidate(path: Path, docs_root: Path) -> bool:
    if path.suffix.lower() != ".md":
        return False
    if path.name == "index.md":
        return False
    if _skip_path(path, docs_root):
        return False
    if path.parent != docs_root:
        return False
    if not bool(re.match(r"^\d{2}-.+\.md$", path.name)):
        return False
    # AR5 companion files next to labs — not lab chapters (Story 5.1)
    if path.name.endswith("-instructor-notes.md"):
        return False
    return True


def _repo_root_for_lint(docs_root: Path) -> Path:
    """Directory that contains `scripts/lint_authoring.py` (works when docs is not `<repo>/docs`)."""
    d = docs_root.resolve()
    marker = Path("scripts") / "lint_authoring.py"
    for p in [d, *d.parents]:
        if (p / marker).is_file():
            return p
    return d.parent


def _load_schema(schema_path: Path) -> dict[str, Any]:
    with schema_path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise ValueError("schema.yaml must be a mapping at top level")
    return raw


def _parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, str | None]:
    if not text.startswith("---"):
        return None, "missing opening --- frontmatter delimiter"
    rest = text[3:]
    end = rest.find("\n---")
    if end == -1:
        return None, "unclosed YAML frontmatter (no closing ---)"
    yaml_block = rest[:end].strip()
    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError as exc:
        return None, f"YAML parse error: {exc}"
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, "frontmatter must be a YAML mapping"
    return data, None


def _check_type(field: str, value: Any, expected: str) -> str | None:
    if expected == "str" and isinstance(value, str):
        return None
    if expected == "int" and isinstance(value, int) and not isinstance(value, bool):
        return None
    if expected == "bool" and isinstance(value, bool):
        return None
    if expected == "list[str]":
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            return None
        return f"expected list of strings, got {type(value).__name__}"
    return f"expected {expected}, got {type(value).__name__}"


def lint_rule1_frontmatter(path: Path, schema: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    text = path.read_text(encoding="utf-8")
    fm, err = _parse_frontmatter(text)
    if err:
        violations.append(f"[rule 1] {path.name}: {err}")
        return violations

    assert fm is not None

    for field_name, spec in schema.items():
        if not isinstance(spec, dict):
            continue
        required = spec.get("required", False)
        if field_name not in fm:
            if required:
                violations.append(f"[rule 1] {path.name}: missing frontmatter field `{field_name}`")
            continue
        value = fm[field_name]
        ftype = spec.get("type", "str")
        terr = _check_type(field_name, value, ftype)
        if terr:
            violations.append(f"[rule 1] {path.name}: field `{field_name}`: {terr}")
            continue
        if "enum" in spec and value not in spec["enum"]:
            violations.append(
                f"[rule 1] {path.name}: field `{field_name}` must be one of {spec['enum']}, got {value!r}"
            )
        if "pattern" in spec and isinstance(value, str):
            pat = spec["pattern"]
            if not re.match(pat, value):
                violations.append(
                    f"[rule 1] {path.name}: field `{field_name}` must match pattern {pat!r}, got {value!r}"
                )
        if ftype == "list[str]" and isinstance(value, list) and len(value) == 0:
            violations.append(f"[rule 1] {path.name}: field `{field_name}` must have at least one entry")

    return violations


def lint_rule2_filename(path: Path) -> list[str]:
    if CHAPTER_FILENAME_RE.match(path.name):
        return []
    return [f"[rule 2] {path.name}: filename must match ^\\d{{2}}-[a-z][a-z0-9-]*\\.md$ (NN-kebab-case)"]


def _extract_headings(text: str) -> list[tuple[int, int, str]]:
    headings: list[tuple[int, int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            headings.append((i, level, title))
    return headings


def _body_after_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :]
    return text


def lint_rule3_headings(path: Path) -> list[str]:
    violations: list[str] = []
    text = path.read_text(encoding="utf-8")
    body = _body_after_frontmatter(text)
    headings = _extract_headings(body)

    h1s = [h for h in headings if h[1] == 1]
    if len(h1s) == 0:
        violations.append(f"[rule 3] {path.name}: no H1 heading (exactly one required)")
    elif len(h1s) > 1:
        violations.append(
            f"[rule 3] {path.name}: multiple H1 headings (lines {h1s[0][0]} and {h1s[1][0]})"
        )

    for i in range(1, len(headings)):
        _pl, prev_lv, _pt = headings[i - 1]
        line_no, level, _title = headings[i]
        if level > prev_lv + 1:
            violations.append(
                f"[rule 3] {path.name}: heading level skips (H{prev_lv} → H{level} at line {line_no})"
            )

    h2_titles = [h[2] for h in headings if h[1] == 2]
    for expected in MANDATORY_H2:
        if expected not in h2_titles:
            violations.append(f"[rule 3] {path.name}: missing mandatory section `## {expected}`")

    idx = 0
    for expected in MANDATORY_H2:
        while idx < len(h2_titles) and h2_titles[idx] != expected:
            idx += 1
        if idx >= len(h2_titles):
            violations.append(
                f"[rule 3] {path.name}: mandatory sections not in required order "
                f"(expected `## {expected}` in sequence after prior mandatories)"
            )
            break
        idx += 1

    return violations


def lint_rule3f_home_index(path: Path, text: str) -> list[str]:
    """Story 3.6: docs/index.md must include cover macros and avoid generic welcome copy."""
    if path.name != "index.md":
        return []
    violations: list[str] = []
    body = _body_after_frontmatter(text)
    low = body.lower()
    if re.search(r"(?m)^#\s+", body):
        h1_lines = [ln for ln in body.splitlines() if re.match(r"^#\s+[^#]", ln)]
        if len(h1_lines) != 1:
            violations.append(
                f"[rule 3f] {path.name}: exactly one H1 required (found {len(h1_lines)})"
            )
    if "welcome to" in low and "nso" in low:
        violations.append(
            f"[rule 3f] {path.name}: remove generic “welcome” marketing copy (Story 3.6)"
        )
    required = (
        ("home_subtitle(", "home_subtitle(...)"),
        ("home_meta(", "home_meta()"),
        ('lab_safety(variant="general")', 'lab_safety(variant="general")'),
        ("topology(", "topology(...)"),
        ("journey_table(", "journey_table()"),
    )
    for needle, label in required:
        if needle not in body:
            violations.append(f"[rule 3f] {path.name}: add {label} (Story 3.6 home cover)")
    return violations


def lint_rule3d_time_budget(path: Path, text: str) -> list[str]:
    """Story 3.4: each lab chapter must call time_budget(...) in the Time Budget section."""
    body = _body_after_frontmatter(text)
    if "time_budget(" not in body:
        return [
            f"[rule 3d] {path.name}: add `time_budget(total=…, segments=[[min,\"label\"],…])` "
            f"(Story 3.4 — minutes must sum to total)"
        ]
    return []


def _flatten_extra_keys(extra: Any, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if not isinstance(extra, dict):
        return keys
    for k, v in extra.items():
        full = f"{prefix}.{k}" if prefix else str(k)
        keys.add(str(k))
        if prefix:
            keys.add(full)
        if isinstance(v, dict):
            keys |= _flatten_extra_keys(v, full)
    return keys


def _parse_mkdocs_extra_block(text: str) -> dict[str, Any]:
    """Parse only the indented YAML under top-level `extra:` — avoids MkDocs !!python tags."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() != "extra:":
            continue
        block_lines: list[str] = []
        j = i + 1
        while j < len(lines):
            ln = lines[j]
            if ln.strip() != "" and not ln.startswith(" ") and not ln.startswith("\t"):
                break
            block_lines.append(ln)
            j += 1
        block = "\n".join(block_lines)
        if not block.strip():
            return {}
        try:
            loaded = yaml.safe_load(block)
            return loaded if isinstance(loaded, dict) else {}
        except yaml.YAMLError:
            return {}
    return {}


def load_allowed_jinja_names(docs_root: Path) -> set[str]:
    """Names allowed in {{ name }} from mkdocs.yml `extra` and macros/main.py."""
    allowed = set(MACRO_BUILTINS)
    repo_root = _repo_root_for_lint(docs_root)
    mk_path = repo_root / "mkdocs.yml"
    if mk_path.is_file():
        try:
            full = mk_path.read_text(encoding="utf-8")
            extra = _parse_mkdocs_extra_block(full)
            if extra:
                allowed |= _flatten_extra_keys(extra)
        except OSError:
            pass

    macro_py = repo_root / "macros" / "main.py"
    if macro_py.is_file():
        text = macro_py.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'env\.variables\[\s*["\']([^"\']+)["\']\s*\]', text):
            allowed.add(m.group(1))
        for m in re.finditer(r"env\.variables\.\s*get\(\s*[\"']([^\"']+)[\"']", text):
            allowed.add(m.group(1))
    return allowed


def _iter_fences(lines: list[str]) -> list[tuple[int, str, list[str], int]]:
    """Return list of (open_line_1based, lang, body_lines, close_line_1based)."""
    out: list[tuple[int, str, list[str], int]] = []
    i = 0
    n = len(lines)
    while i < n:
        m = re.match(r"^```(\S*)\s*$", lines[i])
        if not m:
            i += 1
            continue
        lang = (m.group(1) or "").strip()
        open_line = i + 1
        i += 1
        body_start = i
        while i < n and not re.match(r"^```\s*$", lines[i]):
            i += 1
        if i >= n:
            break
        body = lines[body_start:i]
        close_line = i + 1
        out.append((open_line, lang, body, close_line))
        i += 1
    return out


def _has_skip_before_open(open_line_idx: int, lines: list[str]) -> bool:
    k = open_line_idx - 2  # 0-based line index of opening ```
    while k >= 0 and lines[k].strip() == "":
        k -= 1
    if k < 0:
        return False
    return LINT_SKIP_COMMENT in lines[k]


def _command_fence_ok_after(close_line_idx: int, lines: list[str]) -> bool:
    """After closing ``` line (1-based close_line_idx), optional {{ expected_output(...) }}, then Expected output + text/console fence."""
    j = close_line_idx  # 0-based index of closing ``` line
    j += 1
    while j < len(lines) and lines[j].strip() == "":
        j += 1
    while j < len(lines):
        line = lines[j]
        if _is_expected_output_line(line):
            break
        stripped = line.strip()
        if stripped == "":
            j += 1
            continue
        if re.search(r"\{\{\s*expected_output\s*\(", line):
            j += 1
            continue
        return False
    else:
        return False
    if j >= len(lines) or not _is_expected_output_line(lines[j]):
        return False
    j += 1
    while j < len(lines) and lines[j].strip() == "":
        j += 1
    if j >= len(lines):
        return False
    m = re.match(r"^```(text|console)\s*$", lines[j], re.IGNORECASE)
    return bool(m)


def lint_rules_4abc(path: Path, lines: list[str]) -> list[str]:
    violations: list[str] = []
    for open_line, lang, body, close_line in _iter_fences(lines):
        if lang == "":
            violations.append(
                f"[rule 4a] {path.name}:{open_line}: code fence has no language tag (use ```text, ```cli, …)"
            )
            continue

        lang_lower = lang.lower()
        if lang_lower in CMD_FENCE_LANGS:
            if _has_skip_before_open(open_line, lines):
                continue
            if not _command_fence_ok_after(close_line, lines):
                violations.append(
                    f"[rule 4b] {path.name}:{open_line}: `{lang}` fence must be followed by "
                    f"italic *Expected output:* and a ```text/```console fence, "
                    f"or place `{LINT_SKIP_COMMENT}` on the line above the opening fence"
                )
            for bi, bline in enumerate(body):
                phys = open_line + 1 + bi
                if re.match(r"^\s*\$\s+", bline) or re.match(r"^\s*>\s+", bline):
                    violations.append(
                        f"[rule 4c] {path.name}:{phys}: do not embed shell prompts (`$ ` / `> `) in command fences — use bare commands"
                    )

    return violations


def lint_rule4d_expected_output_landmark(path: Path, lines: list[str]) -> list[str]:
    """Fail if `expected_output` appears without non-empty `landmark=\"...\"` (Story 3.3)."""
    violations: list[str] = []
    in_fence = False
    for i, line in enumerate(lines, 1):
        t = line.strip()
        if t.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "expected_output" not in line or "{{" not in line:
            continue
        if not re.search(r"\{\{\s*expected_output", line):
            continue
        if re.search(r"landmark\s*=\s*['\"]\s*['\"]", line):
            violations.append(
                f"[rule 4d] {path.name}:{i}: `expected_output` landmark must be non-empty (Story 3.3)"
            )
            continue
        if not re.search(r"landmark\s*=\s*[\"'][^\"']+[\"']", line):
            violations.append(
                f"[rule 4d] {path.name}:{i}: `expected_output` requires `landmark=\"...\"` (Story 3.3)"
            )
    return violations


_MACRO_REF_RE = re.compile(r"\{\{-?\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*-?\}\}")


def _text_outside_fences(text: str) -> str:
    """Remove fenced code bodies so `{{ x }}` inside examples does not trigger rule 7."""
    lines = text.splitlines()
    out: list[str] = []
    in_fence = False
    for line in lines:
        if re.match(r"^```", line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def lint_rule7_macros(path: Path, text: str, allowed: set[str]) -> list[str]:
    violations: list[str] = []
    scan = _text_outside_fences(text)
    for m in _MACRO_REF_RE.finditer(scan):
        name = m.group(1)
        # Only top-level names for dotted (allow config.foo if config allowed)
        root = name.split(".", 1)[0]
        if name in allowed or root in allowed:
            continue
        line_no = scan[: m.start()].count("\n") + 1
        violations.append(
            f"[rule 7] {path.name}:{line_no}: `{{{{ {name} }}}}` is not declared in `macros/main.py` or `mkdocs.yml` extra"
        )
    return violations


ALLOW_DECORATIVE_IMG = "<!-- lint-allow-decorative -->"
SCRUB_PROTOCOL_REF = "docs/scrub-protocol.md"
MERMAID_CHAPTER_ALT_SUFFIX = ".alt.txt"

URL_HOST_DENYLIST = frozenset({"fonts.googleapis.com", "fonts.gstatic.com"})


def _heading_slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _extract_heading_slugs_from_body(md_body: str) -> set[str]:
    slugs: set[str] = set()
    for _ln, _level, title in _extract_headings(md_body):
        slugs.add(_heading_slug(title))
    return slugs


def _anchor_matches_heading(anchor: str, slugs: set[str]) -> bool:
    a = anchor.strip()
    if not a:
        return True
    al = a.lower()
    if al in slugs:
        return True
    if _heading_slug(a.replace("-", " ")) in slugs:
        return True
    if _heading_slug(a) in slugs:
        return True
    return False


def load_url_allowlist(repo_root: Path) -> set[str]:
    path = repo_root / "scripts" / "url_allowlist.txt"
    hosts: set[str] = set()
    if not path.is_file():
        return hosts
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        host = line.split("#", 1)[0].strip()
        if host:
            hosts.add(host.lower())
    return hosts


def _url_host_ok(host: str, allowlist: set[str]) -> bool:
    h = host.lower()
    if h in URL_HOST_DENYLIST:
        return False
    return h in allowlist


def _strip_url_trailing_punct(url: str) -> str:
    return url.strip().rstrip(").,;>\"'»«")


def _iter_lines_outside_fences(text: str) -> list[tuple[int, str]]:
    """(1-based file line number, content) for lines outside ``` fences."""
    out: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(text.splitlines(), start=1):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((i, line))
    return out


def _prev_nonblank_mapped(mapped: list[tuple[int, str]], line_no: int) -> tuple[int, str] | None:
    prev: tuple[int, str] | None = None
    for lno, ltext in mapped:
        if lno >= line_no:
            break
        if ltext.strip():
            prev = (lno, ltext)
    return prev


def _extract_markdown_links_mapped(mapped: list[tuple[int, str]]) -> list[tuple[int, str, str]]:
    out: list[tuple[int, str, str]] = []
    for line_no, line in mapped:
        for m in re.finditer(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)", line):
            out.append((line_no, m.group(1), m.group(2).strip()))
    return out


def lint_rule5_images_and_mermaid(path: Path, full_text: str) -> list[str]:
    violations: list[str] = []
    mapped = _iter_lines_outside_fences(full_text)

    for line_no, line in mapped:
        for m in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", line):
            alt = m.group(1)
            if alt.strip() != "":
                continue
            prev = _prev_nonblank_mapped(mapped, line_no)
            prev_ok = prev is not None and ALLOW_DECORATIVE_IMG in prev[1]
            if not prev_ok:
                violations.append(
                    f"[rule 5] {path.name}:{line_no}: image with empty alt `![](...)` requires "
                    f"`{ALLOW_DECORATIVE_IMG}` on the previous non-blank line, or non-empty alt text. "
                    f"For screenshots and diagram images, scrub identifiers per {SCRUB_PROTOCOL_REF} (Story 4.1)."
                )

    chapter_alt = path.with_name(path.stem + MERMAID_CHAPTER_ALT_SUFFIX)
    chapter_alt_ok = chapter_alt.is_file() and chapter_alt.stat().st_size > 0

    lines = full_text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        if not re.match(r"^```\s*mermaid\s*$", lines[i], re.I):
            i += 1
            continue
        open_line = i + 1
        i += 1
        body: list[str] = []
        while i < n and not re.match(r"^```\s*$", lines[i]):
            body.append(lines[i])
            i += 1
        if i >= n:
            break
        i += 1

        has_title = any(re.search(r"title:\s*\S", line, re.I) for line in body[:15])
        if has_title or chapter_alt_ok:
            continue
        violations.append(
            f"[rule 5] {path.name}:{open_line}: mermaid block must include `title:` in the first 15 lines "
            f"or add non-empty `{chapter_alt.name}` beside this chapter (docs/authoring.md)"
        )

    return violations


def lint_rule6a_internal_links(path: Path, docs_root: Path, mapped: list[tuple[int, str]]) -> list[str]:
    violations: list[str] = []
    docs_resolved = docs_root.resolve()
    current = path.resolve()
    try:
        body = _body_after_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        body = ""
    current_slugs = _extract_heading_slugs_from_body(body)

    for line_no, _txt, raw_url in _extract_markdown_links_mapped(mapped):
        url = _strip_url_trailing_punct(raw_url.strip())
        if not url:
            continue
        if re.match(r"^https?://", url, re.I):
            continue
        if url.startswith("mailto:") or url.startswith("ftp:"):
            continue

        parts = url.split("#", 1)
        url_path = parts[0].strip()
        anchor = parts[1].strip() if len(parts) > 1 else None

        if not url_path:
            if anchor and not _anchor_matches_heading(anchor, current_slugs):
                violations.append(
                    f"[rule 6a] {path.name}:{line_no}: anchor `#{anchor}` does not match any heading in this file"
                )
            continue

        target_path = (current.parent / unquote(url_path)).resolve()
        try:
            target_path.relative_to(docs_resolved)
        except ValueError:
            violations.append(
                f"[rule 6a] {path.name}:{line_no}: internal link escapes docs/: `{url}`"
            )
            continue
        if not target_path.is_file():
            violations.append(
                f"[rule 6a] {path.name}:{line_no}: broken link — file not found: `{url}`"
            )
            continue
        if anchor:
            try:
                tb = _body_after_frontmatter(target_path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                tb = ""
            tslug = _extract_heading_slugs_from_body(tb)
            if not _anchor_matches_heading(anchor, tslug):
                violations.append(
                    f"[rule 6a] {path.name}:{line_no}: anchor `#{anchor}` not found in `{target_path.name}`"
                )

    return violations


def lint_rule6b_external_urls(path: Path, mapped: list[tuple[int, str]], allowlist: set[str]) -> list[str]:
    violations: list[str] = []
    reported: set[tuple[int, str]] = set()

    def report(line_no: int, url: str, msg: str) -> None:
        key = (line_no, url)
        if key in reported:
            return
        reported.add(key)
        violations.append(msg)

    for line_no, _txt, raw_url in _extract_markdown_links_mapped(mapped):
        url = _strip_url_trailing_punct(raw_url.strip())
        if not re.match(r"^https?://", url, re.I):
            continue
        p = urlparse(url)
        host = p.hostname
        if not host:
            continue
        hl = host.lower()
        if hl in URL_HOST_DENYLIST:
            report(
                line_no,
                url,
                f"[rule 6b] {path.name}:{line_no}: host `{hl}` is deny-listed (use local assets; see AR17)",
            )
        elif not _url_host_ok(hl, allowlist):
            report(
                line_no,
                url,
                f"[rule 6b] {path.name}:{line_no}: host `{hl}` not in scripts/url_allowlist.txt",
            )

    for line_no, line in mapped:
        for m in re.finditer(r"https?://[^\s)<>\]]+", line, re.I):
            url = _strip_url_trailing_punct(m.group(0))
            p = urlparse(url)
            host = p.hostname
            if not host:
                continue
            hl = host.lower()
            if hl in URL_HOST_DENYLIST:
                report(
                    line_no,
                    url,
                    f"[rule 6b] {path.name}:{line_no}: host `{hl}` is deny-listed (use local assets; see AR17)",
                )
            elif not _url_host_ok(hl, allowlist):
                report(
                    line_no,
                    url,
                    f"[rule 6b] {path.name}:{line_no}: host `{hl}` not in scripts/url_allowlist.txt",
                )

    return violations


LINT_ALLOW_HARDCODED_VERSION = "<!-- lint-allow-hardcoded-version -->"

# Rule 9 — prose outside ``` fences in chapter body (not frontmatter). Tuned to architecture NFR-S4 / UX-DR20.
RULE9_VERSION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("NSO release in prose (use {{ nso_version }})", re.compile(r"(?i)\bNSO\s+[0-9]+\.[0-9]+(?:\.[0-9]+)?\b")),
    ("ncs- version prefix (use macros / scrub examples)", re.compile(r"(?i)\bncs-[0-9]+\.[0-9]+")),
    ("nso- version prefix (use macros / scrub examples)", re.compile(r"(?i)\bnso-[0-9]+\.[0-9]+")),
    ("NSO directory token (e.g. NSO-6.5-free)", re.compile(r"(?i)NSO-[0-9]+\.[0-9]+")),
    ("NED package id (use {{ ned_versions }})", re.compile(r"(?i)cisco-(?:ios|iosxr|ios-xr|nx|asa)-cli-[0-9]+\.[0-9]+")),
]


def _fm_end_line_1based(text: str) -> int:
    """First line number of Markdown body after closing ---, or 1 if no frontmatter."""
    if not text.startswith("---"):
        return 1
    rest = text[3:]
    end = rest.find("\n---")
    if end == -1:
        return 1
    return text[: end + 4].count("\n") + 1


def _iter_body_lines_outside_fences(full_text: str) -> list[tuple[int, str]]:
    """(file line 1-based, text) for body lines outside ``` fences."""
    lines = full_text.splitlines()
    start = _fm_end_line_1based(full_text)
    in_fence = False
    out: list[tuple[int, str]] = []
    for i, line in enumerate(lines, start=1):
        if i < start:
            continue
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((i, line))
    return out


def _line_has_hardcoded_version_allow(mapped: list[tuple[int, str]], idx: int) -> bool:
    line = mapped[idx][1]
    if LINT_ALLOW_HARDCODED_VERSION in line:
        return True
    j = idx - 1
    while j >= 0:
        prev = mapped[j][1].strip()
        if prev:
            return prev == LINT_ALLOW_HARDCODED_VERSION
        j -= 1
    return False


def lint_rule8_instructor_coherence(path: Path) -> list[str]:
    """Warnings only — companion / inline instructor coherence (AR5)."""
    warnings: list[str] = []
    try:
        full = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return warnings
    body = _body_after_frontmatter(full)
    body_start = _fm_end_line_1based(full)
    for m in re.finditer(
        r"{%\s*if\s+instructor\s*%}(.*?){%\s*endif\s*%}", body, flags=re.DOTALL | re.IGNORECASE
    ):
        inner = m.group(1)
        nlines = len(inner.splitlines()) if inner.strip() else 0
        if nlines > 5:
            line_in_body = body[: m.start()].count("\n") + 1
            phys = body_start + line_in_body - 1
            warnings.append(
                f"[rule 8] {path.name}:{phys}: inline `{{% if instructor %}}` block is {nlines} lines "
                f"(> 5) — move extended content to `{path.stem}-instructor-notes.md` (AR5)"
            )
    companion = path.parent / f"{path.stem}-instructor-notes.md"
    if companion.is_file():
        if not re.search(r"{%\s*if\s+instructor\s*%}", body, flags=re.IGNORECASE):
            warnings.append(
                f"[rule 8] {path.name}: companion `{companion.name}` exists but learner file has no "
                f"`{{% if instructor %}}` block — verify content is not misplaced (AR5)"
            )
    return warnings


def lint_rule9_hardcoded_versions(path: Path, full_text: str) -> list[str]:
    violations: list[str] = []
    mapped = _iter_body_lines_outside_fences(full_text)
    for idx, (line_no, line) in enumerate(mapped):
        if _line_has_hardcoded_version_allow(mapped, idx):
            continue
        for label, pat in RULE9_VERSION_PATTERNS:
            if pat.search(line):
                violations.append(
                    f"[rule 9] {path.name}:{line_no}: hardcoded version ({label}) — "
                    f"use `{{{{ nso_version }}}}` / `{{{{ ned_versions }}}}` or place "
                    f"`{LINT_ALLOW_HARDCODED_VERSION}` on the prior line"
                )
                break
    return violations


def lint_rule10_classification(path: Path, full_text: str) -> list[str]:
    fm, err = _parse_frontmatter(full_text)
    if err:
        return []
    assert fm is not None
    if "classification" not in fm:
        return [
            f"[rule 10] {path.name}: frontmatter must set classification: \"Cisco Confidential\""
        ]
    if fm["classification"] != "Cisco Confidential":
        return [
            f"[rule 10] {path.name}: classification must be exactly \"Cisco Confidential\", "
            f"got {fm['classification']!r}"
        ]
    return []


def lint_rule11_lab_safety(repo_root: Path, docs_root: Path) -> list[str]:
    """Partial exists; non-empty LAB_SAFETY_MESSAGE; no global banner include (Story 3.4); index + Lab 8 macros."""
    violations: list[str] = []
    partial = repo_root / "overrides" / "partials" / "lab-safety-banner.html"
    if not partial.is_file():
        violations.append(f"[rule 11] missing `{partial.relative_to(repo_root)}`")

    main = repo_root / "overrides" / "main.html"
    prnt = repo_root / "overrides" / "print.html"
    for label, pth in (("overrides/main.html", main), ("overrides/print.html", prnt)):
        if not pth.is_file():
            violations.append(f"[rule 11] missing `{label}`")
            continue
        txt = pth.read_text(encoding="utf-8", errors="replace")
        if "lab-safety-banner.html" in txt:
            violations.append(
                f"[rule 11] `{label}` must not globally include lab-safety-banner "
                f"(Story 3.4 — use `{{{{ lab_safety(...) }}}}` on index + Lab 8 only)"
            )

    mk = repo_root / "mkdocs.yml"
    extra: dict[str, Any] = {}
    if mk.is_file():
        extra = _parse_mkdocs_extra_block(mk.read_text(encoding="utf-8", errors="replace"))
    msg = extra.get("LAB_SAFETY_MESSAGE") if isinstance(extra, dict) else None
    ok_extra = isinstance(msg, str) and msg.strip() != ""
    macro = repo_root / "macros" / "main.py"
    ok_macro = macro.is_file() and "LAB_SAFETY_MESSAGE" in macro.read_text(
        encoding="utf-8", errors="replace"
    )
    if not ok_extra and not ok_macro:
        violations.append(
            "[rule 11] define non-empty `LAB_SAFETY_MESSAGE` in `mkdocs.yml` `extra:` "
            "or reference `LAB_SAFETY_MESSAGE` in `macros/main.py`"
        )

    idx = docs_root / "index.md"
    if idx.is_file():
        it = idx.read_text(encoding="utf-8", errors="replace")
        if "lab_safety" not in it:
            violations.append('[rule 11] docs/index.md must call {{ lab_safety(variant="general") }}')
        if re.search(
            r'lab_safety\s*\(\s*[^)]*variant\s*=\s*["\']intentional_failure',
            it,
        ):
            violations.append(
                "[rule 11] docs/index.md must not use lab_safety(intentional_failure) (Lab 8 only)"
            )

    for lab8 in sorted(docs_root.glob("08-*.md")):
        t8 = lab8.read_text(encoding="utf-8", errors="replace")
        if "lab_safety" not in t8:
            violations.append(
                f"[rule 11] {lab8.name} must call "
                f'{{{{ lab_safety(variant="intentional_failure") }}}}'
            )
        elif "intentional_failure" not in t8:
            violations.append(
                f"[rule 11] {lab8.name} must use lab_safety(variant=\"intentional_failure\") (Lab 8)"
            )

    for ch in sorted(docs_root.glob("[0-9][0-9]-*.md")):
        if ch.name.startswith("08-"):
            continue
        tc = ch.read_text(encoding="utf-8", errors="replace")
        if "lab_safety(" in tc:
            violations.append(
                f"[rule 11] {ch.name} must not use lab_safety (only index.md and Lab 8)"
            )

    return violations


def _h2_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in body.splitlines():
        hm = re.match(r"^## ([^#].*)$", line)
        if hm:
            if current is not None:
                sections[current.strip()] = "\n".join(buf)
            current = hm.group(1).strip()
            buf = []
        else:
            if current is not None:
                buf.append(line)
    if current is not None:
        sections[current.strip()] = "\n".join(buf)
    return sections


def _section_has_rollback_with_fence(proc: str, common_err: str) -> bool:
    for sec in (proc, common_err):
        if not sec.strip():
            continue
        m = re.search(r"!!!\s*warning\s*\"Rollback\"", sec, flags=re.IGNORECASE | re.MULTILINE)
        if not m:
            continue
        after = sec[m.end() :]
        if "```" in after:
            return True
    return False


# Rule 12 (Story 5.7): UX-DR30 — instructor_block minimums; anchor in docs/authoring.md
RULE12_DOC_ANCHOR = "docs/authoring.md#ux-dr30-minimum-content-per-chapter"

_INSTRUCTOR_BLOCK_START = re.compile(r"instructor_block\s*\(", re.IGNORECASE)


def _unescape_jinja_string_literal(raw: str) -> str:
    """Decode \\n, \\", \\\\ in a macro string body (best-effort)."""
    try:
        return codecs.decode(raw, "unicode_escape")
    except (UnicodeDecodeError, ValueError):
        return raw


def _extract_balanced_paren_arg(s: str, open_paren_idx: int) -> tuple[str, int] | None:
    """open_paren_idx points at '('. Returns (inner between parens, index after closing ')')."""
    if open_paren_idx >= len(s) or s[open_paren_idx] != "(":
        return None
    depth = 0
    i = open_paren_idx
    n = len(s)
    while i < n:
        c = s[i]
        if c in "\"'":
            q = c
            i += 1
            while i < n:
                if s[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if s[i] == q:
                    i += 1
                    break
                i += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                inner = s[open_paren_idx + 1 : i]
                return inner, i + 1
        i += 1
    return None


def _parse_instructor_block_kwargs(inner: str) -> dict[str, str]:
    """Parse variant= and body= string arguments from macro call inner (no nested calls)."""
    out: dict[str, str] = {}
    for key in ("variant", "body"):
        pat = re.compile(
            rf"\b{re.escape(key)}\s*=\s*("
            r'"(?P<dq>(?:[^"\\]|\\.)*)"|'
            r"'(?P<sq>(?:[^'\\]|\\.)*)'"
            r")",
            re.DOTALL,
        )
        m = pat.search(inner)
        if not m:
            continue
        raw = m.group("dq") if m.group("dq") is not None else m.group("sq")
        out[key] = _unescape_jinja_string_literal(raw)
    return out


def iter_instructor_block_calls(scan: str) -> list[tuple[str, str]]:
    """
    Find instructor_block(...) calls in text (already outside code fences).
    Returns list of (variant_lower, body_text).
    """
    found: list[tuple[str, str]] = []
    pos = 0
    while True:
        m = _INSTRUCTOR_BLOCK_START.search(scan, pos)
        if not m:
            break
        open_idx = m.start() + m.group(0).rindex("(")
        got = _extract_balanced_paren_arg(scan, open_idx)
        if not got:
            break
        inner, after = got
        kw = _parse_instructor_block_kwargs(inner)
        variant = (kw.get("variant") or "generic").strip().lower()
        body = kw.get("body") or ""
        found.append((variant, body))
        pos = after
    return found


def _bullet_lines_in_section(section_body: str) -> int:
    n = 0
    for line in section_body.splitlines():
        if re.match(r"^\s*[-*]\s+\S", line):
            n += 1
    return n


def _has_h3_section(md: str, title: str) -> bool:
    return bool(re.search(rf"(?m)^###\s+{re.escape(title)}\s*$", md))


def _section_after_h3(md: str, title: str) -> str | None:
    m = re.search(rf"(?ms)^###\s+{re.escape(title)}\s*$(.*?)(?=^###\s|\Z)", md)
    if not m:
        return None
    return m.group(1)


def _check_generic_instructor_body(body: str) -> list[str]:
    """Return human-readable issue strings for generic variant body."""
    issues: list[str] = []
    if not _has_h3_section(body, "FAQs"):
        issues.append("generic instructor_block body: missing ### FAQs heading")
    else:
        sec = _section_after_h3(body, "FAQs") or ""
        if _bullet_lines_in_section(sec) < 2:
            issues.append("generic instructor_block body: ### FAQs needs at least two bullet items")
    if not _has_h3_section(body, "What breaks"):
        issues.append("generic instructor_block body: missing ### What breaks heading")
    else:
        sec = _section_after_h3(body, "What breaks") or ""
        if _bullet_lines_in_section(sec) < 1:
            issues.append("generic instructor_block body: ### What breaks needs at least one bullet item")
    return issues


def _check_choreography_body(body: str) -> list[str]:
    issues: list[str] = []
    required = [
        ("Pause points", "pause points / pacing"),
        ("Narrating check-sync", "check-sync narration"),
        ("Red-to-green flip", "red-to-green flip narration"),
    ]
    for heading, label in required:
        if not _has_h3_section(body, heading):
            issues.append(f'choreography instructor_block body: missing ### {heading} ({label})')
        else:
            sec = _section_after_h3(body, heading) or ""
            if _bullet_lines_in_section(sec) < 1 and not _section_has_facilitator_content(sec):
                issues.append(f"choreography instructor_block body: ### {heading} needs facilitator content")
    return issues


def _section_has_facilitator_content(sec: str) -> bool:
    """True if section has a list bullet or a substantive prose line."""
    if _bullet_lines_in_section(sec) >= 1:
        return True
    for line in sec.splitlines():
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        if len(t) >= 4:
            return True
    return False


def lint_rule12_ux_dr30(path: Path, full_text: str) -> list[str]:
    """UX-DR30: every lab chapter has instructor_block generic minimums; Lab 8 adds choreography."""
    fm, err = _parse_frontmatter(full_text)
    chapter_n: int | None = None
    if fm is not None and not err:
        ch = fm.get("chapter")
        if isinstance(ch, int):
            chapter_n = ch
        elif isinstance(ch, str) and ch.strip().isdigit():
            chapter_n = int(ch.strip())

    scan = _text_outside_fences(full_text)
    calls = iter_instructor_block_calls(scan)
    violations: list[str] = []

    if not calls:
        violations.append(
            f"[rule 12 UX-DR30] {path.name}: missing instructor_block — "
            f"expected duration stays in frontmatter; add {{ instructor_block(...) }} with "
            f"### FAQs (2+ bullets) and ### What breaks (1+ bullet) — see {RULE12_DOC_ANCHOR}"
        )
        return violations

    generic_calls = [(v, b) for v, b in calls if v == "generic"]
    if not generic_calls:
        violations.append(
            f"[rule 12 UX-DR30] {path.name}: missing instructor_block(variant=\"generic\") "
            f"(or default generic) with ### FAQs and ### What breaks — see {RULE12_DOC_ANCHOR}"
        )
    for _, body in generic_calls:
        for issue in _check_generic_instructor_body(body):
            violations.append(f"[rule 12 UX-DR30] {path.name}: {issue} — see {RULE12_DOC_ANCHOR}")

    if chapter_n == 8:
        choreo = [(v, b) for v, b in calls if v == "choreography"]
        if not choreo:
            violations.append(
                f"[rule 12 UX-DR30] {path.name}: Lab 8 requires "
                f'instructor_block(variant="choreography") with pause / check-sync / red-to-green sections '
                f"— see {RULE12_DOC_ANCHOR}"
            )
        for _, body in choreo:
            for issue in _check_choreography_body(body):
                violations.append(f"[rule 12 UX-DR30] {path.name}: {issue} — see {RULE12_DOC_ANCHOR}")

    return violations


def lint_rule_ar15_rollback(path: Path, full_text: str) -> list[str]:
    fm, err = _parse_frontmatter(full_text)
    if err or fm is None:
        return []
    if fm.get("idempotent") is not False:
        return []
    body = _body_after_frontmatter(full_text)
    sec = _h2_sections(body)
    proc = sec.get("Procedure", "")
    ce = sec.get("Common Errors", "")
    if _section_has_rollback_with_fence(proc, ce):
        return []
    return [
        f"[AR15 rollback] {path.name}: `idempotent: false` requires `!!! warning \"Rollback\"` "
        f"with at least one fenced rollback command under `## Procedure` and/or `## Common Errors` "
        f"— see docs/authoring.md#idempotency-and-rollback"
    ]


def _paths_rule10(docs_root: Path) -> list[Path]:
    paths: list[Path] = []
    idx = docs_root / "index.md"
    if idx.is_file() and not _skip_path(idx, docs_root):
        paths.append(idx)
    for p in sorted(docs_root.glob("[0-9][0-9]-*.md")):
        if _is_chapter_candidate(p, docs_root):
            paths.append(p)
    return paths


def _paths_rules_56(docs_root: Path) -> list[Path]:
    paths = sorted(docs_root.glob("[0-9][0-9]-*.md"))
    idx = docs_root / "index.md"
    if idx.is_file() and not _skip_path(idx, docs_root):
        paths.append(idx)
    return paths


def main() -> int:
    docs_root = Path(sys.argv[1] if len(sys.argv) > 1 else "docs").resolve()
    schema_path = docs_root / "_template" / "schema.yaml"
    if not schema_path.is_file():
        print(f"ERROR: schema not found: {schema_path}", file=sys.stderr)
        return 2

    schema = _load_schema(schema_path)
    mode_13 = os.environ.get("LINT_RULES_1_3_MODE", "warn").lower()
    mode_47 = os.environ.get("LINT_RULES_4_7_MODE", "warn").lower()
    mode_56 = os.environ.get("LINT_RULES_5_6_MODE", "warn").lower()
    mode_811 = os.environ.get("LINT_RULES_8_11_MODE", "warn").lower()
    mode_12 = os.environ.get("LINT_RULES_12_MODE", "warn").lower()
    fail_13 = mode_13 == "fail"
    fail_47 = mode_47 == "fail"
    fail_56 = mode_56 == "fail"
    fail_811 = mode_811 == "fail"
    fail_12 = mode_12 == "fail"

    repo_root = _repo_root_for_lint(docs_root)
    allowed_macros = load_allowed_jinja_names(docs_root)
    url_allowlist = load_url_allowlist(repo_root)

    v13: list[str] = []
    v47: list[str] = []
    v56: list[str] = []
    w8: list[str] = []
    v811: list[str] = []
    v12: list[str] = []
    candidates = sorted(docs_root.glob("[0-9][0-9]-*.md"))

    for path in candidates:
        if not _is_chapter_candidate(path, docs_root):
            continue
        v13.extend(lint_rule2_filename(path))
        v13.extend(lint_rule1_frontmatter(path, schema))
        v13.extend(lint_rule3_headings(path))

        text = path.read_text(encoding="utf-8")
        v13.extend(lint_rule3d_time_budget(path, text))
        body = _body_after_frontmatter(text)
        lines = body.splitlines()
        v47.extend(lint_rules_4abc(path, lines))
        v47.extend(lint_rule4d_expected_output_landmark(path, lines))
        v47.extend(lint_rule7_macros(path, text, allowed_macros))

        w8.extend(lint_rule8_instructor_coherence(path))
        v811.extend(lint_rule9_hardcoded_versions(path, text))
        v811.extend(lint_rule_ar15_rollback(path, text))
        v12.extend(lint_rule12_ux_dr30(path, text))

    for path in _paths_rule10(docs_root):
        try:
            t10 = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        v811.extend(lint_rule10_classification(path, t10))

    v811.extend(lint_rule11_lab_safety(repo_root, docs_root))

    idx = docs_root / "index.md"
    if idx.is_file() and not _skip_path(idx, docs_root):
        try:
            idx_text = idx.read_text(encoding="utf-8", errors="replace")
        except OSError:
            idx_text = ""
        v13.extend(lint_rule3f_home_index(idx, idx_text))

    for path in _paths_rules_56(docs_root):
        full_text = path.read_text(encoding="utf-8", errors="replace")
        mapped = _iter_lines_outside_fences(full_text)
        v56.extend(lint_rule5_images_and_mermaid(path, full_text))
        v56.extend(lint_rule6a_internal_links(path, docs_root, mapped))
        v56.extend(lint_rule6b_external_urls(path, mapped, url_allowlist))

    def dedupe(vs: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in vs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    u13 = dedupe(v13)
    u47 = dedupe(v47)
    u56 = dedupe(v56)
    u8 = dedupe(w8)
    u811 = dedupe(v811)
    u12 = dedupe(v12)

    if u13:
        print(f"Authoring lint: {len(u13)} violation(s) (rules 1–3, mode={mode_13})")
        for v in u13:
            print(f"  {v}")
        print()
    if u47:
        print(f"Authoring lint: {len(u47)} violation(s) (rules 4–7, mode={mode_47})")
        for v in u47:
            print(f"  {v}")
        print()
    if u56:
        print(f"Authoring lint: {len(u56)} violation(s) (rules 5–6, mode={mode_56})")
        for v in u56:
            print(f"  {v}")
        print()
    if u8:
        print(f"Authoring lint: {len(u8)} warning(s) (rule 8 — always non-fatal)")
        for v in u8:
            print(f"  {v}")
        print()
    if u811:
        print(
            f"Authoring lint: {len(u811)} violation(s) (rules 9–11 + AR15 rollback, mode={mode_811})"
        )
        for v in u811:
            print(f"  {v}")
        print()
    if u12:
        print(f"Authoring lint: {len(u12)} violation(s) (rule 12 UX-DR30, mode={mode_12})")
        for v in u12:
            print(f"  {v}")
        print()

    if u13 or u47 or u56 or u8 or u811 or u12:
        print("Fix: see docs/authoring.md. Migration: Epic 4.")
        print(
            "Fail modes: LINT_RULES_1_3_MODE=fail  LINT_RULES_4_7_MODE=fail  "
            "LINT_RULES_5_6_MODE=fail  LINT_RULES_8_11_MODE=fail  LINT_RULES_12_MODE=fail"
        )
        exit_fail = (
            (bool(u13) and fail_13)
            or (bool(u47) and fail_47)
            or (bool(u56) and fail_56)
            or (bool(u811) and fail_811)
            or (bool(u12) and fail_12)
        )
        return 1 if exit_fail else 0

    print("Authoring lint: OK (rules 1–12 + AR15)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
