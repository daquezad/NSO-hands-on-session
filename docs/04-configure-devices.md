---
title: "Lab 4: Configure Devices"
chapter: 4
nso_version: "{{ nso_version }}"
ned_versions:
  - "cisco-iosxr-cli-7.x"
estimated_duration: "30 min"
prerequisites:
  - "Lab 3: Register XRd Routers completed — devices xr-1 and xr-2 are in NSO and sync-from succeeded."
learning_objectives:
  - "Navigate the NSO Web UI to a device configuration path."
  - "Stage a candidate configuration change and commit it through Commit Manager."
  - "Verify the change on the device CLI."
idempotent: true
classification: "Cisco Confidential"
---

# Lab 4: Configure Devices

## Learning Objectives

By the end of this lab you will be able to:

- Navigate the NSO Web UI to a device configuration path on **xr-1**.
- Stage a candidate configuration change and commit it through **Commit Manager**.
- Verify the change on the device CLI.

## Time Budget

{{ time_budget(total=30, segments=[[15,"Web UI edit & commit"],[15,"Device CLI verify"]]) }}

## Prerequisites

- [ ] [Lab 3: Register XRd Routers](03-register-xrd-routers.md) completed — **xr-1** and **xr-2** show as **unlocked** and **sync-from** has succeeded at least once.
- [ ] You can open the NSO Web UI and SSH from **linux-host** to the device management address (your lab sheet lists the address).

## Procedure

### Step 1: Browse device configuration in the Web UI

Navigate to **xr-1** in the Web UI to inspect interface configuration. Use the search bar or expand the configuration tree.

Follow this path to reach the GigabitEthernet IPv4 address container:

```text
/ncs:devices/device{xr-1}/config/cisco-ios-xr:interface/GigabitEthernet{0/0/0/0}/ipv4/address/
```

### Step 2: Make a configuration change

1. Click **Edit Config**.
2. Change the IPv4 address from `10.1.1.3` to `10.1.1.30` (documentation-style lab addressing).

!!! info "Candidate Configuration"
    A green bar appears on edited fields — this is **candidate** configuration. Changes apply to the device only after you **commit**.

### Step 3: Review and commit

1. Open **Tools → Commit Manager**.
2. Open the **config** tab for a diff view.
3. Review the change, then click **Commit**.

After commit, NSO creates a **rollback** file automatically (covered further in Lab 5).

### Step 4: Verify on the device

SSH to **xr-1** and confirm the interface address in running configuration.

<!-- lint-skip: no-output -->

```bash
ssh admin@198.51.100.2
```

*(Use the management IP your lab assigns; `198.51.100.2` is an example documentation address.)*

At the XR prompt, run:

```cli
show run interface gigabitEthernet 0/0/0/0
```

{{ expected_output(landmark="10.1.1.30") }}

*Expected output:*

```text
interface GigabitEthernet0/0/0/0
 ipv4 address 10.1.1.30 255.255.255.0
!
```

*(Timestamps and banner lines may appear above the `interface` block.)*

!!! tip "Password"
    If prompted: `cisco123` (or the password your facilitator provides).

{% if instructor %}
!!! tip "Instructor"
    **Duration:** tight at 30 min if UI unfamiliar. **FAQs:** No Commit Manager — classic UI path differs. **Breaks:** Wrong interface path — confirm NED namespace `cisco-ios-xr` vs legacy.
{% endif %}

## Verification

From **linux-host**, confirm the committed value is visible in NSO (same shell environment as prior labs):

```bash
source ~/NSO-INSTALL/ncsrc
echo "show configuration devices device xr-1 config cisco-ios-xr:interface GigabitEthernet 0/0/0/0 ipv4 address" | ncs_cli -u admin -C
```

{{ expected_output(landmark="10.1.1.30") }}

*Expected output:*

```text
address 10.1.1.30 255.255.255.0
```

*(Path or spacing may wrap differently; look for **10.1.1.30**.)*

If you already confirmed on the device CLI in Step 4, that counts as a second, independent check.

## Common Errors

{{ common_errors_start() }}

{{ common_error(
  "Commit fails or device shows out-of-sync after commit.",
  "Another session holds a lock, or sync-from needed before edit.",
  "Close other NSO sessions, run check-sync, retry commit; see Lab 5 for rollback files."
) }}

{{ common_error(
  "SSH to xr-1 refused or wrong interface output.",
  "Wrong management IP, routing from linux-host, or change not committed.",
  "Confirm IP in Web UI devices detail, ping from linux-host, re-check Commit Manager succeeded."
) }}

{{ common_errors_end() }}

If commits leave the device and CDB out of sync, use Commit Manager rollbacks (see [5. Rollbacks](05-rollbacks.md)) or **[Reset the Lab](reset-lab.md)** for a broader recovery path.
