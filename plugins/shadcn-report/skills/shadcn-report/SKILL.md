---
name: shadcn-report
description: Build polished, self-contained HTML reports with shadcn/ui and Magic UI (magicui.design) components, scaffolded and extended with the shadcn CLI via npx, then bundled into ONE portable .html file (optionally exported to PDF). Use this skill whenever the user wants an HTML report, status report, analytics/metrics report, KPI summary, audit or findings write-up, project/quarterly/weekly report, data summary page, or "make this into a nice report" — and whenever they mention shadcn, shadcn/ui, Magic UI, magicui, or `npx shadcn` in the context of a page or report, even if they don't say "skill". Also use it to edit or rebuild a report made earlier with this skill.
allowed-tools:
  - Bash(npx shadcn@latest:*)
  - Bash(npx -y shadcn@latest:*)
  - Bash(npm install:*)
  - Bash(npm run build:*)
  - Read
  - Write
  - Edit
---

# shadcn Report

Turn data and findings into a single, shareable HTML report built from real
shadcn/ui and Magic UI components. Components are always installed with the
**shadcn CLI via `npx`** — never hand-copied — so the code matches the current
registry versions.

**Stack:** Vite + React 19 + TypeScript + Tailwind v4 + shadcn/ui (radix base) +
Magic UI (`@magicui/*` registry, built into the shadcn CLI) + Recharts (via the
shadcn `chart` component) + `vite-plugin-singlefile` (inlines all JS/CSS/fonts/images).

## Paths

`SKILL_DIR` below means the directory this SKILL.md lives in (shown as the skill's
base directory when it loads; in a plugin install it is
`${CLAUDE_PLUGIN_ROOT}/skills/shadcn-report`). Scripts:

| Script | Does |
|---|---|
| `SKILL_DIR/scripts/init-report.sh <slug>` | Scaffold project with `npx shadcn@latest init`, add the default components, apply the report template |
| `SKILL_DIR/scripts/build-report.sh <project> --out <file.html>` | Type-check + build → one self-contained HTML |
| `SKILL_DIR/scripts/export-pdf.sh <file.html> [--out file.pdf]` | Headless Chrome → PDF (static values, charts sized for paper) |

All three print status to stderr and a JSON result to stdout. They take ~30–60s
(`init`) and ~5–10s (`build`) — run `init` with `run_in_background` if your harness
reaps long foreground commands.

## Workflow

### 1. Pin down the content first

A report is a story about data, so before scaffolding, know: who reads it, the
3–6 numbers that matter, the comparisons/trends worth charting, the tables or
findings to list, and what decision or takeaway it should drive. Read any data
files the user points at and compute the figures yourself (a quick Python/`uv run`
script is fine) — never invent numbers. If the user gave no data, ask; don't fill
the report with plausible-looking fakes.

### 2. Scaffold

```bash
bash "$SKILL_DIR/scripts/init-report.sh" <slug> --title "<Report title>"
```

- `<slug>` is kebab-case. The project goes to `~/.cache/shadcn-reports/<slug>/`
  (override with `--dir <parent>` or `$SHADCN_REPORT_HOME`). It has a ~300 MB
  `node_modules`, so **don't put it inside a git repo** — only the built HTML goes
  where the user wants it.
- `--preset <name>` picks the shadcn look: `nova` (default, Lucide/Geist, neutral),
  `vega`, `maia`, `lyra`, `mira`, `luma`, `sera`, `rhea`.
- `--add "<components>"` installs extra components up front (e.g.
  `--add "alert accordion @magicui/animated-circular-progress-bar"`).
- Already exists? Edit it instead of re-scaffolding (see *Editing a report*).

Installed by default — shadcn: `button card badge table tabs chart separator progress tooltip`;
Magic UI: `number-ticker blur-fade border-beam magic-card animated-shiny-text`; plus
three template helpers (below) and a starter `src/App.tsx`.

### 3. Add more components with the CLI

Run from the project directory, always with `-y` and stdin closed so the CLI can't
block on a prompt:

```bash
cd ~/.cache/shadcn-reports/<slug>
npx shadcn@latest add alert accordion -y </dev/null
npx shadcn@latest add @magicui/bento-grid @magicui/animated-list -y </dev/null
npx shadcn@latest search @magicui -q "progress" </dev/null   # discover
npx shadcn@latest view @magicui/bento-grid-demo </dev/null   # example usage
npx shadcn@latest docs accordion </dev/null                  # shadcn docs
```

After adding, **read `src/components/ui/<name>.tsx`** for the actual props before
using it. For which components suit reports (and which to avoid), read
`references/components.md`.

### 4. Write the report

Edit `src/App.tsx`. The starter is a complete, working example (header, exec
summary with a `BorderBeam`, KPI row, tabbed charts, findings table) — reshape
it to the story rather than starting from a blank file. Keep all content in one
`REPORT` object at the top so the JSX stays about layout.

