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

Run these steps once after installing the plugin (or after updating it). All paths use `$HOME` so they work for any user.

### 1. Deploy `xp.sh` to its stable path

The ambient-XP CLAUDE.md rule references `~/.claude/side-quest/xp.sh` directly, independent of the plugin cache path. Deploy it with:

```bash
mkdir -p "$HOME/.claude/side-quest"
cp "${CLAUDE_PLUGIN_ROOT}/scripts/xp.sh" "$HOME/.claude/side-quest/xp.sh"
chmod +x "$HOME/.claude/side-quest/xp.sh"
```

### 2. Deploy `statusline-command.sh`

The statusline script renders the full Claude Code status bar (user@host, git branch, context usage, rate limits, and XP level). Deploy it with:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/scripts/statusline-command.sh" "$HOME/.claude/statusline-command.sh"
chmod +x "$HOME/.claude/statusline-command.sh"
```

### 3. Add the `statusLine` block to `~/.claude/settings.json`

Merge this into the top-level object in `~/.claude/settings.json`:

```json
"statusLine": {
  "type": "command",
  "command": "bash ~/.claude/statusline-command.sh",
  "refreshInterval": 1
}
```

### 4. Add the Stop hook to `~/.claude/settings.json`

This hook awards a CR 1 fallback XP entry after any session where no XP was recorded in the last 120 seconds (catches conversational sessions the ambient rule misses). Merge into the `hooks` object:

```json
"Stop": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "python3 -c \"\nimport json, sys\nfrom pathlib import Path\nfrom datetime import datetime, timezone\nf = Path.home() / '.claude/side-quest/xp.json'\nif f.exists():\n    h = json.loads(f.read_text()).get('history', [])\n    if h:\n        dt = datetime.fromisoformat(h[-1]['ts'])\n        if (datetime.now(timezone.utc) - dt).total_seconds() < 120:\n            sys.exit(0)\nsys.exit(1)\n\" && exit 0; ~/.claude/side-quest/xp.sh award 1 success --source stop-hook 'turn completed' 2>/dev/null || true",
        "async": true,
        "timeout": 15
      }
    ]
  }
]
```

### 5. Add the ambient XP rule to `~/.claude/CLAUDE.md`

This rule instructs Claude to silently award XP after completing any user-requested task. Add this block to your global `~/.claude/CLAUDE.md`:

```markdown
## Ambient XP

After completing any task the user asked for, silently award XP by running this via Bash — **no mention in the response text**:

```bash
~/.claude/side-quest/xp.sh award <cr> <outcome> "<one-line task summary>" >/dev/null 2>&1 || true
```

**CR rubric:**

| CR | Difficulty | Examples |
|----|-----------|---------|
| 1  | Trivial   | Lookups, renames, one-liner explanations with no tool use |
| 2  | Simple    | Single-file edits, config tweaks, quick fixes |
| 3  | Standard  | Multi-step tasks, multi-file changes, research with findings |
| 4  | Complex   | Cross-cutting features, refactors spanning many files |
| 5  | Boss fight | Architectural changes, large migrations, plugin builds |

**Outcome:** `success` (completed as requested), `partial` (incomplete or worked around), `wipe` (task failed entirely).

**Skip** for pure conversational turns where no tools were used and no action was taken (questions, explanations, clarifications).

If the script is missing or fails, skip silently — never surface the error to the user.
```

The ledger at `~/.claude/side-quest/xp.json` is shared between the stable copy and the plugin script.

# Side Quest

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

5. **XP award.** On completion, `scripts/xp.sh award <cr> <outcome> --source side-quest "<quest>"` grants real D&D 5e XP by CR (CR 1 = 200 … CR 5 = 1,800, up to CR 10) — full XP on success, half on partial, zero on a party wipe. The ledger at `~/.claude/side-quest/xp.json` tracks total XP, level (5e advancement table: Lv 2 at 300, Lv 3 at 900, Lv 4 at 2,700 …), quest count, and the last 100 quests. Atomic writes; any session or agent can read it.

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
✨ +700 XP → 700 total (Level 2, next at 900)
🎉 **LEVEL UP!** Welcome to Level 2, adventurer!

> **Plain English:** The refactor is done — 3 files changed,
> tests pass. Summary of changes below.
```

## Status-bar integration

`scripts/xp.sh statusline` prints a one-liner (`⚔️ Lv 3 · 2,025 XP`) built for Claude Code's `statusLine` setting. To show your XP in the status bar, point `statusLine.command` in `~/.claude/settings.json` at the script (or fold its output into an existing statusline script). The ledger is a plain JSON file, so any other status-bar tool can read `~/.claude/side-quest/xp.json` directly.

## Principles

- **The conversation stays free.** Quests run in the background; main Claude never blocks or polls.
- **Plain English is mandatory.** Every themed response carries a plain-English block. Flavor never replaces information.
- **Faithful loot reports.** Failures and partial results are reported as such — the XP is for honesty, not heroics.
