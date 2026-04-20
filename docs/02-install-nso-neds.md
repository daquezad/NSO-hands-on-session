---
title: "Lab 2: Install NSO and NEDs"
chapter: 2
nso_version: "{{ nso_version }}"
ned_versions:
  - "cisco-ios-cli-6.x"
  - "cisco-iosxr-cli-7.x"
estimated_duration: "50 min"
prerequisites:
  - "Lab 1: Connect to the Workstation completed."
learning_objectives:
  - "Locate and extract the NSO free-trial installer for the workbook target release."
  - "Perform a local NSO install, create an instance, and confirm the daemon is running."
  - "Install the Cisco IOS-XR NED package and reload packages in the Web UI."
idempotent: false
classification: "Cisco Confidential"
---

# Lab 2: Install NSO and NEDs

## Learning Objectives

By the end of this lab you will be able to:

- Locate and extract the NSO free-trial installer for the release pinned in this workbook (`{{ nso_version }}`).
- Perform a local NSO install, create an instance, and confirm the daemon is running.
- Install the Cisco IOS-XR NED package and reload packages in the Web UI.

## Time Budget

{{ time_budget(total=50, segments=[[10,"Extract installer"],[30,"Install & instance"],[10,"Web UI & NED"]]) }}

## Prerequisites

- [ ] [Lab 1: Connect to the Workstation](01-connect-workstation.md) completed — you have a shell on **linux-host**.
- [ ] The NSO free-trial bundle for this workbook is available under your home directory (folder name may match `NSO-{{ nso_version }}-free` or your site’s layout — adjust paths below if your facilitator uses a different bundle).

## Procedure

Commands use **`{{ nso_version }}`** so they track `mkdocs.yml` `extra.nso_version`. If your lab still ships a different directory name, substitute your path **inside the command fences** only.

### Step 1: Locate the installer files

Navigate to the NSO installer directory and list the available binaries:

```bash
cd ~/NSO-{{ nso_version }}-free/
ls *.bin
```

{{ expected_output(landmark="signed.bin list") }}

*Expected output:*

```text
ncs-{{ nso_version }}-cisco-asa-6.x-freetrial.signed.bin
ncs-{{ nso_version }}-cisco-ios-6.x-freetrial.signed.bin
ncs-{{ nso_version }}-cisco-iosxr-7.x-freetrial.signed.bin
ncs-{{ nso_version }}-cisco-nx-5.x-freetrial.signed.bin
nso-{{ nso_version }}-freetrial.container-image-build.linux.x86_64.signed.bin
nso-{{ nso_version }}-freetrial.container-image-prod.linux.x86_64.signed.bin
nso-{{ nso_version }}-freetrial.linux.x86_64.signed.bin
```

*(Exact NED patch versions may differ; you need the Linux `nso-…freetrial.linux.x86_64.signed.bin` and the IOS-XR `ncs-…-cisco-iosxr-….signed.bin`.)*

### Step 2: Extract the NSO installer

Create a work directory and extract the signed installer (output is verbose; this can take a few minutes):

<!-- lint-skip: no-output -->

```bash
mkdir -p work
cd work
bash ../nso-{{ nso_version }}-freetrial.linux.x86_64.signed.bin --skip-verification
```

### Step 3: Install NSO locally

Run the extracted installer with the `--local-install` flag:

```bash
bash nso-{{ nso_version }}.linux.x86_64.installer.bin --local-install ~/NSO-INSTALL
```

{{ expected_output(landmark="NCS installation complete") }}

*Expected output:*

```text
INFO  Using temporary directory /tmp/ncs_installer.XXXXXX to stage NCS installation bundle
INFO  Unpacked ncs-{{ nso_version }} in /home/cisco/NSO-INSTALL
INFO  Found and unpacked corresponding DOCUMENTATION_PACKAGE
INFO  Found and unpacked corresponding EXAMPLE_PACKAGE
INFO  Found and unpacked corresponding JAVA_PACKAGE
INFO  Generating default SSH hostkey (this may take some time)
INFO  NCS installation complete
```

*(Additional INFO lines about SSH keys, certificates, NETSIM, and `ncsrc` are normal.)*

### Step 4: Source the NSO environment

<!-- lint-skip: no-output -->

```bash
cd ~/NSO-INSTALL/
source ncsrc
```

### Step 5: Create an NSO instance

```bash
ncs-setup --dest nso-instance
cd nso-instance/
ls
```

{{ expected_output(landmark="README.ncs") }}

*Expected output:*

