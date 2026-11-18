# Changelog

## [1.0.0] — 2026-11-18

Initial release.

### Added
- `init-report.sh` — scaffolds a Vite + React + Tailwind v4 project with
  `npx shadcn@latest init`, installs default shadcn/ui and Magic UI
  (`@magicui/*`) components with `npx shadcn@latest add`, wires up
  `vite-plugin-singlefile`, and applies a starter report template.
- `build-report.sh` — type-checks and builds the report into one
  self-contained HTML file.
- `export-pdf.sh` — headless Chrome PDF export in static mode, with the
  window sized to the CSS page so Recharts charts don't clip.
- Template helpers: `<Kpi>`, `<Reveal>`, `useStaticMode()`, a colorful
  chart palette, and print CSS.
- `references/components.md` — which shadcn/ui and Magic UI components
  suit reports, which to avoid, and CLI discovery commands.
