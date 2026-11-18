# Component guide for reports

Everything installs with the shadcn CLI from inside the project:

```bash
npx shadcn@latest add <shadcn-name ...> -y            # shadcn/ui
npx shadcn@latest add @magicui/<name ...> -y          # Magic UI (registry is built in)
npx shadcn@latest search @magicui -q "<keyword>"       # find Magic UI items
npx shadcn@latest search @shadcn -q "<keyword>"        # find shadcn items / blocks
npx shadcn@latest view @magicui/<name>-demo            # example usage (JSON; read the "content")
npx shadcn@latest docs <shadcn-name>                   # shadcn docs + API
```

Always pass `-y` and run with stdin closed (`</dev/null`) so the CLI never sits on
a prompt. Components land in `src/components/ui/<name>.tsx` — read the file for the
real props instead of guessing; registry versions change.

## Already installed by `init-report.sh`

| Package | Components |
|---|---|
| shadcn/ui | `button card badge table tabs chart separator progress tooltip` |
| Magic UI | `number-ticker blur-fade border-beam magic-card animated-shiny-text` |
| Report helpers (template) | `@/components/report/kpi` (`<Kpi>`), `@/components/report/reveal` (`<Reveal>`), `@/lib/static-mode` (`useStaticMode()`) |

## shadcn/ui — good report building blocks

| Need | Component(s) | Notes |
|---|---|---|
| Section containers | `card` | `Card / CardHeader / CardTitle / CardDescription / CardContent / CardFooter` |
| Charts | `chart` | Thin wrapper on **Recharts 3**. Wrap charts in `<ChartContainer config={...} className="aspect-auto h-72 w-full">`; colors via `var(--color-<key>)` from the config, which points at `var(--chart-1..5)`. Pass `isAnimationActive={!isStatic}`. |
| Tabular data | `table` | For >50 rows or sorting/filtering, build a data table with `@tanstack/react-table` (`npm i @tanstack/react-table`) — see `npx shadcn@latest docs data-table`. |
| Status / tags | `badge` | variants: `default secondary destructive outline` |
| Alternate views | `tabs` | Inactive tabs don't print — keep must-read content outside tabs. |
| Callouts | `alert` | Risks, caveats, methodology notes. |
| Long detail | `accordion`, `collapsible` | Collapsed content doesn't print either. |
| Progress toward goal | `progress` | |
| Definitions on hover | `tooltip`, `hover-card` | Screen-only; never put essential info only in a tooltip. |
| Avatars / owners | `avatar` | Use initials; external image URLs won't inline. |
| Dense layout | `separator`, `scroll-area`, `aspect-ratio` | |
| Navigation in a long report | `sidebar` or a sticky `<nav>` of anchor links | `sidebar` is heavy; anchor links are usually enough. |

shadcn also ships ready-made chart and dashboard **blocks** — `npx shadcn@latest search @shadcn -q chart` lists them (e.g. `chart-area-interactive`, `chart-bar-multiple`, `chart-pie-donut`, `chart-radial-simple`). `add` drops them in `src/components/` as a starting point to adapt.

## Magic UI — what fits a report

Magic UI is mostly built for landing pages. In a report, motion should *direct
attention to the data*, not compete with it. Rule of thumb: one "hero" effect per
page, subtle reveals everywhere else, nothing that loops behind text.

**Good fits**

| Component | Use it for |
|---|---|
| `number-ticker` | Headline KPIs. Already wrapped by `<Kpi>` (static in print). |
| `blur-fade` | Staggered section reveal. Use via `<Reveal>` so print/screenshots aren't blank. |
| `border-beam` | Highlight the single most important card (exec summary, key result). Parent needs `relative overflow-hidden`. |
| `magic-card` | Hover spotlight on a small grid of feature/metric cards. |
| `animated-circular-progress-bar` | Goal attainment, completion %, scores. |
| `animated-shiny-text`, `highlighter` | Draw the eye to one phrase in a summary. |
| `bento-grid` | Overview grid of 4–6 heterogeneous highlights. |
| `animated-list` | Timeline / event feed / changelog. |
| `file-tree`, `terminal`, `code-comparison` | Technical reports: repo structure, command output, before/after code. |
| `dotted-map`, `globe` | Geographic distribution (globe is WebGL — screen-only, provide a table too). |
| `avatar-circles` | Team / contributors row. |
| `marquee` | Logos or short quotes, sparingly. |
| `grid-pattern`, `dot-pattern` | Very faint header background (use low opacity + `mask-image`). |
| `scroll-progress` | Reading progress bar on long reports. |
| `animated-theme-toggler` | Fancier light/dark switch than the template's button. |

**Avoid in reports** (distracting, or break the single-file / offline goal):
`meteors`, `particles`, `confetti`, `cool-mode`, `smooth-cursor`, `retro-grid`,
`warp-background`, `light-rays`, `dither-field`, `floating-3d-particles`,
`sparkles-text`, `comic-text`, `spinning-text`, `hyper-text` on body copy.
`tweet-card` / `client-tweet-card` fetch from the network at runtime, and
`hero-video-dialog` / `video-text` embed external video — they won't work offline.

## Assets in a single-file build

- Images/SVGs: put them in `src/assets/` and `import logo from "@/assets/logo.png"` —
  Vite inlines them as data URIs. A `<img src="https://...">` stays a network request.
- Fonts: the preset's `@fontsource-variable/*` font is bundled and inlined automatically.
  Add another with `npm i @fontsource-variable/<font>` + `@import` in `src/index.css`, then
  set `--font-sans` / `--font-heading` in the `@theme inline` block.
- Keep the final HTML well under ~10 MB; large photos are the usual culprit.

## Theming

- Colors are CSS variables in `src/index.css` (`:root` and `.dark`). Change
  `--primary`, `--chart-1..5`, `--radius` etc. there, not with hard-coded Tailwind colors.
- Other looks: re-scaffold with `--preset vega|maia|lyra|mira|luma|sera|rhea`, or in an
  existing project `npx shadcn@latest apply <preset> -y`.
- The template's `ThemeProvider` follows the OS (`system`) by default; press **d** to
  toggle. Use `dark:` variants for any custom colors so both themes stay legible.
