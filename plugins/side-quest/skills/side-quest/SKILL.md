---
name: side-quest
description: >
  Launch background subagent(s) to handle a task as a side quest while the main conversation
  stays free. Use when the user types /side-quest or asks to run a task as a side quest.
  Rates the task's difficulty (Challenge Rating) to pick the model — haiku for trivial quests,
  sonnet for standard quests, opus for boss fights — honors a user-named model override, splits
  decomposable tasks across a party of parallel agents, and reports launch and completion in
  Dungeons & Dragons style emoji and flavor, always paired with a plain-English summary.
  Awards D&D 5e XP by Challenge Rating on completion and keeps a persistent XP/level ledger
  at ~/.claude/side-quest/xp.json, shared across all sessions and ready for status-bar integration.
allowed-tools: Agent, AskUserQuestion, Read, Glob, Grep, Bash
---

## First-time setup

Run `/side-quest:setup` once after installing the plugin (or after updating it) — it delegates to the `side-quest-setup` agent, the single source of truth for what gets installed, and is idempotent — safe to re-run after every plugin update. It deploys `xp.sh`, `xp_core.py`, `xp-sync-daemon.sh`, and `statusline-command.sh` to their stable paths; installs the cross-machine MQTT sync daemon; merges the `statusLine` block, the `Stop` hook, and the `PostToolUse` tick hook into `~/.claude/settings.json`; and asks for approval before adding the ambient XP rule to `~/.claude/CLAUDE.md`. See `agents/side-quest-setup.md` for exactly what each hook does and why.

The ledger at `~/.claude/side-quest/xp.json` is shared between the stable copy and the plugin script.

# Side Quest

## Preflight check

Before doing anything else, check if setup has been run:

```bash
test -f "$HOME/.claude/side-quest/xp.sh"
```

If the file is **missing**, stop and tell the user:

> "⚔️ The side-quest ledger isn't set up on this machine yet. Run `/side-quest:setup` first — it deploys the XP scripts, configures the statusline, and walks you through the rest. (~2 minutes)"

Do not proceed with the quest until setup is confirmed.

If the file **exists**, continue normally.

---

Fire-and-forget task delegation with table-top flair. `/side-quest <task>` sends the work to background subagents and narrates the journey in D&D style — every themed response paired with a mandatory plain-English translation, so the flavor never costs you information.

## How it works

1. **Parse the quest.** The command argument is the task. No argument → a one-line tavern-keeper prompt asks what quest you seek. Anything that needs user input (ambiguous targets, choices, credentials) gets resolved *before* launch — background agents can't ask questions mid-quest. Destructive or outward-facing quests (push, deploy, delete, send) are confirmed first.

2. **Rate the Challenge Rating → pick the model.**

   | CR | Difficulty | Examples | Model |
   |---|---|---|---|
   | 1–2 | Trivial | lookups, renames, single-file tweaks | 🧝 haiku |
   | 3–4 | Standard | refactors, multi-file features, research | 🧙 sonnet |
   | 5+ | Boss fight | complex, cross-cutting, architectural | 🐲 opus |

   Naming a model in the quest always overrides the rating.

3. **Assemble the party.** One `general-purpose` background agent by default. Independent sub-tasks get a party — multiple agents launched concurrently, each with a self-contained sub-quest prompt (working directory, constraints, definition of done, return-raw-results instruction). All agents run with `run_in_background: true`.

4. **Quest acceptance.** 📜 scroll with quest name, CR, party composition, dice-roll flair — then a `> **Plain English:**` block stating exactly what launched, on which model, and what happens next.

5. **XP award.** On completion, `scripts/xp.sh award <cr> <outcome> --source side-quest "<quest>"` grants XP by CR (level-1 base: CR 1 = 2,000 … CR 5 = 18,000, up to CR 10 = 59,000) — full XP on success, half on partial, zero on a party wipe. Awards are level-scaled: every base reward is multiplied by `1.04 ** (level − 1)`, one point below the level-threshold growth (`1.05`), so each level takes ~1% more turns to clear than the last. The ledger at `~/.claude/side-quest/xp.json` tracks total XP, level (geometric curve: Lv 2 at 1,000 XP, each subsequent gap ×1.05), quest count, and the last 100 quests. Atomic writes; any session or agent can read it.

6. **Quest report.** On completion: 🏆 loot report (concrete results) + XP line with the script's real numbers (+ 🎉 LEVEL UP when crossed) + plain-English summary. On failure: 💀 party-wiped report, zero XP, plain-English error and suggested next step. Results are reported faithfully — partial or failed work is never inflated, and XP follows honesty.

