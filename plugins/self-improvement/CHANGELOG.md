# Changelog

## [2.0.2] — 2026-06-16
Fixed fabricated timestamps in captured learnings and the promotion CHANGELOG.

### Fixed
- **Timestamps are now real.** The `learnings` capture agent and the `self-improvement` review pipeline previously emitted `<ISO-8601>` / `ISO-8601` placeholders in their entry templates with no instruction to compute the actual time, so the Haiku capture agent fabricated values — typically date-only `…T00:00:00Z` guesses. Both agents (and the `self-improvement` skill) now mandate obtaining the wall-clock time from the shell via `date +%Y-%m-%dT%H:%M:%S%z` and pasting it verbatim, with an explicit "never guess / `00:00:00` is the tell-tale of a fake timestamp" warning. The capture agent generates the timestamp in the same Bash call as the hex ID.

## [2.0.1] — 2026-06-15
Post-release tuning and an orchestration fix.

### Changed
- `MAX_PROMOTIONS_PER_RUN` default raised from 3 to 10 — the investigator's conservative bar is the real gate; the cap is only a runaway backstop. Tunable in `~/.learnings/config`.

### Fixed
- Orchestrator no longer yields mid-pipeline. `learning-investigator` agents are now launched as concurrent **foreground** calls (never `run_in_background`), so the review collects every verdict and runs through promote/skip/log/notify/report in a single turn instead of dispatching background investigators and returning a "they're running…" status.

## [2.0.0] — 2026-06-15
Merged the `learnings` plugin into `self-improvement` and made the review half autonomous.

### Added
- **Autonomous review.** A gated `SessionEnd` hook (`review-trigger.sh`) spawns a detached, headless `claude -p` review when user-level pending entries reach a threshold and the cooldown has elapsed. Runs in its own process — no cost to the live session.
- **`learning-investigator` agent** — judges each pending entry's "needed-ness" and returns a structured verdict. Conservative bar: high confidence + a second recurrence signal + dedup, user-scope only for auto-promotion.
- **Auto-promotion** to user-level `~/.claude/CLAUDE.md`, with a per-run cap and a full `[PROMO]`/`[SKIP]` audit trail in `~/.learnings/CHANGELOG.md`.
- **`/self-improvement:revert <PROMO-hex>`** command + `revert.sh` to undo a promotion.
- **`learnings` capture agent + skill** moved in from the (now removed) standalone `learnings` plugin.
- **Tunables** via `~/.learnings/config` (`REVIEW_THRESHOLD`, `COOLDOWN_HOURS`, `REVIEW_MODEL`, `MAX_PROMOTIONS_PER_RUN`, `STALE_LOCK_MIN`).
- **Concurrency lock** (atomic `mkdir`, stale-reclaim) so overlapping session-ends can't run dual reviews.

### Security
- The headless review runs **least-privilege**, not `--dangerously-skip-permissions`: a fixed tool allow-list (`Read,Edit,Write,Grep,Glob,Bash,Task,Agent` — no network/MCP tools) with filesystem access scoped to `~/.learnings` and `~/.claude` via `--add-dir`. Anything outside is auto-denied.
- The detached spawn passes all values to the child via environment variables, never by string-concatenation into the `bash -c` body — a quote or `$(...)` in the transcript path cannot escape into a shell.

### Changed
- **BREAKING:** `self-improvement` is no longer interactive per-item approval. Both the autonomous and manual (`/self-improvement`) paths run the same non-interactive auto-promote pipeline; safety is the conservative bar + revertible trail rather than pre-approval.
- **BREAKING:** the standalone `learnings` plugin is removed; install/update `self-improvement` and run `/self-improvement:setup`. The `learnings` agent/skill names are preserved for compatibility.
- Model usage tuned for cost: capture on `haiku`, investigator on `sonnet`, headless review on `sonnet` (configurable).

## [1.0.0] — 2026-06-09
Initial versioned release.
