#!/usr/bin/env bash
# Counts `Status: pending` entries across USER-LEVEL ~/.learnings only.
# User-level on purpose: the SessionEnd gate runs with an arbitrary cwd, so a
# project-dependent count would be nondeterministic. Prints a single integer.
set -uo pipefail

LEARNINGS_DIR="$HOME/.learnings"
total=0

for f in LEARNINGS.md ERRORS.md FEATURE_REQUESTS.md; do
  path="$LEARNINGS_DIR/$f"
  [[ -f "$path" ]] || continue
  n="$(grep -c -E '^- \*\*Status\*\*: pending' "$path" 2>/dev/null || true)"
  [[ "$n" =~ ^[0-9]+$ ]] || n=0
  total=$(( total + n ))
done

echo "$total"
