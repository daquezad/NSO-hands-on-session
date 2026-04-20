## Common tasks

Run these from the project root after `pip install -r requirements.txt`:

| Target | Purpose |
|--------|---------|
| `make build-learner` | Build learner site → `site/` (instructor content excluded) |
| `make build-instructor` | Build instructor site → `site-instructor/` (all content, INSTRUCTOR=1) |
| `make build-all` | Build learner + instructor sites, dual-audience smoke (5.3), FR37 leakage scan (5.6) |
| `make check-instructor-leak` | Scan `site/` for instructor-only markers (`scripts/check_instructor_leak.py`, FR37) |
| `make pdf` | Learner PDF → `dist/cisco-secure-services-nso-{version}.pdf` (`mkdocs-print-site-plugin` + Chromium; optional WeasyPrint fallback — Story 6.2; Story 6.4 post-process adds bookmarks + metadata) |
| `make pdf-test` | Spike corpus PDF page-count check vs `tests/fixtures/pdf/acceptance-baseline.pdf` (6.2 AC4) |
| `make pdf-learner` | Alias for `make pdf` |
| `make pdf-instructor` | Instructor PDF → `dist/cisco-secure-services-nso-{version}-instructor.pdf` |
| `make serve` | Live-reload dev server (learner variant; default `127.0.0.1:8000`) |
| `make serve-instructor` | Live-reload with facilitator content (`INSTRUCTOR=1`; default `127.0.0.1:8001`) |
| `make lint` | Run authoring lint (default **warn** mode — Epic 4 migration) |
| `make lint-fail-all` | Same linter with **all** rule groups in **fail** mode (dry run / cutover) |
| `make clean` | Remove `site/` and `site-instructor/` |
| `make help` | Print this table |

See `docs/authoring.md` for the full onboarding quickstart and content contract. See **`docs/lint-cutover-plan.md`** for warn → fail rollout and CI notes (Story 2.7).

### GitHub Actions workflows (Stories 6.7–6.9, AR9)

Three workflows — each file is a separate entrypoint:

| Workflow | Trigger | Role |
|----------|---------|------|
| **`build.yml`** | Pull requests and pushes to **`main`** | Full CI via reusable **`_build.yml`** (learner + instructor sites, PDF, veraPDF, bookmarks, 6.6 checks, quality gates). PRs also enforce Conventional Commit **titles**. |
| **`deploy.yml`** | After a successful **`Build`** run on a **`push` to `main`** | Rebuilds the same commit, uploads the learner PDF as an artifact, runs **`mike deploy`** to the **`gh-pages`** branch (NSO version + **`main`** alias — rolling docs from `main`), and runs a **private Pages** smoke check (warns if anonymous GET returns **200**). |
| **`release.yml`** | Push of a tag matching **`v*`** | Runs **`ci`** first — if anything fails, **no** Release and **no** **`mike`** (Story **6.9 AC6**). On success: release notes + checklist + **`CHANGELOG.md`** update, **`mike deploy`** / **`set-default`**, **GitHub Release** (PDF + checklist), then commits **`CHANGELOG.md`** to **`main`**. |

Shared install steps live in **`.github/actions/setup-toolchain`**; the full job is **`.github/workflows/_build.yml`** (`workflow_call`) so **`build.yml`** and **`release.yml`** stay DRY.

**Accessibility (Story 6.10):** CI sets **`AXE_MODE=warn`** on the build job (axe still runs; serious/critical do not fail the job). The merged report is uploaded as **`axe-report-{run_id}.json`**. To block merges on **serious/critical** axe findings, set **`AXE_MODE: fail`** in **`.github/workflows/_build.yml`**. Authoring **lint rule 12** (instructor-block macro) runs in **fail** mode in CI. Details: **`docs/_internal/accessibility.md`**.

**v1.0 release gates (PRD):** calendar checklist (**v0.7 → v0.9 → v1.0**) — **`docs/_internal/v1-release-checklist.md`** (not in the published site).

**Repo settings (Pages):** Use **Deploy from a branch** → **`gh-pages`** → **`/(root)`** — **not** “GitHub Actions” static upload (Story **6.7** OIDC deploy was replaced by **`mike`** in **6.8**). Set **Pages visibility** to **private** to the org where required (FR33). Details: **`docs/_internal/deploy.md`**.

