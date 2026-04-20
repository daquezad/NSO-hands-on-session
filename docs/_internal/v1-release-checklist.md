# v1.0 release readiness (internal)

Aligned with **`_bmad-output/planning-artifacts/prd.md`** (Phase 1 calendar gates) and current CI (**Stories 6.7–6.10**). Not published in MkDocs (`docs/_internal/**` is excluded from the learner site).

**Owners:** fill names/dates in the sign-off rows. Use this as the single place to track **v0.7 → v0.9 → v1.0** before tagging and running the first production cohort.

---

## v0.7 — Delight moment + PDF AA confidence (“make-or-break”)

**Target:** Lab 8 choreography is reliable on the **real lab VM**; PDF tag-tree / UA posture is credible enough to stop iterating on the engine and focus on content.

### Lab 8 (real VM)

- [ ] Drift introduced on IOS-XR (or target device per lab) as written in the chapter.
- [ ] `check-sync` shows the expected failure/red path.
- [ ] `re-deploy` restores intended state; learner can verify on device.
- [ ] Timing matches published time budget (adjust chapter or budget if not).
- [ ] Proctor notes (instructor blocks) match what you actually say/do.

### PDF / accessibility (engineering)

- [ ] `make pdf` artifact opens offline; images, nav, classification present (**FR20–FR26** intent).
- [ ] `pdf_finalize_accessibility` path acceptable; bookmark count vs nav validated in CI (**Story 6.5**).
- [ ] veraPDF report reviewed (CI may be non-blocking — decide if v0.7 requires **strict** `VERAPDF_NON_BLOCKING` off for sign-off).
- [ ] Spot-check: headings, lists, tables, alt text on a sample of print pages.

### Sign-off

| Role | Name | Date |
|------|------|------|
| Author / builder | | |
| Notes | | |

---

## v0.9 — Full content + human gates

**Target:** All material ready for a real session; legal/brand and accessibility spot-checks done.

### Content (9 labs + home/appendices)

- [ ] Every lab chapter follows the template (objectives, time, prereqs, procedure, verification, common errors, lab-safety where required).
- [ ] `docs/index.md` and nav match delivery agenda.
- [ ] Instructor blocks complete enough for a non-author facilitator (per PRD scope).
- [ ] Reset-the-lab appendix tested on a real VM (**PRD risk mitigation**).

### Screenshots & scrub

- [ ] All in-repo screenshots scrubbed per **`docs/scrub-protocol.md`** (and logs in **`docs/scrub-logs/`** as you use them).
- [ ] **10% random sample** reviewed by a second engineer (PRD); issues fixed or waived with rationale.

### Brand / legal / classification

- [ ] Site + PDF covers, footer, classification banner — **formal brand/legal review** complete (PRD **v0.9** gate).
- [ ] `bug_report_url` and support path in **`_data/site.yaml`** / cover acceptable to reviewers.

### Accessibility (spot-check #2)

- [ ] Site: keyboard nav, focus, landmarks, copy buttons — checked on representative pages.
- [ ] PDF: spot-check with Acrobat/screen reader or internal process; document outcome in **`docs/a11y-log.md`** or equivalent.
- [ ] CI: decide whether to flip **`AXE_MODE: fail`** in **`.github/workflows/_build.yml`** before or immediately after v1.0 cohort (**`docs/_internal/accessibility.md`**).

### Timing & rehearsal

- [ ] Full **3-hour** timing rehearsal with at least one stand-in learner or dry-run; adjust labs 4–7 only if rehearsal proves schedule impossible (**PRD contingency** — protect Lab 8).
- [ ] Facilitator pack at minimum: **checklist + timing sheet** (FR29-style artifact).

### Engineering / repo

- [ ] **`main`** green on **`build.yml`**; release workflow exercised if possible (tag dry-run or pre-release).
- [ ] **`mike`** / Pages URL and **private** visibility confirmed (**`docs/_internal/deploy.md`**).

### Sign-off

| Role | Name | Date |
|------|------|------|
| Author / builder | | |
| Brand / legal (as required) | | |
| Second-pair screenshot sample | | |
| Notes | | |

---

## v1.0 — First real cohort (definition of “shipped”)

**Target:** PRD **v1.0** — first cohort delivered, metrics captured, checklist filed.

### Delivery

- [ ] Cohort scheduled; lab VMs and NSO/NED versions match **`_data/versions.yaml`** / workbook.
- [ ] Learners receive **PDF** (and/or location of private site per runbook).
- [ ] Proctor completion checklist filed (**FR29**-class artifact per PRD).

### Success measures

- [ ] **S1a** (or agreed metric): e.g. % reaching Lab 9 — recorded with cohort id and date.
- [ ] Incidents / confusion points logged for fast follow-up PRs.

### After the session

- [ ] Retro notes; update **`CHANGELOG.md`** / release process if needed (**`CONTRIBUTING.md`** — Cutting a release).
- [ ] If something must be pulled from circulation, see **`docs/_internal/rollback.md`**.

### Sign-off

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Notes | | |

---

## Quick links

| Topic | Where |
|--------|--------|
| Axe warn → fail | **`docs/_internal/accessibility.md`** |
| Deploy / `mike` / private Pages | **`docs/_internal/deploy.md`** |
| Roll back a bad release | **`docs/_internal/rollback.md`** |
| CI workflows & tagging | **`CONTRIBUTING.md`** (GitHub Actions, Cutting a release) |
| Authoring contract | **`docs/authoring.md`** |
