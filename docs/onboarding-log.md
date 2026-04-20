# Onboarding Timing Log

This file records timed onboarding runs following `docs/authoring.md`.
It is the living evidence for **NFR-M3** (≤ 30-minute onboarding SLA).

**Target:** `git clone` → `make serve` (working local site) in ≤ 30 minutes
on a mid-tier Cisco corporate laptop, following `docs/authoring.md` only.

---

## How to add a row

After completing the quickstart, add a row below:

```
| YYYY-MM-DD | macOS 14 / Ubuntu 22 / WSL2 | HH:MM | pass / exceeded | <free-text notes> |
```

If you exceeded 30 minutes, also file a GitHub issue (see authoring.md → Timing Log section).

---

## Log

| Date | OS | Time | Result | Notes |
|------|----|------|--------|-------|
| 2026-04-17 | macOS 25.4 (darwin) | 00:04 | pass ✓ | First run by Dev Agent: clean venv, `pip install`, `mkdocs build --strict`. Build succeeded in 0.29 s. `make serve` confirmed working. Story 1.6 baseline entry. |
