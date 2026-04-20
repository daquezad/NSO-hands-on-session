---
# ============================================================
# AR14 Frontmatter Schema — required fields for every lab chapter.
# Copy this file to docs/NN-kebab-title.md and fill every placeholder.
# "Cisco Confidential" is a LITERAL — do not change it.
# ============================================================
title: "Lab N: Your Lab Title Here"
chapter: 0                          # integer — matches the NN prefix of the filename

ned_versions:                        # list — at least one entry; use exact version strings
  - "cisco-ios-cli-6.x"
  - "cisco-iosxr-cli-7.x"
estimated_duration: "N min"          # format: "<integer> min" — used in the Time Budget ribbon
prerequisites:
  - "Lab 1 completed"                # list — reference the lab number or describe the skill
learning_objectives:
  - "Describe …"                     # list — start each with an action verb (Cisco Learning Taxonomy)
  - "Configure …"
  - "Verify …"
idempotent: true                     # bool — true if the Procedure can be re-run safely from any point
classification: "Cisco Confidential" # LITERAL — do not change; drives the classification banner
---

<!-- ============================================================
     CHAPTER TEMPLATE — Story 2.1 (AR14)
     Mandatory section order: LO → TB → Prereq → Procedure → Verification → Common Errors
     Each section MUST be present. Delete this comment block when copying.
     ============================================================ -->

# {{ title }}

<!-- REQUIRED (FR6, UX-DR3): H1 must match the frontmatter `title` field exactly.
     Only one H1 per chapter. -->

<!-- ============================================================
     SECTION 1 — Learning Objectives
     Requirement: FR2 (measurable outcomes), UX-DR27 (action verbs)
     ============================================================ -->

## Learning Objectives

<!-- REQUIRED: At least three objectives; each starts with an action verb from Bloom's taxonomy
     (Describe, Configure, Verify, Troubleshoot, Implement, Analyze…).
     Keep to one sentence each. -->

By the end of this lab you will be able to:

- Describe the purpose of …
- Configure … using the NSO CLI.
- Verify … by running the appropriate show commands.

<!-- ============================================================
     SECTION 2 — Time Budget
     Requirement: FR6 (time budget ribbon), UX-DR3 (--fs-small)
     ============================================================ -->

## Time Budget

<!-- REQUIRED: Segment minutes must sum to `total` (macro errors at build if not).
     Story 3.4: use the time_budget ribbon macro. -->

{{ time_budget(total=30, segments=[[5,"Setup"],[20,"Procedure"],[5,"Verify"]]) }}

<!-- ============================================================
     SECTION 3 — Prerequisites
     Requirement: FR2 (entry criteria), NFR-U1 (learner autonomy)
     ============================================================ -->

## Prerequisites

<!-- REQUIRED: List everything the learner must have completed or have access to
     before starting this lab. Reference prior lab numbers explicitly. -->

- [ ] Lab N–1 completed (or the following state is present: …).
- [ ] NSO CLI accessible at `user@ncs>`.
- [ ] Devices … are in the NSO device inventory (`show devices list`).

<!-- ============================================================
     SECTION 4 — Procedure
     Requirement: FR4 (step-by-step), NFR-U4 (code fences), NFR-U5 (input/output pairing),
                  UX-DR17 (command → Expected output fence pattern)
     ============================================================ -->

## Procedure

<!-- REQUIRED: Numbered steps. Every command fence (bash/cli/shell) must be immediately
     followed by an "Expected output:" label and a text/console fence.
     Use bare commands — no leading $ or > prompt in the fence.
     See authoring.md for the input/output fence pattern (UX-DR17). -->

### Step 1: Do something

Describe what this step accomplishes in one sentence.

```cli
show devices list
```

*Expected output:*

```text
NAME          ADDRESS    DESCRIPTION  NED ID
------------- ---------- ------------ --------
xrd-1         10.0.0.1                cisco-iosxr-cli-7.x
```

### Step 2: Do something else

Describe what this step accomplishes in one sentence.

```cli
devices sync-from
```

*Expected output:*

```text
sync-result {
    device xrd-1
    result true
}
```

<!-- ============================================================
     SECTION 5 — Verification
     Requirement: NFR-U2 (at least one concrete check), UX-DR17 (paired output)
     ============================================================ -->

## Verification

<!-- REQUIRED: At least one concrete, copy-pasteable verification command with expected output.
     The learner must be able to confirm success independently.
     Each check must pair a command fence with an Expected output fence (UX-DR17). -->

Run the following to confirm the lab is complete:

```cli
show running-config …
```

*Expected output:*

```text
! Replace with the exact expected output after a successful lab run.
```

<!-- ============================================================
     SECTION 6 — Common Errors
     Requirement: NFR-U3 (error guidance), UX-DR: common_errors card pattern (Epic 3)
     ============================================================ -->

## Common Errors

<!-- REQUIRED: At least one error scenario with symptom, cause, and resolution.
     In Epic 3 this section is rendered as Common Errors cards with a red left border.
     Follow the three-field pattern below for each entry. -->

### Error: Device sync fails

**Symptom:** `sync-result { result false }` or `Connection refused`.

**Cause:** The XRd instance is not reachable or the management address is incorrect.

**Resolution:** Verify the device address with `show devices detail | include address`, then
re-run `devices sync-from`.
