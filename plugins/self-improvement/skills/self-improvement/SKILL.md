---
name: self-improvement
description: Review and AUTO-PROMOTE accumulated learnings into CLAUDE.md. Sweeps a session for missed learnings, investigates each pending entry in ~/.learnings/ for "needed-ness", and promotes the qualifiers into CLAUDE.md with a conservative bar and a full revertible audit trail in CHANGELOG.md. Runs autonomously when a session ends (gated SessionEnd hook) and on demand via /self-improvement. Use this skill when the user asks to review learnings, promote entries, do a retrospective, or run the self-improvement pipeline. For raw background capture, see the separate `learnings` skill.
allowed-tools: Agent, Read, Write, Edit, Grep, Glob, Bash
---

# Self-Improvement

The **review + auto-promote** half of the learning loop. Capture is handled separately by the `learnings` skill, which writes pending entries to `~/.learnings/` continuously. This skill is the deliberate-but-autonomous half: it investigates each pending entry, promotes the ones that clear a conservative bar into `CLAUDE.md`, and records every decision in `CHANGELOG.md` so the active log stays clean and every promotion is reversible.

It closes the loop so Claude gets better as you keep using it — no manual step required.

## How it runs

**One pipeline, one behavior, two triggers.** The pipeline never branches on who called it — it always runs non-interactively and auto-promotes. That single invocation model is what makes it safe to run headless (an approval prompt in an unattended process would deadlock).

| Trigger | How |
|---|---|
| **Autonomous** (primary) | A gated `SessionEnd` hook (`~/.claude/self-improvement/review-trigger.sh`) checks the user-level pending count; if it's ≥ `REVIEW_THRESHOLD` and the cooldown has elapsed and no review holds the lock, it spawns a **detached, headless `claude -p`** review that runs the pipeline in its own process — zero cost to your live session. |
| **Manual** | `/self-improvement` runs the *same* pipeline in the foreground so you can watch promotions happen and intervene. |

Undo any promotion with `/self-improvement:revert <PROMO-hex>`.

## Relationship to `learnings`

| | `learnings` | `self-improvement` |
|---|---|---|
| **Who invokes** | Main Claude, autonomously, on every trigger | SessionEnd hook (headless) or the user (`/self-improvement`) |
| **When** | Continuously | After a session ends (if enough piled up), or on demand |
| **Does** | Appends pending entries to `~/.learnings/` | Investigates, auto-promotes qualifiers, logs to CHANGELOG |
| **Behavior** | Pure capture | Non-interactive auto-promote + revertible trail |

## The pipeline (run by the `self-improvement` agent)

1. **Sweep** (if given a session transcript path) for learnings passive capture missed; write them as `Status: pending` using the `learnings` entry formats.
2. **Read** all `Status: pending` entries from `~/.learnings/{LEARNINGS,ERRORS,FEATURE_REQUESTS}.md`. (Manual runs also read the project `.learnings/` mirror; autonomous runs do not — see Scope.)
3. **Investigate** each candidate with a `learning-investigator` subagent (one per entry, concurrent), which returns a structured verdict.
4. **Act**: auto-promote verdicts that clear the bar (append to target `CLAUDE.md`, `[PROMO-<hex>]` to CHANGELOG, remove from pending); `[SKIP-<hex>]` clear rejects; leave uncertain/project-scoped entries pending. Enforce `MAX_PROMOTIONS_PER_RUN`.
5. **Notify** via a single Pushover summary.
6. **Report** the same summary to stdout (lands in `.review.log` for headless runs).

## The promotion bar (investigator)

Auto-promote only when **all** hold: broadly applicable, **not** a duplicate of existing `CLAUDE.md` content, **high** confidence, **and** a second recurrence signal (`Priority: high|critical` or the pattern appears in ≥2 pending entries). Self-assessed confidence alone is too gameable — the independent signal is required. Anything short of the bar stays **pending** (not skipped). A per-run cap prevents a backlog from flooding `CLAUDE.md` in one pass.

## Scope (autonomous vs manual)

- **Autonomous runs promote to user-level `~/.claude/CLAUDE.md` only.** The session-end working directory is arbitrary, so promoting to a project `CLAUDE.md` would risk the wrong repo. Project-scoped entries are left pending and named in the Pushover summary.
- **Manual `/self-improvement` runs** (you're present, cwd is intentional) may also promote to the project `CLAUDE.md`.

## File Layout

```
~/.learnings/
├── LEARNINGS.md / ERRORS.md / FEATURE_REQUESTS.md   # pending, written by learnings agent
├── CHANGELOG.md       # append-only: every PROMO / SKIP / REVERT lands here with full original entry
├── config             # optional tunables (REVIEW_THRESHOLD, COOLDOWN_HOURS, MAX_PROMOTIONS_PER_RUN, ...)
├── .last-review .review.lock .review.log            # review bookkeeping
```

There is no separate archive file. `CHANGELOG.md` is the single sink and the basis for revert. It is **not** loaded into normal context — only read on explicit request or by `revert.sh`.

## CHANGELOG Entry Formats

### Promoted
````markdown
## [PROMO-<hex>] Short title
- **Timestamp**: ISO-8601
- **Source**: LRN-<hex> | ERR-<hex> | FEAT-<hex>
- **Disposition**: promoted
- **Mode**: autonomous | manual
- **Target**: ~/.claude/CLAUDE.md (or project CLAUDE.md, manual only)
- **Section**: Section of target file
- **Why**: One-sentence rationale
- **Promoted text**:
```text
<the exact text appended to the target — verbatim (fence at left margin), so revert can find it>
```
- **Original entry**: (Full body of source, for posterity)
````

### Skipped
```markdown
## [SKIP-<hex>] Short title
- **Timestamp**: ISO-8601
- **Source**: LRN/ERR/FEAT-<hex>
- **Disposition**: skipped
- **Reason**: Why it didn't warrant promotion
- **Original entry**: (Full body of source)
```

### Reverted (written by `/self-improvement:revert`)
```markdown
## [REVERT-<hex>] Short title
- **Timestamp**: ISO-8601
- **Source**: PROMO-<hex>
- **Disposition**: reverted
- **Reason**: Why the guidance was wrong/outdated
- **Removed from**: Target CLAUDE.md / section
```

## Tunables (`~/.learnings/config`)

```
REVIEW_THRESHOLD=5         # min user-level pending entries before an autonomous review fires
COOLDOWN_HOURS=6           # min hours between autonomous reviews
REVIEW_MODEL=sonnet        # model for the headless review (smaller = cheaper)
MAX_PROMOTIONS_PER_RUN=10  # high runaway-backstop, not a routine limiter (rest stay pending)
STALE_LOCK_MIN=120         # reclaim a review lock older than this (crashed run)
```

## Principles

**Conservative bar, revertible trail.** Auto-promotion is safe only because the bar is high and every change is logged and reversible. Keep both honest.

**Be specific.** Promote concrete rules with the *why*, never vague platitudes.

**Keep active files clean.** Reviewed entries leave the pending files; only CHANGELOG remembers.

**Don't over-promote.** When unsure, the entry stays pending. The per-run cap is a backstop.

## Installation

```
/self-improvement:setup
```

Wires the agents, the `/self-improvement` command, the deployed scripts, the SessionEnd hook, and the CLAUDE.md delegation block. Idempotent. See the script's printed prerequisite about `OP_SERVICE_ACCOUNT_TOKEN` for Pushover.
