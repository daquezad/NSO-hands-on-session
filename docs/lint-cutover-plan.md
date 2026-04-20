# Authoring lint — warn → fail cutover plan

This document tracks **AR13** rules and the **AR15** rollback extension: current enforcement mode, what blocks in CI today, and how to move to full **fail** mode after Epic 4 brownfield migration.

**Related:** `CONTRIBUTING.md` (lint env vars, Conventional Commits), `scripts/lint_authoring.py`, `make lint` / `make lint-fail-all`.

## CI today (Story 2.7)

| Check | Behavior |
|-------|----------|
| `make lint` | Default **warn** for all rule groups — prints violations, **exit 0** so PRs stay mergeable during migration. |
| `make lint-fail-all` | Sets every `LINT_RULES_*_MODE=fail` (including **rule 12**) — use locally or in CI when you want a **full enforcement dry run** (Epic 4 backlog sizing). |
| PR title | **Conventional Commits** (AR19) enforced in `.github/workflows/build.yml` — invalid titles **fail** the workflow. |

To **block merges on lint violations**, change the workflow step from `make lint` to `make lint-fail-all` after content is green (or per-group by exporting only the modes you want to enforce).

## Rule inventory and modes

| ID | Scope | Default mode | Env var | Notes |
|----|--------|--------------|---------|--------|
| 1–3, 3d, 3f | Structure | warn | `LINT_RULES_1_3_MODE` | Frontmatter schema, filename, headings; **3d** — `time_budget(...)` on chapters; **3f** — `docs/index.md` home cover (Story 3.6) |
| 4a–d, 7 | Fences / macros | warn | `LINT_RULES_4_7_MODE` | Language tags, expected output, bare commands, `expected_output` landmark (Story 3.3), Jinja macro name references (rule 7) |
| 5–6 | Alt / links / URLs | warn | `LINT_RULES_5_6_MODE` | Allowlist: `scripts/url_allowlist.txt` |
| 8 | Instructor coherence | **warning only** | — | Never fails exit code; listed under `LINT_RULES_8_11_MODE` group for messaging |
| 9–11, AR15 | Versions, classification, lab safety, rollback | warn | `LINT_RULES_8_11_MODE` | Rule 11 includes **Story 3.4** `lab_safety` placement (index + Lab 8 only); rule 8 warnings print in the same rollout window |
| 12 | UX-DR30 instructor_block (generic FAQs + What breaks; Lab 8 choreography) | warn | `LINT_RULES_12_MODE` | Story 5.7 — lands **warn-first**; chapters need `instructor_block` backfill (Epic 4 residuals or pre–v1.0 content passes) |

**Rule 8** does not set a fail bit; only rules **9–11** and **AR15** in the `8_11` group respect `LINT_RULES_8_11_MODE=fail`.

**Rule 12** respects `LINT_RULES_12_MODE=fail` independently (not bundled with the `8_11` group).

## Planned cutover (fill in at release planning)

| Milestone | Target | Actions |
|-----------|--------|---------|
| Epic 4 complete | 2026-04-17 (labs 1–9 migrated) | Enable `lint-fail-all` in CI when ready; `make lint` is clean in warn mode with zero violations. |
| Post-migration | TBD | Optionally split CI: fail on `1_3` first, then `4_7`, etc. |
| Rule 12 (UX-DR30) | Story 5.7 (2026-04-17) | Shipped **warn** by default; track instructor-block backfill per lab; promote with Epic 6 release gate when `make lint-fail-all` is green for rule 12 |

Update this table when enforcement dates are agreed; optional follow-up is automated drift detection between this doc and `lint_authoring.py` (nice-to-have).

## Epic 4 — chapter migration vs lint (rolling)

| Lab | File | `lint-fail-all` clean for this chapter alone | Notes |
|-----|------|---------------------------------------------|--------|
| 1 | `docs/01-connect-workstation.md` | Yes (2026-04-17) | Reference chapter: AR14 frontmatter, mandatory H2 order, `time_budget`, paired I/O + `expected_output`, `common_errors_*`, scrub log + placeholder PNG under `assets/images/01/`. |
| 2 | `docs/02-install-nso-neds.md` | Yes (2026-04-17) | `idempotent: false` + AR15 `!!! warning "Rollback"` with fenced commands; `{{ nso_version }}` in command paths; scrub log. |
| 3 | `docs/03-register-xrd-routers.md` | Yes (2026-04-17) | Devices + sync-from; scrub log. |
| 4 | `docs/04-configure-devices.md` | Yes (2026-04-17) | Web UI + device CLI; doc-range example IPs; scrub log. |
| 5 | `docs/05-rollbacks.md` | Yes (2026-04-17) | Commit Manager + device verify; scrub log. |
| 6 | `docs/06-out-of-band-sync.md` | Yes (2026-04-17) | Title aligned to nav “Out-of-Band Sync”; scrub log. |
| 7 | `docs/07-device-groups-templates.md` | Yes (2026-04-17) | Groups + apply-template; scrub log. |
| 9 | `docs/09-rbac-access-control.md` | Yes (2026-04-17) | AAA + NACM; XPath examples; scrub log. |
| 8 | `docs/08-create-service.md` | Yes (2026-04-17) | **`lab_safety(intentional_failure)`**; `idempotent: false` + AR15 rollback; python-and-template **STATIC** service; scrub log. |
