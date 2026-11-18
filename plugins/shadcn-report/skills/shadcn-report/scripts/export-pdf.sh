#!/bin/bash
# Export a built report HTML to PDF with headless Chrome/Chromium.
#
# Usage: export-pdf.sh <report.html> [--out <file.pdf>]
#   Browser: $CHROME_BIN, else Google Chrome / Chromium / Edge from the usual paths.
#
# Why not just "print": headless print-to-PDF never fires `beforeprint`, so the
# page is loaded with ?static (final values, no animation). The window width is
# set to the printable width of the report's CSS @page (1200px - 2x48px margin)
# so Recharts measures the same width it will print at and nothing clips.
#
# Status -> stderr. Final JSON -> stdout.
set -e
set -o pipefail

HTML=""
OUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    -h|--help) sed -n '2,11p' "$0" >&2; exit 0 ;;
    -*) echo "Unknown flag: $1" >&2; exit 2 ;;
    *) HTML="$1"; shift ;;
  esac
done

[[ -f "$HTML" ]] || { echo "Usage: export-pdf.sh <report.html> [--out file.pdf]" >&2; exit 2; }
HTML_ABS="$(cd "$(dirname "$HTML")" && pwd)/$(basename "$HTML")"
[[ -z "$OUT" ]] && OUT="${HTML_ABS%.html}.pdf"
mkdir -p "$(dirname "$OUT")"
OUT_ABS="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"

find_chrome() {
  if [[ -n "$CHROME_BIN" && -x "$CHROME_BIN" ]]; then echo "$CHROME_BIN"; return; fi
  local c
  for c in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"; do
    [[ -x "$c" ]] && { echo "$c"; return; }
  done
  for c in google-chrome google-chrome-stable chromium chromium-browser microsoft-edge; do
    command -v "$c" >/dev/null 2>&1 && { command -v "$c"; return; }
  done
}

CHROME="$(find_chrome)"
if [[ -z "$CHROME" ]]; then
  echo "No Chrome/Chromium found. Install one or set CHROME_BIN=/path/to/chrome." >&2
  exit 1
fi

echo "==> printing with $(basename "$CHROME")" >&2
"$CHROME" --headless --disable-gpu --no-pdf-header-footer \
  --window-size=1104,1600 --virtual-time-budget=4000 \
  --print-to-pdf="$OUT_ABS" "file://$HTML_ABS?static" >/dev/null 2>&1 </dev/null || true

if [[ ! -s "$OUT_ABS" ]]; then
  echo "PDF was not written: $OUT_ABS" >&2
  exit 1
fi

node -e '
  const fs = require("fs");
  const f = process.argv[1];
  console.log(JSON.stringify({ ok: true, pdf: f, bytes: fs.statSync(f).size }, null, 2));
' "$OUT_ABS"