Template helpers (already in the project):

- **`<Kpi label value prefix? suffix? decimals? delta? invertDelta? hint? />`** —
  stat tile; animates with `NumberTicker` on screen, plain exact text in print.
  `invertDelta` for metrics where down is good (cost, latency, churn).
- **`<Reveal delay?>`** — `BlurFade` on scroll; plain `div` in static mode.
- **`useStaticMode()`** — true for `?static`, `prefers-reduced-motion`, and print.
  Use it to disable any other animation: `isAnimationActive={!isStatic}` on
  Recharts series, `{!isStatic && <BorderBeam/>}`.

Why static mode matters: Magic UI's `NumberTicker` starts at 0 and `BlurFade`
starts invisible until scrolled into view. Without static mode, a screenshot,
PDF, or printout shows zeros and blank sections. Any new animated component
you add needs the same treatment.

Design principles for reports:
- **Data first, motion second.** One hero effect per page (e.g. `BorderBeam` on
  the key card), subtle staggered reveals elsewhere, nothing looping behind text.
- **Hierarchy:** title → one-paragraph takeaway → KPIs → evidence (charts) →
  detail (tables, findings) → methodology/notes.
- **Charts:** use the shadcn `chart` wrapper; colors come from `var(--chart-1..5)`
  via the `ChartConfig`. The template overrides the preset's grayscale chart
  palette with shadcn's colorful defaults (see the `report.css` block at the
  bottom of `src/index.css`). Label axes and units; prefer bar/line/area over pie.
- **Both themes:** the page follows the OS theme (press **d** or the toggle to
  switch). Use theme tokens (`bg-card`, `text-muted-foreground`, `--primary`) or
  `dark:` variants — never one-theme hard-coded colors.
- **Print-aware:** content inside inactive `tabs` / closed `accordion` doesn't
  print — keep must-read content outside them. Add `print-hidden` to controls and
  `print-avoid-break` to cards.
- **Self-contained:** import images from `src/assets/` (they get inlined). No
  remote images, fonts, or runtime fetches — the file must work offline and as an
  email attachment. (`tweet-card`, `hero-video-dialog`, `video-text` break this.)

### 5. Build

```bash
bash "$SKILL_DIR/scripts/build-report.sh" ~/.cache/shadcn-reports/<slug> --out ./<slug>.html
```

`--out` defaults to the project's `dist/index.html`. The build runs `tsc -b` first
with `noUnusedLocals` on — an unused import fails the build; read the error, fix,
rebuild. Check `fully_inlined: true` in the JSON.

### 6. Verify it visually

Don't hand over a report you haven't looked at. Screenshot it with whatever
browser tool is available (agent-browser, Playwright, etc.), using `?static` so
values are final:

```
file:///abs/path/<slug>.html?static
```

Check light **and** dark, a desktop width (~1280px) and a phone width (~390px):
no overflow, charts readable, numbers correct. Fix and rebuild as needed. A
second screenshot without `?static` after ~2s confirms the animations run.

### 7. Deliver

- Give the user the absolute path to the `.html` (and the project dir, for edits).
- **PDF wanted?** `bash "$SKILL_DIR/scripts/export-pdf.sh" ./<slug>.html` — it
  loads `?static` and sizes the window to the CSS page so charts don't clip.
  Generic "print to PDF" from a browser tool tends to show zeros or clipped
  charts; use the script.
- If your environment can publish artifacts/pages, the single HTML file can be
  published as-is (everything is inlined).

## Editing a report

The project persists in `~/.cache/shadcn-reports/<slug>/`. Edit `src/App.tsx`
(and add components with the CLI), then re-run `build-report.sh` with the same
`--out`. Changing look wholesale: `npx shadcn@latest apply <preset> -y </dev/null`
inside the project, then rebuild.

## Troubleshooting

| Symptom | Fix |
|---|---|
| CLI hangs / prints an arrow-key menu | Pass every option (`-t vite -b radix -p <preset> --no-monorepo -y`) and redirect stdin `</dev/null`. |
| `Project already exists` | Edit the existing project or pick a new slug. |
| Build fails with `TS6133 ... is declared but never read` | Remove the unused import/variable. |
| Numbers show 0 / sections blank in screenshot or PDF | Use `?static`; make sure new animated pieces check `useStaticMode()`. |
| Charts all gray | Preset ships neutral `--chart-*`; keep the template's palette block or set your own in `src/index.css`. |
| Chart clipped in PDF | Use `export-pdf.sh`, not a generic print. |
| `export-pdf.sh`: no Chrome found | Install Chrome/Chromium or set `CHROME_BIN`. |
| Huge HTML (> ~10 MB) | Large images — resize/compress before importing. |
| `@magicui/<x>` not found | `npx shadcn@latest search @magicui -q <x>` for the current name. |
