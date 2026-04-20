# Responsive spot-check log (Story 3.10)

Manual checks that the learner site stays **legible and navigable** on narrow viewports (secondary medium; PDF + desktop web remain primary per UX-DR26).

**Target viewports:** 320px, 480px, 768px, 1024px, 1280px, 1440px — no horizontal scroll, no overlapping content, body text readable.

---

## How to add a row

After a pass, add a row:

```
| YYYY-MM-DD | Tester | Viewports checked | Result | Notes |
```

---

## Log

| Date | Tester | Viewports checked | Result | Notes |
|------|--------|-------------------|--------|-------|
| 2026-04-17 | Project | 320 / 480 / 768 / 1024 / 1280 (browser devtools) | pass | Story 3.10 baseline: hamburger nav (Material), **Contents** floating pill toggles `#__toc`, time-budget legend stacks ≤600px, journey table card layout ≤600px with **intentional break** chip text+color on Lab 8, copy/header controls meet ≥44×44px tap floor at ≤768px. |