```text
README.ncs  logs  ncs-cdb  ncs.conf  packages  scripts  state
```

### Step 6: Configure WebUI access

Starting with **NSO {{ nso_version }}**, WebUI and RESTCONF may only allow access via the server hostname. To allow access by IP address, edit `ncs.conf` under your instance (path may vary — use the file your facilitator points to).

Add a `<server-alias>` for your lab management address (example below uses a documentation-style address — **use the IP your environment provides**):

```xml
<allow-case-insensitive-enums>true</allow-case-insensitive-enums>
</cli>

<webui>
<server-alias>198.51.100.27</server-alias>
<enabled>true</enabled>
<transport>
<tcp>
<enabled>true</enabled>
<ip>0.0.0.0</ip>
```

!!! warning "Security Note"
    Binding to `0.0.0.0` is for lab use only. In production, restrict access to specific interfaces.

### Step 7: Start NSO

<!-- lint-skip: no-output -->

```bash
ncs
```

*(No stdout is normal; the daemon starts in the background. Use the next step to confirm.)*

### Step 8: Confirm NSO is running

```bash
ncs --status | grep started
```

{{ expected_output(landmark="started") }}

*Expected output:*

```text
status: started
```

### Step 9: Access the Web UI

Open Firefox and navigate to the login URL your environment provides. Example:

```text
http://198.51.100.27:8080/login.html
```

!!! info "Default Credentials"
    **Username:** `admin` | **Password:** `admin`

After logging in, you will see the NSO main page. Navigate to the **Config Editor** section.

### Step 10: Install the IOS-XR NED

#### Extract the NED package

<!-- lint-skip: no-output -->

```bash
cd ~/NSO-{{ nso_version }}-free/work/
bash ../ncs-{{ nso_version }}-cisco-iosxr-7.x-freetrial.signed.bin --skip-verification
```

*(Replace `7.x` in the filename with the exact IOS-XR NED package name from `ls *.bin` in Step 1 if it differs.)*

#### Copy the NED archive into the instance

```bash
cp ncs-{{ nso_version }}-cisco-iosxr-*.tar.gz ~/NSO-INSTALL/nso-instance/packages/
```

{{ expected_output(landmark="packages") }}

*Expected output:*

```text

```

*(No output on success; verify with `ls ~/NSO-INSTALL/nso-instance/packages/` if needed.)*

#### Reload packages in the Web UI

1. Go to the NSO Web UI.
2. Navigate to **ncs:packages**.
3. Select **Actions** → **Reload** → **Run reload action**.

After reloading, you should see the `cisco-ios-xr` package in the list.

!!! tip "Verify"
    Open **Devices** — it should be empty until Lab 3.

{% if instructor %}
!!! tip "Instructor"
    **Duration:** allow +10 min if extract is slow. **FAQs:** Wrong `nso_version` path — symlink bundle to `~/NSO-{{ nso_version }}-free`. **Breaks:** Installer says target exists — use Rollback or fresh VM.
{% endif %}

## Verification

Confirm the daemon and package reload:

```bash
ncs --status | grep started
```

{{ expected_output(landmark="started") }}

*Expected output:*

```text
status: started
```

In the Web UI, confirm **ncs:packages** lists **cisco-ios-xr** (name may vary slightly by build).

## Common Errors

{{ common_errors_start() }}

{{ common_error(
  "Installer or ncs-setup fails with permission or existing directory errors.",
  "Prior partial install or wrong working directory leaves files in ~/NSO-INSTALL or work/.",
  "Stop NSO (`ncs --stop`), remove the partial trees after backup if needed, or restore the VM snapshot — see Rollback below and Reset the Lab."
) }}

{{ common_error(
  "Web UI returns connection refused or TLS errors after editing ncs.conf.",
  "Wrong server-alias IP, daemon not restarted, or firewall blocking the port.",
  "Fix `server-alias` to match how learners browse (IP vs hostname), restart `ncs`, and retest. Ask the class to use the exact URL you published."
) }}

{{ common_errors_end() }}

!!! warning "Rollback"
    If you must discard this install and start over on the same VM (destructive):

    ```bash
    ncs --stop 2>/dev/null || true
    rm -rf ~/NSO-INSTALL ~/NSO-{{ nso_version }}-free/work/nso-instance
    ```

    Prefer **[Reset the Lab](reset-lab.md)** (snapshot restore) when the system is in an unknown state.

If NSO will not start or packages will not reload after multiple attempts, restore the VM snapshot and repeat this lab. Details: **[Reset the Lab](reset-lab.md)**.
