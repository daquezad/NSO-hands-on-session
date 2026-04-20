#!/usr/bin/env bash
# Story 3.11 — run after `make build-learner`. Fast Python checks first, then static server + Lighthouse + axe.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
SITE="${1:-site}"
PORT="${PORT:-8765}"
export QUALITY_BASE_URL="http://127.0.0.1:${PORT}"

if [[ ! -d "$SITE" ]]; then
  echo "ERROR: site directory missing: $SITE (run make build-learner first)"
  exit 1
fi

python3 scripts/check_perf_budget.py "$SITE"
python3 scripts/check_internal_links.py "$SITE"

python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$SITE" &
HTTP_PID=$!
cleanup() { kill "$HTTP_PID" 2>/dev/null || true; }
trap cleanup EXIT
sleep 2

CHROME="${CHROME_PATH:-}"
if [[ -z "$CHROME" ]]; then
  for c in chromium chromium-browser google-chrome-stable google-chrome; do
    if command -v "$c" &>/dev/null; then
      CHROME="$(command -v "$c")"
      break
    fi
  done
fi
if [[ -z "$CHROME" ]]; then
  echo "ERROR: no Chrome/Chromium found for Lighthouse. Set CHROME_PATH or install Chromium."
  exit 1
fi
export CHROME_PATH="$CHROME"

LH_COMMON=(
  --only-categories=performance
  --output=json
  --quiet
  --form-factor=mobile
  --throttling-method=simulate
  --chrome-flags="--headless --no-sandbox --disable-gpu --disable-dev-shm-usage"
)

npx lighthouse@11.6.0 "${QUALITY_BASE_URL}" "${LH_COMMON[@]}" --output-path="$ROOT/lh-home.json"
npx lighthouse@11.6.0 "${QUALITY_BASE_URL}08-create-service/" "${LH_COMMON[@]}" --output-path="$ROOT/lh-lab8.json"

python3 scripts/check_lighthouse_performance.py "$ROOT/lh-home.json" "$ROOT/lh-lab8.json" --min-score 0.9
python3 scripts/check_axe_warn.py

echo "OK: quality gates passed."
