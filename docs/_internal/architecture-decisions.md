# Architecture decisions (internal)

Epic 6 Story 6.1 adds **ADR-006**; broader ADR set remains in `_bmad-output/planning-artifacts/architecture.md`.

## ADR-006 — PDF render engine selection (AR6)

- **Status:** Accepted (spike complete, 2026-04-20)
- **Context:** Need a primary PDF engine and a documented fallback before wiring `make pdf` (Story 6.2). NFR-A2 (PDF/UA), FR20–FR26, and **AR6** apply.
- **Decision:**
  - **Primary:** Chromium headless, `--print-to-pdf`, on HTML produced for publication (print-site / learner build semantics).
  - **Fallback:** WeasyPrint on **simplified or print-specific HTML**, not raw Material theme pages if compatibility fails.
- **Consequences:** CI should pin Chromium channel where possible; WeasyPrint validated on Linux; veraPDF gate in 6.5.
- **Evidence:** `docs/_internal/pdf-engine-spike.md`

## ADR-007 — PDF artifact path and version source (Story 6.2)

- **Decision:** Learner PDF output is **`dist/cisco-secure-services-nso-{nso_version}.pdf`** where **`nso_version`** is read from **`_data/versions.yaml`** (kept in sync with `extra.nso_version` in `mkdocs.yml`). Instructor variant uses the same basename with a **`-instructor`** suffix.
- **Rationale:** Aligns Epic 6.2 FR22 naming with a single checked-in version file; `make pdf` / `scripts/pdf_build.py` implement this layout.
