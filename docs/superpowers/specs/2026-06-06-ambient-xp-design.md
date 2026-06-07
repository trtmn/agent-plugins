# Ambient XP Design

**Date:** 2026-06-06  
**Status:** Approved  
**Plugin:** side-quest

## Summary

Extend the side-quest XP system to award XP for all tasks completed in the main conversation, not just `/side-quest` background tasks. Awards are silent (no in-conversation message) and use the same D&D 5e CR-based XP table and persistent ledger as side quests.

---

## Architecture

### Stable script installation

`xp.sh` is copied from the plugin to `~/.claude/side-quest/xp.sh` — a permanent, version-independent location alongside `xp.json`. Plugin updates won't clobber it. All consumers (CLAUDE.md rules, status-bar commands) reference this stable path.

The side-quest `SKILL.md` documents the setup step so future installs know to copy the script.

### CLAUDE.md behavioral rule

A rule added to `~/.claude/CLAUDE.md` instructs main Claude to silently award XP after completing any user-requested task:

- Run `~/.claude/side-quest/xp.sh award <cr> <outcome> "<task-summary>"` via Bash
- No mention of this in the response text
- CR assessment follows the same 1–5 rubric as side-quest:

  | CR | Difficulty | Examples |
  |----|-----------|---------|
  | 1  | Trivial   | Lookups, renames, one-liner answers |
  | 2  | Simple    | Single-file edits, config tweaks |
  | 3  | Standard  | Multi-step tasks, multi-file changes |
  | 4  | Complex   | Cross-cutting features, refactors |
  | 5  | Boss fight | Architectural changes, large migrations |

- Outcome: `success` (done), `partial` (incomplete or worked around), `wipe` (task failed entirely)
- **Skip** for pure conversational turns (questions, explanations with no action taken)

### Ledger source tagging

`xp.sh award` gains an optional `--source <label>` flag (default: `"ambient"`). The side-quest command passes `--source side-quest` so history entries distinguish origin. The `history` array in `xp.json` gains a `"source"` field on each entry.

Existing entries without `"source"` are treated as `"side-quest"` for backward compatibility (all prior entries were awarded by the side-quest command).

---

## Data flow

```
Main Claude completes task
  → assesses CR (1–5) and outcome
  → Bash: ~/.claude/side-quest/xp.sh award <cr> <outcome> --source ambient "<summary>"
  → script updates ~/.claude/side-quest/xp.json atomically
  → statusline reflects new total on next render
  → no response text emitted
```

---

## Changes required

1. **`xp.sh`** — add `--source <label>` flag to `award` command; write it into history entries
2. **`SKILL.md`** (side-quest) — add setup note: copy `scripts/xp.sh` to `~/.claude/side-quest/xp.sh` on install; update `award` call to pass `--source side-quest`
3. **`commands/side-quest.md`** — update `xp.sh award` call to pass `--source side-quest`
4. **`~/.claude/CLAUDE.md`** — add ambient XP behavioral rule

---

## Error handling

- If `xp.sh` is missing or fails, main Claude skips silently — no error surfaced to user
- Partial/wipe outcomes are assessed honestly from actual task results, same as side quests
- Conversational turns (no tools used, no action taken) do not trigger an award

---

## Non-goals

- No in-conversation XP messages for ambient awards (statusline only)
- No retroactive XP for past sessions
- No user-visible CR justification (CR is internal to the award call)
