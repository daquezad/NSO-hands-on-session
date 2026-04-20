---
title: "Lab 9: RBAC Access Control"
chapter: 9
nso_version: "{{ nso_version }}"
ned_versions:
  - "cisco-iosxr-cli-7.x"
estimated_duration: "40 min"
prerequisites:
  - "Labs 1–7 completed — devices xr-1 and xr-2 exist, and you can edit NACM as admin."
learning_objectives:
  - "Create a local NSO user and map it through an authgroup to device credentials."
  - "Define NACM groups and rule-lists that target configuration subtrees by XPath."
  - "Validate allow/deny behavior by switching between admin and a restricted user."
idempotent: true
classification: "Cisco Confidential"
---

# Lab 9: RBAC Access Control

## Learning Objectives

By the end of this lab you will be able to:

- Create a local NSO user and attach it to device credentials through an **authgroup**.
- Configure **NACM** groups, rule-lists, and rules that target paths with **XPath**.
- Log in as a restricted user and confirm allowed vs denied actions in the Web UI.

## Time Budget

{{ time_budget(total=40, segments=[[15,"Users & authgroups"],[20,"NACM rules"],[5,"Broaden rule"]]) }}

## Prerequisites

- [ ] You can log in to the NSO Web UI as **admin** and open **Configuration Editor** for **aaa**, **nacm**, and **devices**.
- [ ] Device definitions for **xr-1** / **xr-2** use management addresses consistent with your lab (examples use **198.51.100.2** for **xr-1** in XPath samples).

## Procedure

NSO combines **AAA users**, **authgroups** (device credential mapping), and **NACM** (northbound access rules) for fine-grained control.

### Step 1: Create a read-only test user

1. Open **Configuration Editor → aaa:aaa → authentication → users**.
2. Click **Edit config**, then **+** to add a user.
3. Create **`read_user`** (password per your lab policy).
4. **Commit**.

You can log out and confirm login as **`read_user`** (limited until NACM is configured).

### Step 2: Map the user through an authgroup

1. Open **Configuration Editor → ncs:devices → authgroup** (select the group your devices use, often **`XR`**).
2. Under **umap** (or **default-map** per your template), add **`read_user`** with **remote-name** / **remote-password** matching device login (**`admin`** / **`cisco123`** in many labs).
3. **Commit**.

Log in as **`read_user`** and open **Device Manager** — you should still reach **connect**, **ping**, and **check-sync** when rules allow it.

### Step 3: Create a NACM group and rule-list

1. Log in as **admin**.
2. Open **Configuration Editor → nacm:nacm → groups**.
3. Create **`read_group`**, assign **group-id** (for example **`1`**), and add user **`read_user`**.
4. Under **rule-lists**, create **`read_rule`** and attach **`read_group`** so all rules in the list apply to that membership.

### Step 4: Discover XPath targets

Use the NSO CLI to print XPath forms of configuration (paths vary slightly by release):

```bash
source ~/NSO-INSTALL/ncsrc
echo "show devices device | display xpath" | ncs_cli -u admin -C
```

{{ expected_output(landmark="devices/device") }}

*Expected output:*

```text
/devices/device[name='xr-1']/…
/devices/device[name='xr-2']/…
```

*(Truncated — you need the `/devices/device[...]` prefixes for rules.)*

For deeper paths:

<!-- lint-skip: no-output -->

```bash
source ~/NSO-INSTALL/ncsrc
echo "show configuration devices device xr-1 | display xpath" | ncs_cli -u admin -C
```

*Expected output (illustrative — addresses follow your lab):*

```text
/devices/device[name='xr-1']/address 198.51.100.2
/devices/device[name='xr-1']/authgroup XR
/devices/device[name='xr-1']/device-type/cli/ned-id cisco-iosxr-cli-7.x
```

!!! info "Access operations"
    Use the UI help on **access-operations** to see **create**, **update**, **delete**, **exec**, and related keywords for your release.

### Step 5: Create a deny rule for domain configuration on xr-1

1. Inside **`read_rule`**, add a rule **`deny-config-domain`**.
2. **Path:** `/devices/device[name='xr-1']/config/cisco-ios-xr:domain`
3. **Action:** `deny`
4. **Access-operations:** `create`, `update`, `delete`, `exec` (adjust to your NACM schema).
5. **Commit**.

### Step 6: Test as read_user

1. Log out, then log in as **`read_user`**.
2. Open **Device Manager**.

You should observe:

- **sync-from** may be hidden or disabled (depending on remaining default rules).
- On **xr-1**, **domain** configuration is not visible or not editable.
- On **xr-2**, **domain** may still appear if the rule only names **xr-1**.

### Step 7: Broaden the rule to all devices

1. Log in as **admin**.
2. Change the rule path from:
   ```text
   /devices/device[name='xr-1']/config/cisco-ios-xr:domain
   ```
   to:
   ```text
   /devices/device/config/cisco-ios-xr:domain
   ```
3. **Commit**.

Log in as **`read_user`** again — **domain** should be hidden on **all** managed devices covered by the rule.

!!! tip "Key takeaway"
    NACM rules target **XPath** expressions — from entire subtrees down to single leaves — to control who can see or change configuration.

{% if instructor %}
!!! tip "Instructor"
    **Duration:** +15 min if learners mis-type XPath. **FAQs:** Still admin-equivalent — clear browser session. **Breaks:** Lockout — use admin + Commit Manager rollback for `nacm` changes.
{% endif %}

## Verification

Confirm **`read_user`** still exists (admin session):

```bash
source ~/NSO-INSTALL/ncsrc
echo "show configuration aaa authentication users user read_user" | ncs_cli -u admin -C
```

{{ expected_output(landmark="read_user") }}

*Expected output:*

```text
user read_user {
```

*(Additional password / key lines may follow — you only need to see the **`read_user`** stanza.)*

Confirm NACM rules in the Web UI under **Configuration Editor → nacm:nacm** — **`read_rule`** should list **`deny-config-domain`**. Optional CLI (output varies):

<!-- lint-skip: no-output -->

```bash
source ~/NSO-INSTALL/ncsrc
echo "show configuration nacm nacm rule-list read_rule" | ncs_cli -u admin -C
```

## Common Errors

{{ common_errors_start() }}

{{ common_error(
  "read_user sees the same UI as admin or changes still apply after deny.",
  "Session cache, wrong user, or rule path typo / wrong NACM group attachment.",
  "Log out fully, clear site data if needed, re-check **groups** ↔ **read_user** mapping and XPath spelling (including namespace prefix)."
) }}

{{ common_error(
  "ncs_cli XPath commands return errors or empty.",
  "Wrong `-u` user, environment not sourced, or display xpath not supported in your build.",
  "Run `source ~/NSO-INSTALL/ncsrc` first; use **Configuration Editor** copy-path features as a fallback."
) }}

{{ common_errors_end() }}

If you lock yourself out or rules conflict, log in as **admin**, revert the last **NACM** commits in **Commit Manager**, or use **[Reset the Lab](reset-lab.md)** for snapshot restore.
