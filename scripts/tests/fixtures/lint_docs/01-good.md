---
title: "Lab 1: Fixture Good"
chapter: 1
nso_version: "6.3"
ned_versions:
  - "cisco-ios-cli-6.x"
estimated_duration: "45 min"
prerequisites:
  - "None"
learning_objectives:
  - "Describe the fixture"
idempotent: true
classification: "Cisco Confidential"
---
# Lab 1: Fixture Good

## Learning Objectives

One objective.

## Time Budget

{{ time_budget(total=45, segments=[[5,"Setup"],[35,"Procedure"],[5,"Verify"]]) }}

## Prerequisites

- None

## Procedure

### Step 1

Run a command (NSO version macro: {{ nso_version }}).

```cli
show version
```

*Expected output:*

```text
ok
```

## Verification

Check something.

## Common Errors

None.

{{ instructor_block(variant="generic", body="### FAQs\n- Fixture FAQ one?\n- Fixture FAQ two?\n\n### What breaks\n- Example failure mode.\n") }}