**Versioning:** **`mike`** is configured in **`mkdocs.yml`** (`plugins.mike`, `extra.version.provider: mike`). **`SITE_URL`** is set in CI for correct redirects; locally use e.g. **`SITE_URL=http://127.0.0.1:8000/ mkdocs serve`** (default in **`mkdocs.yml`** matches this).

### Cutting a release (Story 6.9, FR35/FR36)

1. Ensure **`main`** is green (**`build.yml`**).
2. Create an annotated or lightweight tag: **`git tag v0.4.0`** and **`git push origin v0.4.0`** (semver after **`v`**).
3. **`release.yml`** builds notes from **`git log`** since the previous tag, attaches **`release-checklist-{tag}.md`** and the learner PDF, and updates **`CHANGELOG.md`** on **`main`** (requires **`contents: write`** and a **`main`** branch that allows the GitHub Actions bot to push — adjust branch protection if needed).
4. Rollback: **`docs/_internal/rollback.md`**.

### PDF metadata (`_data/site.yaml`, Story 6.3)

- **`bug_report_url`** — Pre-filled issue URL for the PDF cover “Report an issue” link (GitHub `template` / `title` / `labels` query params as needed). Forks can point this at an internal tracker without code changes.
- **`hooks.py`** merges this file into MkDocs `extra` at build time. **`_data/versions.yaml`** remains the canonical **`nso_version`** for filenames and footers (keep it aligned with `extra.nso_version` in `mkdocs.yml` for humans).
- **Build date (UTC)** on the PDF cover comes from `extra.pdf_build_date`: use **`SOURCE_DATE_EPOCH`** (seconds since Unix epoch) for reproducible timestamps; otherwise the build uses the current UTC date.

### PDF CI gates (Story 6.5)

After **`make pdf`** (or CI’s PDF build step):

1. **veraPDF** — PDF/UA-1 (`-f ua1`), XML report. Install on Ubuntu with **`bash scripts/ci/install-verapdf-ubuntu.sh`** (unpacks the official installer to `/opt/verapdf`). Run: **`bash scripts/ci/run_verapdf.sh dist/cisco-secure-services-nso-<ver>.pdf`**.  
   - **`VERAPDF_NON_BLOCKING=1`** — report only; exit 0 even if the PDF is not fully UA-compliant (used in CI until link/annotation remediation lands).  
   - Omit that variable to **fail** on non-zero veraPDF exit (strict gate).
2. **Bookmarks** — **`python3 scripts/ci/validate-pdf-bookmarks.py dist/cisco-secure-services-nso-<ver>.pdf --report bookmark-report.txt`**. Fails if bookmark count &lt; nav `.md` leaf count from **`mkdocs.yml`**.
3. **External resources** — **`python3 scripts/ci/check-external-resources.py site dist/cisco-secure-services-nso-<ver>.pdf`**. Scans built HTML and PDF link annotations for `http(s)://` hosts; fails on **`scripts/ci/external-allowlist.yaml`** `blocked_hosts` (e.g. Google Fonts) or any host not listed under `hosts`.
4. **Classification** — **`python3 scripts/ci/check-classification.py site dist/cisco-secure-services-nso-<ver>.pdf`**. Every HTML page must include **`css-classification-banner`** or the phrase **Cisco Confidential**; the learner PDF must contain that phrase on every page after the cover (use **`--no-skip-cover`** to require it on page 1 as well).

Short internal index (not part of the published MkDocs site): **`docs/_internal/contributing.md`**.

### PDF accessibility finalize (Story 6.4)

- After Chromium/WeasyPrint writes the PDF, **`scripts/pdf_finalize_accessibility.py`** runs (via **`scripts/pdf_build.py`**) unless **`PDF_SKIP_A11Y=1`**. It uses **`PdfWriter(clone_from=reader)`** so **tagged structure** (`/StructTreeRoot`, `/MarkInfo`) from Headless Chrome is preserved, adds a **bookmark outline** for every **H1/H2** on the print page (matched forward through the page list), and sets **`/Lang`** to **`en-US`** and document **`Title`** from `site_name` in **`mkdocs.yml`**.
- Run standalone: `python scripts/pdf_finalize_accessibility.py dist/cisco-secure-services-nso-<ver>.pdf --print-html site/print_page/index.html` (after `mkdocs build`).

