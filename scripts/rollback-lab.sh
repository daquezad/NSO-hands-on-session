#!/usr/bin/env bash
# Story 3.9 — learner-facing wrapper: prints per-lab rollback hints and points to docs/reset-lab.md.
set -euo pipefail

LAB="${LAB:-}"
if [[ -z "$LAB" ]]; then
  echo "Usage: make rollback-lab LAB=N"
  echo "  N must be an integer from 1 through 9 (workbook chapter number)."
  echo "Full procedures, VM reset, and NSO rollback patterns: docs/reset-lab.md"
  exit 1
fi

if ! [[ "$LAB" =~ ^[1-9]$ ]]; then
  echo "ERROR: LAB must be a single digit 1–9, got: $LAB"
  exit 1
fi

echo "NSO workbook — rollback hints for Lab $LAB"
echo "-------------------------------------------"
echo "Canonical steps and safety notes: docs/reset-lab.md"
echo ""

case "$LAB" in
  1)
    echo "Lab 1 — Workstation access only. If the VM desktop is broken, restore the lab snapshot"
    echo "from your environment (no NSO rollback applies)."
    ;;
  2)
    echo "Lab 2 — NSO install / packages. Prefer reloading packages from the Web UI (packages → Reload)."
    echo "If the instance is corrupt, restore the VM snapshot and re-run this lab from the top."
    ;;
  3)
    echo "Lab 3 — Devices. Remove stale devices or reload device.xml via ncs_load only if you"
    echo "understand the diff; when unsure, snapshot restore is faster."
    ;;
  4)
    echo "Lab 4 — Device config. Use Commit Manager rollback files for the last few commits,"
    echo "or sync-to from NSO if you need to push intended CDB state to the device."
    ;;
  5)
    echo "Lab 5 — Rollbacks (primary reference). Web UI: Commit Manager → Load/Save → pick a rollback"
    echo "file, Load, review diff, Commit."
    ;;
  6)
    echo "Lab 6 — Out-of-band sync. Use Check-Sync, then Sync-To or Sync-From as taught in the lab"
    echo "to reconcile drift before moving on."
    ;;
  7)
    echo "Lab 7 — Templates / device groups. Revert via Commit Manager or re-apply template after"
    echo "fixing CDB; see chapter steps for the exact menu path."
    ;;
  8)
    echo "Lab 8 — Services / drift. Service Manager: Check-Sync, then Re-deploy to reconcile;"
    echo "use Commit Manager rollbacks if you need to undo staged service changes."
    ;;
  9)
    echo "Lab 9 — RBAC / NACM. Log in as admin, adjust or delete rules in the NACM model, then Commit;"
    echo "rollback files apply to commits the same way as other labs."
    ;;
esac

echo ""
echo "This script does not run destructive CLI against your VM; it is a reminder of the documented path."
exit 0
