#!/usr/bin/env bash
# Story 6.5 — Run veraPDF against PDF/UA-1, write XML report, propagate exit code unless VERAPDF_NON_BLOCKING=1.
set -euo pipefail

PDF="${1:?usage: run_verapdf.sh <file.pdf> [report.xml]}"
RUN_ID="${GITHUB_RUN_ID:-local}"
if [[ -n "${2:-}" ]]; then
  OUT_XML="$2"
elif [[ -n "${GITHUB_RUN_ID:-}" ]]; then
  OUT_XML="verapdf-report-${RUN_ID}.xml"
else
  OUT_XML="verapdf-report.xml"
fi

VERAPDF_BIN="${VERAPDF_BIN:-}"
if [[ -z "${VERAPDF_BIN}" ]]; then
  if command -v verapdf >/dev/null 2>&1; then
    VERAPDF_BIN="$(command -v verapdf)"
  elif [[ -x /opt/verapdf/verapdf ]]; then
    VERAPDF_BIN="/opt/verapdf/verapdf"
  else
    echo "run_verapdf: verapdf not found. Install per CONTRIBUTING (Story 6.5) or set VERAPDF_BIN." >&2
    exit 2
  fi
fi

set +e
"${VERAPDF_BIN}" -f ua1 --format xml "${PDF}" >"${OUT_XML}" 2>verapdf.stderr
RC=$?
set -e

cat verapdf.stderr >&2 || true

echo "run_verapdf: exit=${RC} report=${OUT_XML}"

if [[ "${VERAPDF_NON_BLOCKING:-0}" == "1" ]]; then
  echo "run_verapdf: VERAPDF_NON_BLOCKING=1 — not failing job on non-zero veraPDF exit (${RC})." >&2
  exit 0
fi

exit "${RC}"