## Example

```
/side-quest refactor src/auth.ts to use the new session store
```

```
📜 **QUEST ACCEPTED: The Refactoring of Mount Doom**
⚔️ CR 3 (Moderate) — a lone 🧙 Sonnet wizard rides forth
🎲 Initiative rolled… the party ventures into the background!

> **Plain English:** Launched 1 background agent (sonnet) to
> refactor src/auth.ts. I'll report back when it finishes.
```

…and when the notification lands:

```
🏆 **QUEST COMPLETE!** 🐉 The dragon is slain!
💰 Loot: 3 files changed, all tests passing
✨ +7,000 XP → 7,000 total (Level 7, next at 8,050)
🎉 **LEVEL UP!** Welcome to Level 7, adventurer!

> **Plain English:** The refactor is done — 3 files changed,
> tests pass. Summary of changes below.
```

## Ambient and mechanical XP

Beyond `/side-quest` itself, three independent mechanisms feed the same ledger:

- **Ambient XP** (model-issued, CLAUDE.md rule): after completing any user-requested task, Claude runs `~/.claude/side-quest/xp.sh award <cr> <outcome> "<summary>"` — the only path that grants CR-based XP, since judging task difficulty needs the model's judgment. Skipped for pure-conversation turns with no tool use.
- **Tick** (mechanical, `PostToolUse` hook, fires on every tool call): `xp.sh tick "$tool"` grants a small flat XP amount and records a randomized Mad-Libs-style flavor line naming the actual tool used (`random_flavor` in `xp_core.py`), with a generic "the crew" filler when no tool name is available. Zero token cost — the hook runs entirely inside the harness.
- **Respond** (mechanical, `Stop` hook, fires at the end of every turn): `xp.sh respond` reads the turn's transcript (Claude Code hands it `transcript_path` on stdin) and **mechanically scores a Challenge Rating** from what actually happened — distinct files edited, edit volume, investigation depth, whether tests ran, multi-turn span (`extract_turn_features` + `score_turn` in `xp_core.py`, no ML/deps). The reward is the CR-table amount, so `respond` is a full stand-in for the model's Ambient XP `award` when that doesn't fire (non-Claude harness, or the model skipped it). If no transcript is available it falls back to the old tool-count tier (100 XP floor at level 1). It self-debounces — a no-op if an `ambient`- or `stop-hook`-sourced award already landed in the last 10s, so a turn the model already rewarded is never double-counted.

All awards scale with level by `1.04 ** (level − 1)`, **capped at 3×** (`LEVEL_AWARD_CAP`) — the uncapped version was a runaway inflation loop once `respond` started minting every turn. Set `LEVEL_AWARD_CAP = 1.0` to disable level-scaling.

`quests_completed` only increments on `award` (from `/side-quest` or the ambient rule) — `tick` and `respond` never bump it.

## Cross-machine sync

The ledger syncs over MQTT (`sidequest/xp/{events,state}`) — every award/tick/respond is applied locally, then published; the `xp-sync-daemon.sh` listener on each machine merges remote events by `event_id`. Beyond that event stream:

- **Self-echo guard**: the broker echoes a machine's own publishes back to its subscriber; `apply-remote` drops any event whose `machine` is us (already applied locally — re-applying only risks a double-count once the id ages out of the 4,000-entry dedup ring).
- **Reconcile on connect**: the event stream has no replay for a machine that was offline when its broker session lapsed, so totals drift and never re-converge. On every (re)connect the daemon runs `xp.sh reconcile <retained-state>` — XP is monotonic, so catching up to a higher shared total is always safe.
- **`xp.sh reset-ledger <total>`**: operator override. Forces this machine's total and bumps a shared `epoch`; every other machine adopts it (up *or* down) on its next reconcile. Use it to undo an inflation bug fleet-wide.

## Status-bar integration

`scripts/xp.sh statusline` prints a one-liner (`⚔️ Lv 3 · 2,025 XP`) built for Claude Code's `statusLine` setting. To show your XP in the status bar, point `statusLine.command` in `~/.claude/settings.json` at the script (or fold its output into an existing statusline script). The ledger is a plain JSON file, so any other status-bar tool can read `~/.claude/side-quest/xp.json` directly.

## Principles

- **The conversation stays free.** Quests run in the background; main Claude never blocks or polls.
- **Plain English is mandatory.** Every themed response carries a plain-English block. Flavor never replaces information.
- **Faithful loot reports.** Failures and partial results are reported as such — the XP is for honesty, not heroics.
