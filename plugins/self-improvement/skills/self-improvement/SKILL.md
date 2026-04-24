---
name: self-improvement
description: User-triggered review and promotion of accumulated learnings. Reads pending entries from ~/.learnings/, proposes promotion candidates to CLAUDE.md, and lets the user approve each one. Use this skill when the user explicitly asks to review learnings, promote entries, do an end-of-session retrospective, or analyze GitHub PRs/issues for recurring patterns. Also use on phrases like "promote", "review learnings", "what have we learned", or "self-improvement". Do NOT use this skill for logging — that is the separate `learnings` skill (autonomous, background capture).
allowed-tools: Agent, Read, Write, Edit, Grep, Glob, Bash
---

# Self-Improvement

User-triggered review and promotion workflow. Capture is handled separately by the `learnings` skill and its subagent, which write entries to `~/.learnings/` continuously and autonomously. This skill is the *deliberate* half: the user runs it, the subagent proposes promotions, the user decides, and decided entries move to `CHANGELOG.md` so the active log stays clean.

## Relationship to `learnings`

| | `learnings` | `self-improvement` |
|---|---|---|
| **Who invokes** | Main Claude, autonomously | User, via `/self-improvement` |
| **When** | Continuously, as things happen | On demand |
| **Does** | Appends entries to `~/.learnings/` | Reviews entries, proposes promotions, archives to CHANGELOG.md |
| **Human in loop?** | No — pure capture | Yes — user decides every promotion |

Never auto-promote. Capture is free; promotion is deliberate.

## File Layout

```
~/.learnings/
├── LEARNINGS.md          # pending — written by learnings agent, read here
├── ERRORS.md             # pending — written by learnings agent, read here
├── FEATURE_REQUESTS.md   # pending — written by learnings agent, read here
└── CHANGELOG.md          # append-only; every reviewed entry lands here with a disposition
```

There is no separate ARCHIVE file. `CHANGELOG.md` is the single sink: promoted entries, skipped entries, and reversions all live there with a `Disposition` field.

## Workflow

Delegate the entire review to the `self-improvement` subagent via the Agent tool (`subagent_type: self-improvement`, `run_in_background: true`). It runs in its own context window so the review can scan all pending entries without consuming the main session's tokens, and in the background so the main conversation stays responsive during the sweep. The main agent gets a completion notification with the proposals, then walks through decisions with the user in a follow-up turn.

The subagent must:

1. **Session sweep.** Re-read the current conversation for any corrections, errors, suggestions, or feature gaps that the `learnings` agent may have missed. Log any findings (same format and path as the `learnings` agent — the subagent owns both roles during a review). Autonomous capture is best-effort; this step is the safety net.
2. **Read pending entries** from `~/.learnings/LEARNINGS.md`, `ERRORS.md`, `FEATURE_REQUESTS.md` (anything with `Status: pending`).
3. **Group and summarize** candidates worth promoting, organized by theme.
4. **Propose** for each candidate: target CLAUDE.md (user vs. project), section, proposed text, one-line rationale.
5. **Wait for the user** to approve, reject, or modify each one. Do not batch-promote.
6. **Act on each decision:**
   - Approved → write to the target CLAUDE.md, append a `[PROMO-<hex>]` entry to `CHANGELOG.md`, remove the source entry from its pending file.
   - Skipped → append a `[SKIP-<hex>]` entry to `CHANGELOG.md` with the reason, remove the source entry from its pending file.
7. **Report back** with a concise summary: sweep findings, promotions, skips, counts.

Keep the main session informed only at the summary level — the subagent handles the per-entry dance internally.

## Promotion Criteria

Propose promotion when an entry is:

1. **Broadly applicable** — applies beyond one conversation or file.
2. **Likely to recur** — future Claude would plausibly hit the same thing.
3. **Not already documented** — check the target CLAUDE.md first; never duplicate.

Do not propose:

- One-off workarounds for temporary situations.
- Fixes that are self-documented by the code change itself.
- Anything already covered verbatim in the target CLAUDE.md.

## Where to Promote

- **Project CLAUDE.md** (project root) — project-specific conventions, pitfalls, patterns.
- **User CLAUDE.md** (`~/.claude/CLAUDE.md`) — cross-project knowledge that applies regardless of project.

Rule of thumb: "Would this matter in a completely different project?" — Yes → user. No → project. Sometimes both → promote to both with slightly different framing.

## CHANGELOG Entry Formats

### Promoted entry
```markdown
## [PROMO-<hex>] Short title matching the source
- **Timestamp**: ISO-8601
- **Source**: LRN-<hex> | ERR-<hex> | FEAT-<hex>
- **Disposition**: promoted
- **Target**: project CLAUDE.md | user CLAUDE.md (note both if promoted to both)
- **Section**: Which section of the target file
- **What was promoted**: Exact text or a close summary
- **Why**: One sentence on why this deserved promotion
- **Original entry**: (Full body of the source entry, for posterity)
```

### Skipped entry
```markdown
## [SKIP-<hex>] Short title matching the source
- **Timestamp**: ISO-8601
- **Source**: LRN-<hex> | ERR-<hex> | FEAT-<hex>
- **Disposition**: skipped
- **Reason**: Why it didn't warrant promotion
- **Original entry**: (Full body of the source entry, for posterity)
```

### Reversion (rare)
If a promotion turns out to be wrong, add a new entry — never edit or delete existing ones.

```markdown
## [REVERT-<hex>] Short title
- **Timestamp**: ISO-8601
- **Source**: PROMO-<hex>
- **Disposition**: reverted
- **Reason**: Why the promoted guidance was wrong or outdated
- **Removed from**: Target CLAUDE.md / section
```

The changelog is append-only. It is **not** loaded into regular context — only read when the user explicitly asks ("show me what we skipped", "what was promoted last week", "search the changelog for X").

## Learning from GitHub PRs and Issues

When the user asks to learn from GitHub history:

```bash
gh pr list --state closed --limit 50 --json number,title,reviews,comments
gh pr view <number> --json reviews,comments,body
```

Extract:
- Recurring reviewer complaints → LEARNINGS.md
- Rejected approaches (and why) → LEARNINGS.md as anti-patterns
- Common bug patterns from issues → ERRORS.md
- Frequently requested features → FEATURE_REQUESTS.md

Focus on patterns appearing across multiple PRs/issues — not one-offs. Always cite the source PR/issue number in the entry.

## Principles

**Human-in-the-loop for every promotion.** Auto-promotion causes CLAUDE.md bloat and unwanted rules. The user decides, every time.

**Keep active files small.** Once reviewed, entries leave LEARNINGS/ERRORS/FEATURE_REQUESTS and live only in CHANGELOG. Scanning for pending work stays fast.

**Be specific when promoting.** "Don't use deprecated APIs" is useless. "Don't use `os.path.join` in this codebase — it uses `pathlib.Path` everywhere (see utils.py)" is useful.

**Document the why.** A promoted rule without the reason behind it becomes cargo-culted. Include the motivating incident.

## Installation

Link the subagent and slash command into your Claude Code user config:

```bash
ln -sf "$(pwd)/agents/self-improvement.md" ~/.claude/agents/self-improvement.md
ln -sf "$(pwd)/commands/self-improvement.md" ~/.claude/commands/self-improvement.md
```

See the `learnings` skill for the companion autonomous-capture setup.