### Conventional Commits (AR19)

PR titles must follow **Conventional Commits** so squash-merged history stays readable (enforced in **`.github/workflows/build.yml`**):

```text
<type>(<scope>): <subject>
```

- **Types:** `feat`, `fix`, `docs`, `chore`, `ci`, `refactor`, `lint`, `content`
- **Scope (examples):** chapter `ch03`, `scripts`, `workflow`, `repo`, component area — use lowercase, short, and consistent within the repo.
- **Subject:** imperative mood, no trailing period in the one-line title.

Examples: `docs(ch03): clarify sync-from steps`, `ci(repo): add PR build workflow`, `content(ch07): tighten verification`.

**Merge strategy:** This project assumes **Squash and merge** on `main`, with the **PR title** becoming the default commit subject — so the PR title is what CI validates. Per-commit message hooks are optional; if you later move off squash-merge, add something like **commitlint** in CI (follow-up).

**Local hook (optional):** install the sample hook so `git commit` rejects non-conforming messages:

```bash
./scripts/install-hooks.sh
```

Hook script: `scripts/hooks/commit-msg` (merge/revert commits are allowed through).

### Authoring lint (AR13)

`make lint` runs `scripts/lint_authoring.py` against `docs/`. **Default: warn mode** — violations are printed but the process **exits 0** so brownfield chapters can migrate in Epic 4 without blocking merges.

To treat structural violations as build failures locally:

```bash
LINT_RULES_1_3_MODE=fail make lint
```

Rules **4–7** (code fences, input/output pairing, bare commands, macro names) use a separate flag (default **warn**):

```bash
LINT_RULES_4_7_MODE=fail make lint
```

Rules **5–6** (image/Mermaid alt text, internal link resolution, external URL allowlist in `scripts/url_allowlist.txt`) use:

```bash
LINT_RULES_5_6_MODE=fail make lint
```

Rules **9–11** and **AR15 rollback** (hardcoded versions, classification literal, lab-safety banner wiring, rollback admonition for non-idempotent labs) use:

```bash
LINT_RULES_8_11_MODE=fail make lint
```

Rule **12** (UX-DR30 — `instructor_block` generic minimums; Lab 8 choreography) uses:

```bash
LINT_RULES_12_MODE=fail make lint
```

Rule **8** (instructor inline vs companion notes) prints warnings only; it never fails the process.

Promotion to **fail mode in CI** is switching the workflow step from `make lint` to `make lint-fail-all` (see `docs/lint-cutover-plan.md`) after Epic 4 migration.

Run tests:

```bash
python -m unittest scripts.tests.test_lint_authoring -v
python -m unittest discover scripts/tests -v
```

Optional WeasyPrint fallback (for `PDF_ENGINE_FORCE_FAIL=1` / AR6): install OS libraries per [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation), then `pip install -r requirements-weasyprint.txt` (exact pin).

---

## Dependency pinning rules

This repo enforces **exact version pins** on every Python dependency (NFR-S4, AR2). This is the supply-chain integrity contract for the NSO Hands-On Training Delivery System.

**Rules:**

1. Every entry in `requirements.txt` must use `==` — no `>=`, `~=`, `>`, `<`, `*`, or unpinned lines.
2. New dependencies require: (a) exact version pin, (b) architecture sign-off on the PR, (c) a PR comment justifying why the dep is needed and what alternatives were considered.
3. Chromium version is pinned in `scripts/chromium.lock`; bumps follow the same rules as `requirements.txt`.
4. Python version is pinned in `.python-version`; changes require architecture + CI sign-off.
5. Automated lint enforcement for rule 1 lands in Epic 2 (authoring lint). Until then, reviewers **must** reject PRs that add unpinned dependencies.

**Why these rules exist:** Two CI builds of the same commit SHA 24 hours apart must produce structurally-identical site and PDF artifacts (NFR-R1, FR35). Unpinned dependencies can resolve to different versions between the two runs, breaking that guarantee.
