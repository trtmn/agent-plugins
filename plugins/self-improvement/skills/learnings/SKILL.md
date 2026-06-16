---
name: learnings
description: Autonomous capture of every correction, error, suggestion, and knowledge gap to ~/.learnings/ as it happens. Not user-invoked — this is the contract for passive logging. Main Claude delegates to the `learnings` subagent in the background the moment a trigger fires. Reviewing and promoting those entries into CLAUDE.md is handled by the companion `self-improvement` skill.
allowed-tools: Agent, Read, Write, Edit, Grep, Glob, Bash
---

# Learnings

Autonomous, in-session capture of everything worth remembering across sessions. This skill documents the contract; the actual work is done by the `learnings` subagent, invoked in the background by main Claude whenever a trigger fires.

This skill is the **capture** half of the learning loop. The **review + auto-promote** half lives in the `self-improvement` skill (same plugin). Capture is autonomous and continuous; review is autonomous on session-end (and runnable on demand).

## Relationship to `self-improvement`

These are **two skills, one plugin, one invocation model each** — a clean seam:

| | `learnings` | `self-improvement` |
|---|---|---|
| **Who invokes** | Main Claude, autonomously, on every trigger | The SessionEnd hook (headless) — or you, via `/self-improvement` |
| **When** | Continuously, as things happen | After a session ends (if enough piled up), or on demand |
| **Does** | Appends pending entries to `~/.learnings/` | Sweeps, investigates "needed-ness", auto-promotes qualifiers to CLAUDE.md, logs to CHANGELOG |
| **Behavior** | Pure capture, never promotes | Non-interactive auto-promote, with a conservative bar + revertible audit trail |

Capture is cheap; promotion is gated. The two never share behavior, so neither gets invoked in the other's mode.

## The Trigger Contract

Main Claude (not this skill directly) watches for these signals and delegates to the `learnings` subagent via the Agent tool, in the background (`run_in_background: true`):

- **User corrections**: "Actually, it should be...", "No, don't...", "That's wrong because..." → LEARNINGS.md
- **Knowledge gaps**: outdated info given, project convention missed, rule had to be taught → LEARNINGS.md
- **Suggestions**: user proposed a better approach, tool, or pattern → LEARNINGS.md
- **Command/tool failures**: shell command failed, API errored, file op behaved unexpectedly → ERRORS.md
- **Feature requests**: user asked for something Claude couldn't do → FEATURE_REQUESTS.md
- **Repeated mistakes**: same slip twice in one session → LEARNINGS.md, priority high

**Skip:** typos, transient failures (network blips), anything already captured verbatim in the relevant CLAUDE.md.

**The bar:** "Would future Claude plausibly hit this same thing?" If yes, log it.

## Autonomy Rules

- **Don't ask permission** before logging. Ever.
- **Don't wait for a pause.** Fire the background subagent call in the same turn as the trigger.
- **Don't defer to end-of-session.** Context is freshest now. (The session-end review is a safety net, not the primary capture path.)
- **Acknowledge in one short line.** "Logged port-5000 conflict to ERRORS.md" is the whole acknowledgment. No re-explanation.
- **Never block the user.** The subagent runs in the background — main Claude hands off the raw event + a suggested classification (LEARNINGS / ERRORS / FEATURE_REQUESTS) and continues.

## File Layout

```
~/.learnings/
├── LEARNINGS.md          # pending lessons (corrections, gaps, suggestions)
├── ERRORS.md             # pending failures
├── FEATURE_REQUESTS.md   # pending capability gaps
├── CHANGELOG.md          # append-only audit trail — reviewed (promoted/skipped/reverted) entries land here
├── config               # optional: REVIEW_THRESHOLD / COOLDOWN_HOURS / MAX_PROMOTIONS_PER_RUN overrides
├── .last-review         # timestamp of the last autonomous review (cooldown marker)
├── .review.lock         # mutex held by an in-flight review (a directory; auto-reclaimed if stale)
└── .review.log          # stdout/stderr of the most recent headless review
```

Plus, if a project is active, a project-level `.learnings/` mirror in the project root for project-specific entries. See the subagent definition for routing rules.

## Entry Format

All IDs are `<PREFIX>-<6-char-hex>`. Hex is random, generated at log time (`openssl rand -hex 3` or `python3 -c "import secrets; print(secrets.token_hex(3))"`).

The `Timestamp` field must be the real wall-clock time from the shell — `date +%Y-%m-%dT%H:%M:%S%z` — never a guessed or date-only `…T00:00:00Z` value.

### LEARNINGS.md
```markdown
## [LRN-a3f7c1] Short descriptive title
- **Timestamp**: <real `date +%Y-%m-%dT%H:%M:%S%z` output — never guessed or 00:00:00>
- **Priority**: low | medium | high | critical
- **Status**: pending
- **Area**: frontend | backend | infra | tests | docs | config | workflow | other
- **What happened**: Brief description
- **Lesson**: The concrete takeaway
- **Source**: e.g., "User correction in conversation", "PR #42"
- **Suggested fix**: Specific rule or action
```

### ERRORS.md
```markdown
## [ERR-b2e9d4] Short descriptive title
- **Timestamp**: <real `date +%Y-%m-%dT%H:%M:%S%z` output — never guessed or 00:00:00>
- **Priority**: low | medium | high | critical
- **Status**: pending
- **Area**: (same categories)
- **Command/action**: What was attempted
- **Error**: Failure message or description
- **Root cause**: Why it failed (once known)
- **Fix**: What resolved it or what to do differently
- **Reproduction**: Steps (if useful)
```

### FEATURE_REQUESTS.md
```markdown
## [FEAT-c8d2a5] Short descriptive title
- **Timestamp**: <real `date +%Y-%m-%dT%H:%M:%S%z` output — never guessed or 00:00:00>
- **Priority**: low | medium | high | critical
- **Status**: pending
- **Area**: (same categories)
- **Request**: What the user asked for
- **Context**: Why they needed it
- **Workaround**: What was done instead, if anything
```

All new entries start as `Status: pending`. They stay pending until a review (autonomous or manual) reaches them.

## Principles

**Capture is cheap, lossage is expensive.** Err on the side of logging. Future review filters; present-you just records.

**Be specific.** "Don't use deprecated APIs" is useless. "Don't use `os.path.join` — this codebase uses `pathlib.Path` everywhere (see utils.py)" is useful.

**Document the why.** The entry must make sense without the original conversation. Assume the reader has none of the context.

**Act, don't narrate.** Log it, say one line, move on.

## Self-Check on First Delegation

Before firing the `learnings` subagent for the first time in a session, verify `~/.claude/agents/learnings.md` exists. If it doesn't, surface a one-line warning instead of silently failing:

> "⚠ learnings agent not wired up — run `/self-improvement:setup` to fix it."

Do not block the current task. Just warn once and move on.

## Installation

The `learnings` agent ships inside the `self-improvement` plugin. After installing/updating that plugin, run:

```
/self-improvement:setup
```

This wires up the `learnings` agent symlink, the `self-improvement` agents, the SessionEnd review hook, and patches `~/.claude/CLAUDE.md`. The script is idempotent — re-running after an update is safe.
