# PDF tests (Epic 6)

## Baseline fixture (Story 6.1)

- **`tests/fixtures/pdf/acceptance-baseline.pdf`** — Chromium output from `scripts/spike/spike-corpus.html`. Used by `make pdf-test` (AC4).

## Reproducibility (NFR-R1, Story 6.2)

Full-workbook PDFs include variable metadata (`/CreationDate`, `/ModDate`). For comparisons:

1. **Normalized SHA-256** — `scripts/pdf_build.py` prints a digest after normalizing metadata via `pypdf` (fixed dummy dates). Two builds from the same sources should yield the **same normalized hash** when using the **same Chromium version** and engine path.
2. **Cross-machine drift** — Different Chromium builds may still change content streams slightly; treat byte identity as best-effort. Page counts and `make pdf-test` are the stable gates for CI.

## `make pdf-test` (AC4)

Runs `scripts/pdf_acceptance_test.py`:

- Regenerates a one-page PDF from `scripts/spike/spike-corpus.html` with headless Chromium.
- Asserts **page count** matches `acceptance-baseline.pdf` (tolerance: exact for the spike corpus).

Requires Chrome/Chromium on `PATH`.

## WeasyPrint fallback (AR6, AC2)

Primary engine is **Chromium** on `print_page/index.html` from `mkdocs-print-site-plugin`. The **secondary** engine is **WeasyPrint** on the same HTML.

- Optional install: `pip install -r requirements-weasyprint.txt` **plus** OS libraries (GTK/Pango); on macOS, `brew install weasyprint` often provides a working `weasyprint` CLI.
- Validate fallback with:  
  `PDF_ENGINE_FORCE_FAIL=1 make pdf`  
  (expects a **stderr WARNING** that the secondary engine was used.)

If WeasyPrint cannot import on your host, use Linux CI or install native deps — the primary `make pdf` path does not require WeasyPrint.

## Instructor leakage (AC5)

After building the learner PDF, `scripts/pdf_build.py` runs:

`python scripts/check_instructor_leak.py --pdf dist/cisco-secure-services-nso-<version>.pdf`

Same regex set as HTML FR37 scanning, applied to **extracted PDF text** (limitations: code fences are not stripped like HTML).

## PDF chrome (Story 6.3)

After `make build-learner` (or `mkdocs build`), the combined print HTML is `site/print_page/index.html`.

**Automated / structural checks:** `python -m unittest scripts.tests.test_print_css_smoke` asserts `docs/assets/css/print.css` exists, `mkdocs.yml` references it and enables the print-site cover, and `_data/site.yaml` defines `bug_report_url`.

**Manual / visual (remaining for 6.4–6.5):**

- **Cover** — Course title, **NSO** version, **UTC build date**, prominent **Cisco Confidential**, and a working **bug-report** link (from `_data/site.yaml`).
- **Body pages** — Running footer via injected `@page` CSS: **Cisco Confidential** + **NSO** version (aligned with `_data/versions.yaml`); first PDF page (cover) clears margin text so the banner is not duplicated in the margin.
- **Layout** — Code blocks and tables do not clip off the page; headings avoid awkward splits where the browser allows.
- **Tagged PDF / bookmarks / veraPDF** — Out of scope for 6.3; covered in Stories **6.4** and **6.5**.

## PDF accessibility (Story 6.4)

- **Tagged PDF:** Headless Chromium’s `--print-to-pdf` output includes **`/MarkInfo` → Marked** and a **`/StructTreeRoot`** (verify with a PDF library or Acrobat). The finalize step **must not** use `PdfWriter.append()` alone — it drops tags; this repo uses **`PdfWriter(clone_from=...)`** inside **`scripts/pdf_finalize_accessibility.py`**.
- **Bookmarks:** Built from **`site/print_page/index.html`**: every **`h1`** and **`h2`** under `#print-site-page`, in DOM order, with destinations resolved by forward substring search on `extract_text()` per page.
- **Metadata:** **`/Lang`** = `en-US`, **`/Title`** = `site_name` from **`mkdocs.yml`**.
- **Reading order:** Forward-only page matching enforces bookmark order consistent with pagination; spot-check with Acrobat or **`pdftotext`** when Poppler is installed.
- **Figures / alt text:** Chromium’s tag tree should carry alt text from HTML; deep **`Figure` /Alt** validation is the focus of **Story 6.5 (veraPDF)**.

## veraPDF + bookmarks (Story 6.5)

- **CI:** `.github/workflows/build.yml` builds the learner PDF, installs veraPDF (`scripts/ci/install-verapdf-ubuntu.sh`), runs **`scripts/ci/run_verapdf.sh`** (PDF/UA-1, XML report), and **`scripts/ci/validate-pdf-bookmarks.py`**. Reports upload as the **`pdf-quality-reports`** artifact.
- **Strict UA gate:** In CI, **`VERAPDF_NON_BLOCKING=1`** is set until remaining PDF/UA issues (e.g. link annotation `Contents`) are fixed; set **`VERAPDF_NON_BLOCKING=0`** (or unset) locally / in workflow to fail the job on veraPDF exit **1**.
- **Local:** See **`CONTRIBUTING.md`** (PDF CI gates).

## Distribution checks (Story 6.6)

After **`make build-learner`** and **`make pdf`**:

- **`scripts/ci/check-external-resources.py`** — allowlist in **`scripts/ci/external-allowlist.yaml`**; blocks known-bad hosts (e.g. Google Fonts CDNs) and fails on unexpected external links in HTML + PDF annotations.
- **`scripts/ci/check-classification.py`** — ensures Cisco Confidential banner/phrase on every HTML page and (by default) on every PDF body page after the cover.

**Tests:** `python -m unittest scripts.tests.test_check_external_resources scripts.tests.test_check_classification -v`
