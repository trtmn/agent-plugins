Run the self-improvement review workflow: sweep the current session for anything autonomous capture missed, review pending entries in `~/.learnings/`, and propose promotions to CLAUDE.md for my approval.

Delegate the whole workflow to the `self-improvement` subagent via the Agent tool (`subagent_type: self-improvement`, `run_in_background: true`). The subagent runs in its own context window so this review doesn't consume main-session tokens, and in the background so the main conversation stays responsive while the sweep + proposal generation happens. I'll get a completion notification with the proposals, and then we walk through decisions together in a follow-up turn.

The subagent will:
1. Sweep the current conversation for anything that should have been logged but wasn't.
2. Read pending entries from `~/.learnings/{LEARNINGS,ERRORS,FEATURE_REQUESTS}.md` (and the project-level `.learnings/` mirror, if any).
3. Group and propose promotion candidates — target file, section, and exact text — for my decision.
4. On each decision: write approved entries to the target CLAUDE.md, record the decision (promoted or skipped) in `~/.learnings/CHANGELOG.md` with full original entry for posterity, and remove from the pending file.
5. Report back with a concise summary.

Do NOT promote anything without my explicit approval. Do NOT batch-approve. Do NOT skip the session sweep.

For raw autonomous capture (the passive side), use the separate `learnings` subagent — not this one.
