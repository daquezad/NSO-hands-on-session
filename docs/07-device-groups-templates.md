---
title: "Lab 7: Device Groups & Templates"
chapter: 7
nso_version: "{{ nso_version }}"
ned_versions:
  - "cisco-iosxr-cli-7.x"
estimated_duration: "35 min"
prerequisites:
  - "Lab 6: Out-of-Band Sync completed — xr-1 and xr-2 are in sync with NSO."
learning_objectives:
  - "Create a device group that contains multiple managed devices."
  - "Author a device template with NED-scoped settings (for example DNS name-servers)."
  - "Apply a template to a device group and verify configuration on a device CLI."
idempotent: true
classification: "Cisco Confidential"
---

# Lab 7: Device Groups & Templates

## Learning Objectives

By the end of this lab you will be able to:

- Create a **device group** that contains **xr-1** and **xr-2**.
- Define a **device template** with IOS-XR DNS settings.
- Run **Apply-Template** for the group and verify **DNS** configuration on a device.

## Time Budget

{{ time_budget(total=35, segments=[[15,"Device group"],[20,"Template & apply"]]) }}

## Prerequisites

- [ ] [Lab 6: Out-of-Band Sync](06-out-of-band-sync.md) completed — both devices are **in-sync** and reachable.
- [ ] You can open **Configuration Editor** and **Commit Manager** as **admin**.

## Procedure

Device **groups** and **templates** let you push configuration to **multiple** devices with one action.

### Step 1: Create a device group

1. Go to **Devices → Device groups**.
2. Click **+ Add device group**.
3. Name it **`ios-xr-devices`**.
4. Click **Create**.
5. Select **xr-1** and **xr-2**, then **+ Add to device group**.
6. Click **Create device group**.

Both devices should appear in **`ios-xr-devices`**.

### Step 2: Create a device template

1. Open **Configuration Editor**.
2. Select the **ncs:devices** module.
3. Click **Edit config**.
4. In the **template** tile, click **+**.
5. Choose NED **cisco-iosxr**, then **Confirm**.
6. Open the NED subtree to edit template content.

### Step 3: Configure DNS in the template

1. Navigate to **Domain** (path may read **domain** / **Domain name** depending on UI skin).
2. Add a **domain name** and **name-server** IP (example: **`2.2.2.2`** — documentation-style resolver).

### Step 4: Review and commit

1. Open **Commit Manager** and review the diff — you should see the new **device group** and **template** objects.
2. **Commit**.

### Step 5: Apply the template to the group

1. In **Configuration Editor → ncs:devices**, open the device group **`ios-xr-devices`**.
2. Click **Actions → Apply-Template**.
3. Select your template name (scroll if needed).
4. Run **Apply-Template**.

The action result should show **ok** for each member device.

!!! info "Templates vs services"
    Templates are flexible but lack **service lifecycle** semantics. Uncontrolled edits on devices can drift from the template intent — **services** (Lab 8) add structure and reconciliation.

{% if instructor %}
!!! tip "Instructor"
    **Duration:** +10 min if Apply-Template fails ACL/NACM. **FAQs:** Template not listed — commit the template first. **Breaks:** Partial apply — check per-device sync then rollback last commit.
{% endif %}

## Verification

On **xr-1**, confirm DNS settings from the template:

<!-- lint-skip: no-output -->

```bash
ssh admin@198.51.100.2
```

```cli
show run domain
```

{{ expected_output(landmark="name-server") }}

*Expected output:*

```text
domain name-server 2.2.2.2
```

*(Additional `domain name` lines may appear if you set them in the template.)*

## Common Errors

{{ common_errors_start() }}

{{ common_error(
  "Apply-Template returns failed or only one device updates.",
  "Authgroup mapping, device lock, or template path not committed.",
  "Verify both devices in the group share credentials; check Commit Manager for errors, then sync-from on failing device."
) }}

{{ common_error(
  "show run domain is empty after a successful apply.",
  "Template targeted wrong NED branch or DNS not under domain in your IOS-XR model.",
  "Re-open the template in Configuration Editor, confirm **Domain** leaves exist in the diff, commit, and re-run Apply-Template."
) }}

{{ common_errors_end() }}

If **apply-template** fails for all devices or leaves partial state, roll back the last commits or follow **[Reset the Lab](reset-lab.md)**.
