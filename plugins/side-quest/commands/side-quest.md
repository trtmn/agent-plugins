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

## 5. Report the outcome

When the completion notification arrives, relay the result:

**Success:**

```
🏆 **QUEST COMPLETE!** 🐉 <flavor line>
💰 Loot: <concrete results — files changed, findings, artifacts> ✨ +<n> XP

> **Plain English:** <what the agent(s) actually did or found,
> with specifics the user can act on>.
```

**Failure:**

```
💀 **PARTY WIPED.** <flavor line>

> **Plain English:** <what failed and why, verbatim error if short,
> and a suggested next step>.
```

## Rules

- The plain-English block is **mandatory** in every themed response. Flavor never replaces information.
- Report results faithfully — if the agent's work failed or was partial, the loot report says so. No inflating the haul.
