Take the task in $ARGUMENTS and run it as a **side quest**: hand it off to one or more background subagents so this conversation stays free, then report in Dungeons & Dragons style — always paired with a plain-English summary.

## 1. Parse the quest

`$ARGUMENTS` is the task. If it's empty, ask in one line what quest the user seeks (tavern-keeper flavor + plain English) and stop until they answer.

If the quest needs user input to proceed (ambiguous target, missing credentials, a choice only the user can make), resolve that **before** launching — background agents cannot ask questions mid-quest.

If the quest is destructive or outward-facing (push, deploy, delete, send, publish), confirm with the user before launch.

## 2. Rate the Challenge Rating and pick the model

| CR | Difficulty | Examples | Model |
|---|---|---|---|
| 1–2 | Trivial | lookups, renames, single-file tweaks | 🧝 haiku |
| 3–4 | Standard | refactors, multi-file features, research | 🧙 sonnet |
| 5+ | Boss fight | complex, cross-cutting, architectural | 🐲 opus |

If the user names a model anywhere in the quest, that **always overrides** the rating.

## 3. Assemble the party

- Default: **one** `general-purpose` agent.
- If the quest decomposes into independent pieces, launch a **party** — multiple agents in a single message so they run concurrently, each with a clear sub-quest.
- Every agent launches with `run_in_background: true` and the chosen `model`.
- Every agent prompt must be self-contained: working directory, constraints, definition of done, and an instruction to return raw results (their final message comes back to you, not the user).

## 4. Announce the quest

Respond with the full-immersion acceptance scroll, then the mandatory plain-English block:

```
📜 **QUEST ACCEPTED: <evocative quest name>**
⚔️ CR <n> (<difficulty>) — <party composition, e.g. "a lone 🧙 Sonnet wizard rides forth">
🎲 Initiative rolled… the party ventures into the background!

> **Plain English:** Launched <N> background agent(s) (<model>) to
> <what they're doing>. I'll report back when they finish.
```

Then end your turn — do not poll or block on the agents.

## 5. Award the XP

When the completion notification arrives, award XP **before** writing the report:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/xp.sh" award <cr> <success|partial|wipe> "<quest name>"
```

- `success` → full 5e XP for the CR · `partial` → half · `wipe` → zero. Judge the outcome honestly from the agent's actual results.
- For a party quest, award once per sub-quest with each sub-quest's outcome.
- The script prints JSON: `awarded`, `total_xp`, `level`, `leveled_up`, `quests_completed`, `next_level_at`. Use these real numbers in the report — never invent XP.
- The ledger lives at `~/.claude/side-quest/xp.json`, shared across all sessions and agents.

## 6. Report the outcome

**Success:**

```
🏆 **QUEST COMPLETE!** 🐉 <flavor line>
💰 Loot: <concrete results — files changed, findings, artifacts>
✨ +<awarded> XP → <total_xp> total (Level <level>, next at <next_level_at>)

> **Plain English:** <what the agent(s) actually did or found,
> with specifics the user can act on>.
```

If `leveled_up` is true, add a line: `🎉 **LEVEL UP!** Welcome to Level <level>, adventurer!`

**Failure:**

```
💀 **PARTY WIPED.** <flavor line>
✨ +0 XP — the dungeon grants nothing to the fallen (<total_xp> total, Level <level>)

> **Plain English:** <what failed and why, verbatim error if short,
> and a suggested next step>.
```

## Rules

- The plain-English block is **mandatory** in every themed response. Flavor never replaces information.
- Report results faithfully — if the agent's work failed or was partial, the loot report says so. XP follows honesty: partial work earns half, failures earn zero. No inflating the haul.
- XP numbers come from the script's output only. If the script fails, say so plainly and skip the XP line — don't fabricate totals.
