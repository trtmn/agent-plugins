#!/bin/bash
# Type-check and build a report project into ONE self-contained HTML file.
#
# Usage: build-report.sh <project-dir> [--out <file.html>]
#   --out defaults to <project-dir>/dist/index.html (no copy).
#
# Status -> stderr. Final JSON -> stdout.
set -e
set -o pipefail

PROJECT=""
OUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    -h|--help) sed -n '2,7p' "$0" >&2; exit 0 ;;
    -*) echo "Unknown flag: $1" >&2; exit 2 ;;
    *) PROJECT="$1"; shift ;;
  esac
done

[[ -z "$PROJECT" ]] && { echo "Usage: build-report.sh <project-dir> [--out file.html]" >&2; exit 2; }
[[ -f "$PROJECT/vite.config.ts" ]] || { echo "Not a report project: $PROJECT" >&2; exit 1; }

cd "$PROJECT"
LOG="$(mktemp -t shadcn-report-build.XXXXXX)"
trap 'rm -f "$LOG"' EXIT

echo "==> npm run build (tsc -b && vite build)" >&2
if ! npm run build >"$LOG" 2>&1 </dev/null; then
  echo "BUILD FAILED — fix these errors and re-run:" >&2
  sed 's/\x1b\[[0-9;?]*[a-zA-Z]//g' "$LOG" | grep -v '^\s*$' | tail -60 >&2
  exit 1
fi

DIST="$PWD/dist/index.html"
[[ -f "$DIST" ]] || { echo "Build produced no dist/index.html" >&2; exit 1; }

# Any leftover sibling assets mean something did not inline.
LEFTOVER="$(find dist -type f ! -name index.html | head -5)"
if [[ -n "$LEFTOVER" ]]; then
  echo "WARNING: files not inlined into index.html:" >&2
  echo "$LEFTOVER" >&2
fi

FINAL="$DIST"
if [[ -n "$OUT" ]]; then
  mkdir -p "$(dirname "$OUT")"
  cp "$DIST" "$OUT"
  FINAL="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
fi

node -e '
  const fs = require("fs");
  const [file, leftover] = process.argv.slice(1);
  const bytes = fs.statSync(file).size;
  console.log(JSON.stringify({ ok: true, html: file, bytes,
    size: (bytes / 1024 / 1024).toFixed(2) + " MB",
    fully_inlined: leftover === "" }, null, 2));
' "$FINAL" "$LEFTOVER"
