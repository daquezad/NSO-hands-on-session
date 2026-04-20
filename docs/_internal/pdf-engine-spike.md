# PDF engine spike — Chromium headless vs WeasyPrint (Story 6.1)

**Status:** Complete (spike). **Date:** 2026-04-20. **Host used for Chromium:** macOS 15.4 (Darwin arm64).

This document satisfies **AC1–AC2** for Epic 6 Story 6.1 and **AR6** (primary + fallback engines). It does **not** change `mkdocs.yml` or CI (Story 6.2+).

## Input corpora

### A — Controlled corpus (both engines)

- **File:** `scripts/spike/spike-corpus.html` (standalone HTML + minimal CSS).
- **Purpose:** Apples-to-apples timing and size without MkDocs/Material complexity.
- **Engines:** Chromium headless and WeasyPrint (Debian bookworm Docker image, see below).

### B — Production-like sample (Chromium only)

- **Source:** `mkdocs build` then `site/08-create-service/index.html` (longest / most complex lab chapter in the repo at spike time: **Lab 8**, ~298 lines source MD).
- **WeasyPrint:** Rendering **failed** on this file (see § Risks). Metrics below are **Chromium-only** for corpus B.

## Environment versions

| Component | Version / notes |
|-----------|------------------|
| Google Chrome (headless) | 147.0.7727.56 |
| WeasyPrint (Debian `apt`) | 57.2 (Docker `python:3.12-slim-bookworm`; `apt install weasyprint`) |
| Chromium CLI | `--headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf=OUT.pdf file://INPUT` |

## Metrics

### Corpus A (`spike-corpus.html`)

| Metric | Chromium headless | WeasyPrint |
|--------|-------------------|------------|
| Wall time (measured) | ~2.4 s (includes cold Chrome startup on laptop) | ~0.35 s (Docker, after image `apt install`) |
| Output size | 97,263 bytes | 17,219 bytes |
| Pages (macOS Spotlight `kMDItemNumberOfPages`) | 1 | 1 |
| Bookmarks / outline | Not populated for this CLI (single page; outline N/A) | Empty outline for simple doc |
| Code blocks / table / link | Visually preserved in both PDFs | Preserved |
| Tagged PDF / PDF/UA | Chromium emits modern PDF (1.7-class); tag tree not validated in this spike (veraPDF in **6.5**). WeasyPrint 57.x generates structured output; full **PDF/UA-1** gate deferred to CI. | Same |

### Corpus B (Lab 8 `index.html`, Chromium only)

| Metric | Chromium headless |
|--------|-------------------|
| Wall time | ~4–5 s (one-off run; not benchmark-grade) |
| Output size | ~331 KB |
| Pages | 9 |
| WeasyPrint | **Error:** `KeyError: ('none',)` in list marker / `display` handling with Material-generated DOM/CSS (WeasyPrint 57.2). |

## Recommendation (AR6)

| Role | Engine | Rationale |
|------|--------|-----------|
| **Primary** | **Chromium headless** (`--print-to-pdf`) | Matches `_bmad-output/planning-artifacts/architecture.md` Decision 2; renders **full MkDocs Material HTML** for Lab 8 without a separate HTML sanitizer; multi-page PDF with acceptable size; aligns with `mkdocs-print-site-plugin` + print CSS direction for **6.2**. |
| **Fallback** | **WeasyPrint** (current stable ≥ 66 in CI when available; spike used **57.2** from Debian for comparison) | Strong semantic HTML → PDF path for **tagging** per upstream docs; **must** consume **print-pipeline HTML** (single-page / simplified) — **not** raw theme `index.html`. On macOS, native WeasyPrint needs Pango/Cairo (Homebrew); Linux CI matches architecture assumptions. |

**Non-goals for this spike:** Wiring `make pdf`, veraPDF, bookmark validator — **Stories 6.2–6.5**.

## Acceptance baseline (AC3)

- **Path:** `tests/fixtures/pdf/acceptance-baseline.pdf`
- **Contents:** Chromium render of **corpus A** (`spike-corpus.html`), committed so **6.2** can hash/diff deterministically.
- **Scope note:** Full-workbook PDF will differ; this fixture is a **small reproducible** artifact, not the final manual.

## Risks and follow-ups

1. **WeasyPrint + Material HTML:** Direct render of built chapter HTML is **not** reliable today; fallback path should use HTML produced for **print** (expected from print-site workflow in **6.2**).
2. **Tagged PDF hard gate:** Run **veraPDF** PDF/UA-1 in CI (**6.5**) on Chromium output; if unsatisfactory, activate WeasyPrint fallback per architecture.
3. **Instructor leakage:** Learner PDF must stay clean of facilitator markers — **5.6** HTML guard extends to PDF text in **6.2** / release gate.

## How to reproduce

See `scripts/spike/README.md`.
