Run the self-improvement review pipeline now, in the foreground, against this machine's pending learnings.

First, check that `~/.claude/agents/learnings.md` and `~/.claude/agents/learning-investigator.md` exist. If either is missing, stop and tell me: "⚠ The self-improvement agents aren't wired up. Run `/self-improvement:setup` first." Do not proceed without them.

Then delegate to the `self-improvement` subagent via the Agent tool (`subagent_type: self-improvement`). Run it in the **foreground** so I can watch promotions happen live and interrupt if needed. Do NOT pass a transcript path (this is a mid-session manual run, not a session-end sweep) unless I explicitly ask you to sweep this conversation.

The subagent runs the same non-interactive pipeline the autonomous session-end hook uses:
1. (Optional, only if I ask) sweep this conversation for anything capture missed.
2. Read pending entries from `~/.learnings/{LEARNINGS,ERRORS,FEATURE_REQUESTS}.md` — and, since this is a manual run inside a repo, the project-level `.learnings/` mirror too.
3. Dispatch a `learning-investigator` per candidate to judge needed-ness (conservative bar: high confidence + a recurrence signal + not a duplicate).
4. Auto-promote the qualifiers — append to the target CLAUDE.md, log a `[PROMO-<hex>]` to `~/.learnings/CHANGELOG.md`, remove from the pending file. Skip clear rejects with a `[SKIP-<hex>]`. Leave uncertain entries pending.
5. Report a summary: swept / promoted / skipped / left-pending, with targets.

This run auto-promotes (no per-item approval prompt) — that's intentional and matches the autonomous behavior. Everything is logged; undo any promotion with `/self-improvement:revert <PROMO-hex>`.

For raw autonomous capture (the passive side), use the separate `learnings` subagent — not this one.
