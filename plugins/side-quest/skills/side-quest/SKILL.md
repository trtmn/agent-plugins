---
name: side-quest
description: >
  Launch background subagent(s) to handle a task as a side quest while the main conversation
  stays free. Use when the user types /side-quest or asks to run a task as a side quest.
  Rates the task's difficulty (Challenge Rating) to pick the model — haiku for trivial quests,
  sonnet for standard quests, opus for boss fights — honors a user-named model override, splits
  decomposable tasks across a party of parallel agents, and reports launch and completion in
  Dungeons & Dragons style emoji and flavor, always paired with a plain-English summary.
allowed-tools: Agent, AskUserQuestion, Read, Glob, Grep, Bash
---

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

5. **Quest report.** On completion: 🏆 loot report (concrete results) + plain-English summary. On failure: 💀 party-wiped report + plain-English error and suggested next step. Results are reported faithfully — partial or failed work is never inflated.

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
💰 Loot: 3 files changed, all tests passing ✨ +150 XP

> **Plain English:** The refactor is done — 3 files changed,
> tests pass. Summary of changes below.
```

## Principles

- **The conversation stays free.** Quests run in the background; main Claude never blocks or polls.
- **Plain English is mandatory.** Every themed response carries a plain-English block. Flavor never replaces information.
- **Faithful loot reports.** Failures and partial results are reported as such — the XP is for honesty, not heroics.
