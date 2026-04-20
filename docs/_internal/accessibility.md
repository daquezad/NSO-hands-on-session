# Accessibility CI — axe warn vs fail (internal)

Story **6.10** — **AR21**, **FR39**, WCAG 2.1 AA target.

## Current behaviour

- **`scripts/check_axe_warn.py`** runs **`@axe-core/cli`** against URLs listed in **`scripts/ci/axe-pages.yaml`** (sample pages; expand as needed).
- **`AXE_MODE`** (environment):
  - **`warn`** (default in **`.github/workflows/_build.yml`**) — prints violations, writes **`axe-report-{run_id}.json`**, exits **0** even when issues exist (pre‑v1.0).
  - **`fail`** — exits **non-zero** if any violation has **`impact`** **`serious`** or **`critical`** (blocks merge).

## When to flip to fail mode

Cut over when:

1. **`axe-report-*.json`** shows **zero** `serious` / `critical` violations on **every page** listed in **`axe-pages.yaml`**, and
2. Spot-checks on long chapters agree (expand **`axe-pages.yaml`** toward full nav before locking v1.0).

**Procedure:** In **`.github/workflows/_build.yml`**, set:

```yaml
env:
  AXE_MODE: fail
```

at **job** level (or only on the **`quality_gates`** step via `scripts/ci/run_quality_gates.sh` — same variable is read by **`check_axe_warn.py`**).

## Screen readers

Release notes carry a **Screen reader compatibility** matrix (Story **6.9**). Deep PDF/UA work remains with **veraPDF** (Story **6.5**).

## Related

- **`scripts/ci/a11y_baseline.yaml`** — optional violation **count** ceilings for **warn** mode (baseline drift warnings).
- **`docs/_internal/rollback.md`** — if a bad release must be pulled back.
- **`docs/_internal/v1-release-checklist.md`** — when to tighten CI vs cohort sign-off (**v0.9** / **v1.0**).
