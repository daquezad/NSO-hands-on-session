#!/usr/bin/env bash
# Install git hooks from scripts/hooks/ into .git/hooks/ (run from repo root).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_SRC="$ROOT/scripts/hooks"
GIT_HOOKS="$ROOT/.git/hooks"

if [[ ! -d "$ROOT/.git" ]]; then
  echo "install-hooks: not a git repository (no .git). Skipping." >&2
  exit 1
fi

mkdir -p "$GIT_HOOKS"
install -m 0755 "$HOOKS_SRC/commit-msg" "$GIT_HOOKS/commit-msg"
echo "Installed $GIT_HOOKS/commit-msg"
