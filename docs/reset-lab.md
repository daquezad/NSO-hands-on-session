# Reset the Lab

When exercises leave NSO, devices, or the Linux desktop in an unknown state, use this appendix to return to a **known-good baseline** before retrying a chapter or the full workbook.

---

## Before you reset

1. **Save work** you still need (notes, exports) outside the lab VM if your environment allows it.
2. **Prefer NSO-native undo** when the problem is limited to recent commits: open **Commit Manager**, review rollback files, and load the one that matches the state you want (see [5. Rollbacks](05-rollbacks.md)).
3. **Snapshot restore** is the fastest recovery when multiple subsystems are corrupted or you are unsure what changed.

---

## VM-level reset (clean slate)

Your hosted lab environment typically provides **snapshot** or **reprovision** controls (name varies by platform). Use the vendor flow to restore the **initial snapshot** for this workbook.

After the VM is fresh:

1. Confirm you can open a terminal on **linux-host** (Lab 1).
2. Walk forward through labs in order, or jump to your chapter only if you already know earlier labs are clean.

Example check after reconnecting:

```bash
hostname
```

Expected output:

```
linux-host
```

*(Illustrative — your VM may show a different stable hostname.)*

---

## NSO rollback (configuration undo)

For mistakes confined to **recent NSO commits**, use the Web UI:

1. **Commit Manager** → **Load/Save**
2. Select the **rollback file** dated before the bad change
3. **Load** → review the staged candidate → **Commit**

This pattern is the primary undo path for Labs 4–9 when CDB changes are the issue.

```bash
# Optional — from a shell on linux-host, confirm NSO is running (paths may match your install tree)
pgrep -a java | head -3
```

Expected output:

```
# one or more Java processes (NSO JVM) — exact lines depend on your release
```

---

## Per-chapter expectations (idempotency)

During **Epic 4** migration, each `docs/NN-*.md` chapter will declare `idempotent: true|false` in YAML frontmatter. Until that metadata is present for every chapter, use this working guidance:

| Lab | Chapter | Safe to repeat? | If stuck |
|-----|---------|-----------------|----------|
| 1 | Connect to the Workstation | Usually yes | Fix console / desktop; snapshot if unusable |
| 2 | Install NSO and NEDs | Re-run cautiously | Reload packages; snapshot if install is corrupt |
| 3 | Register XRd Routers | Often yes | Remove bad devices or restore snapshot |
| 4 | Configure Devices | Yes with rollbacks | Commit Manager rollback files |
| 5 | Rollbacks | Yes | Use this chapter as the rollback reference |
| 6 | Out-of-Band Sync | Yes | Check-Sync + Sync-To / Sync-From |
| 7 | Device Groups & Templates | Yes | Re-apply or rollback commits |
| 8 | Create a Service | Yes (expect drift drills) | Re-deploy service; roll back commits as needed |
| 9 | RBAC Access Control | Yes | Revert NACM rules via Commit Manager |

If a chapter includes a **`!!! warning "Rollback"`** admonition (required when `idempotent: false` in frontmatter), follow those commands first; use this appendix if you still cannot converge.

---

## Makefile helper

From the repo root (developer workstation — **not** required on the lab VM), contributors can run:

```bash
make rollback-lab LAB=5
```

That invokes `scripts/rollback-lab.sh`, which prints **non-destructive** reminders keyed to chapter 1–9. It does **not** SSH into your environment or run `ncs` commands for you.

---

## Evidence

Timed VM validation runs are recorded in **`docs/reset-lab-log.md`**.
