#!/bin/bash
# Scaffold a single-file HTML report project with the shadcn/ui CLI (via npx),
# Magic UI components from the @magicui registry, and vite-plugin-singlefile.
#
# Usage: init-report.sh <slug> [--dir <parent>] [--preset <name>] [--title <title>]
#                              [--add "<extra components>"] [--bare]
#
# Status -> stderr. Final JSON -> stdout.
set -e
set -o pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="$SKILL_DIR/assets/template"

SLUG=""
PARENT="${SHADCN_REPORT_HOME:-$HOME/.cache/shadcn-reports}"
PRESET="nova"
TITLE=""
EXTRA=""
BARE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) PARENT="$2"; shift 2 ;;
    --preset) PRESET="$2"; shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    --add) EXTRA="$2"; shift 2 ;;
    --bare) BARE=1; shift ;;
    -h|--help) sed -n '2,9p' "$0" >&2; exit 0 ;;
    -*) echo "Unknown flag: $1" >&2; exit 2 ;;
    *) SLUG="$1"; shift ;;
  esac
done

if [[ -z "$SLUG" ]]; then
  echo "Usage: init-report.sh <slug> [--dir <parent>] [--preset nova] [--title <title>] [--add \"...\"]" >&2
  exit 2
fi
if [[ ! "$SLUG" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
  echo "Slug must be kebab-case (a-z, 0-9, -): got '$SLUG'" >&2
  exit 2
fi
[[ -z "$TITLE" ]] && TITLE="$SLUG"

command -v node >/dev/null || { echo "node is required (>= 20)" >&2; exit 1; }
command -v npx >/dev/null || { echo "npx is required" >&2; exit 1; }

mkdir -p "$PARENT"
PROJECT="$PARENT/$SLUG"
if [[ -e "$PROJECT" ]]; then
  echo "Project already exists: $PROJECT (edit it, or pick another slug)" >&2
  exit 1
fi

LOG="$(mktemp -t shadcn-report-init.XXXXXX)"
trap 'rm -f "$LOG"' EXIT

run() {
  # Run quietly; on failure dump the log so the caller sees why.
  if ! "$@" >"$LOG" 2>&1 </dev/null; then
    echo "FAILED: $*" >&2
    sed 's/\x1b\[[0-9;?]*[a-zA-Z]//g' "$LOG" | tail -40 >&2
    exit 1
  fi
}

echo "==> shadcn init (vite, radix, preset=$PRESET) in $PARENT/$SLUG" >&2
# </dev/null + explicit -p/-b/--no-monorepo keeps the CLI from prompting.
(cd "$PARENT" && run npx -y shadcn@latest init -t vite -b radix -p "$PRESET" -n "$SLUG" --no-monorepo -y)

cd "$PROJECT"

echo "==> installing vite-plugin-singlefile" >&2
run npm install -D vite-plugin-singlefile

# Replace the template's vite config with a known-good single-file config.
cat > vite.config.ts <<'EOF'
import { resolve } from "node:path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
import { viteSingleFile } from "vite-plugin-singlefile"

// Everything (JS, CSS, fonts, images) is inlined into dist/index.html.
export default defineConfig({
  plugins: [react(), tailwindcss(), viteSingleFile()],
  resolve: {
    alias: {
      "@": resolve(import.meta.dirname, "./src"),
    },
  },
  build: {
    assetsInlineLimit: 100_000_000,
    chunkSizeWarningLimit: 100_000_000,
    cssCodeSplit: false,
  },
})
EOF

SHADCN_COMPONENTS="card badge table tabs chart separator progress tooltip"
MAGIC_COMPONENTS="@magicui/number-ticker @magicui/blur-fade @magicui/border-beam @magicui/magic-card @magicui/animated-shiny-text"

echo "==> shadcn add: $SHADCN_COMPONENTS" >&2
# shellcheck disable=SC2086
run npx -y shadcn@latest add $SHADCN_COMPONENTS -y

echo "==> shadcn add (Magic UI): $MAGIC_COMPONENTS" >&2
# shellcheck disable=SC2086
run npx -y shadcn@latest add $MAGIC_COMPONENTS -y

if [[ -n "$EXTRA" ]]; then
  echo "==> shadcn add (extra): $EXTRA" >&2
  # shellcheck disable=SC2086
  run npx -y shadcn@latest add $EXTRA -y
fi

echo "==> applying report template" >&2
rm -f public/vite.svg src/assets/react.svg
if [[ "$BARE" -eq 0 ]]; then
  cp "$TEMPLATE_DIR/src/App.tsx" src/App.tsx
fi
mkdir -p src/lib src/components/report
cp "$TEMPLATE_DIR/src/lib/static-mode.ts" src/lib/static-mode.ts
cp "$TEMPLATE_DIR/src/components/report/"*.tsx src/components/report/
cat "$TEMPLATE_DIR/src/report.css" >> src/index.css

# index.html: real title, no external favicon (it would 404 once the file is moved).
TITLE="$TITLE" node -e '
  const fs = require("fs");
  const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  let h = fs.readFileSync("index.html", "utf8");
  h = h.replace(/<title>.*<\/title>/, "<title>" + esc(process.env.TITLE) + "</title>");
  h = h.replace(/\s*<link rel="icon"[^>]*>/, "");
  fs.writeFileSync("index.html", h);
'

echo "==> done" >&2
node -e '
  const [project, slug, preset] = process.argv.slice(1);
  console.log(JSON.stringify({ ok: true, project, slug, preset,
    entry: project + "/src/App.tsx", build: "build-report.sh " + project }, null, 2));
' "$PROJECT" "$SLUG" "$PRESET"
