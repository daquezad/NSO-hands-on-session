# NSO Hands-On Training Workbook

Cisco Network Services Orchestrator — Hands-On Lab Guide built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

**Repository:** [github.com/daquezad/NSO-hands-on-session](https://github.com/daquezad/NSO-hands-on-session) · `git clone https://github.com/daquezad/NSO-hands-on-session.git`

## Local Development

```bash
pip install -r requirements.txt
make serve                 # learner site (default http://127.0.0.1:8000)
# make serve-instructor    # facilitator content (INSTRUCTOR=1, default :8001)
# make build-all           # static builds → site/ and site-instructor/
```

Open the URL printed by the command (defaults to `http://127.0.0.1:8000` for `make serve`).

## Deployment

Push to `main` branch — GitHub Actions automatically builds and deploys to GitHub Pages.

## Adding Screenshots

Place images in `docs/assets/images/` and reference them in Markdown:

```markdown
![Description](assets/images/filename.png)
```

## Pull requests

Opening a PR against `main` runs **lint** (warn mode by default), **learner** MkDocs build, **`check_noindex.py`**, **Story 3.11 gates** (`check_perf_budget.py`, `check_internal_links.py`, Lighthouse performance on home + Lab 8, axe warn-only), then the **instructor** build and its noindex check. PR titles must follow **Conventional Commits** (see `CONTRIBUTING.md`). Node **20** + `npm ci` install pinned **Lighthouse** and **@axe-core/cli** (`package-lock.json`).

## Updating Content

Edit any `.md` file in `docs/`, commit, and push. The site rebuilds automatically.

## Repository layout

- `docs/` — Markdown source for the learner workbook (9 lab chapters + `index.md`). Facilitator-only paths: `docs/instructor-artifacts/` and `docs/*-instructor-notes.md` (included only in `make build-instructor`).
- `docs/assets/images/` — screenshots and rendered diagrams referenced by relative paths from chapter Markdown (FR5).
- `docs/assets/mermaid-sources/` — Mermaid `.mmd` sources + `.alt.txt` (Story 3.5); run `make pre-render-mermaid` to regenerate committed assets under `docs/assets/images/mermaid/`.
- `docs/assets/images/mermaid/` — pre-rendered SVG + PNG + alt text for `{{ topology() }}` (Story 3.5).
- `docs/assets/fonts/` — locally-bundled Cisco-fallback fonts (populated in Story 1.3) so the site renders correctly offline (NFR-S3).
- `docs/stylesheets/extra.css` — Cisco-branded design token layer (Story 1.4); global application of link/code/focus/reduced-motion tokens (Story 3.2).
- `overrides/` — Material theme Jinja2 overrides (Cisco Confidential banner, NSO-version header/footer — populated in Story 3.1).
- `main.py` — shim required by `mkdocs-macros` (`module_name: main`); loads `macros/main.py` (UX-DR20 `nso_version`, section primitives in Story 3.4, future instructor/component macros — Stories 5.1, 5.3).
- `macros/main.py` — `define_env` and macros (`expected_output`, `time_budget`, `common_errors_*`, `lab_safety`, `topology`, `home_subtitle`, `home_meta`, `journey_table`, …) consumed via `main.py`.
- `hooks.py` — post-build sitemap removal; **paired** command/output transform (Story 3.3); optional **cwebp** WebP + `<picture>` wrap for PNG screenshots (Story 3.5); **skip links** + `#workbook-navigation` / `#verification` landmarks (Story 3.7); **`on_files`** drops `docs/instructor-artifacts/**` and `docs/*-instructor-notes.md` on learner builds only (Story 5.1 / AR5).
- `docs/a11y-log.md` — WCAG 2.1 AA spot-check log (Story 3.7).
- `docs/responsive-check-log.md` — narrow-viewport / touch spot-check log (Story 3.10).
- `docs/scrub-protocol.md` — screenshot/diagram identifier scrub (FR45, NFR-S6, Story 4.1); `docs/scrub-logs/` for per-chapter and second-pair logs.
- `scripts/pre_render_mermaid.py` — Mermaid CLI → SVG/PNG (Story 3.5).
- `scripts/optimize_images.py` — optional **oxipng** + per-folder size warnings (Story 3.5).
- `scripts/check_noindex.py` — verifies `noindex,nofollow` on every built page and no `sitemap.xml` (Story 3.8).
- `scripts/check_perf_budget.py` / `scripts/check_internal_links.py` — NFR-P5 / NFR-R4 (Story 3.11).
- `scripts/check_lighthouse_performance.py` / `scripts/check_axe_warn.py` — Lighthouse floor + axe warn-only (Story 3.11).
- `scripts/ci/run_quality_gates.sh` — orchestrates gates after `make build-learner` (used by CI and `make ci-quality-gates`).
- `scripts/rollback-lab.sh` — invoked via `make rollback-lab LAB=N` (Story 3.9); see `docs/reset-lab.md`.
- `docs/javascripts/paired.js` — copy acknowledgment + global `aria-live` announcer (Stories 3.3 + 3.7).
- `scripts/` — Python build helpers (authoring lint, leakage guard, external-resource check, classification check — populated across Epics 2, 5, 6).
- `.github/workflows/` — **`build.yml`** (PR + `main`: full CI via **`_build.yml`**), **`deploy.yml`** (**`mike deploy`** to **`gh-pages`** after green **`Build` on `main`** + PDF artifact), **`release.yml`** (`v*` → **`mike`** `latest` + default + Release). Shared setup: **`.github/actions/setup-toolchain`** (Stories 6.7–6.8). Internal deploy notes: **`docs/_internal/deploy.md`**.
- `package.json` / `package-lock.json` — pinned **Lighthouse** + **@axe-core/cli** for CI (Story 3.11).
- `Makefile` — single-command contributor targets (`make build-learner`, `make pdf-learner`, etc. — wired in Story 1.5).
- `mkdocs.yml` — MkDocs configuration (extended incrementally across stories; untouched in 1.1).
- `requirements.txt` — Python dependencies (exact-pinned in Story 1.2; untouched in 1.1).
