# Ambient XP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Award XP silently for every task completed in the main conversation, not just side quests, using the existing xp.sh ledger.

**Architecture:** Add a `--source <label>` flag to `xp.sh award` so ambient vs. side-quest entries are distinguishable in history. Install xp.sh to a stable path (`~/.claude/side-quest/xp.sh`). Add a CLAUDE.md behavioral rule that fires the script silently after every completed task.

**Tech Stack:** Python 3 (inline in xp.sh heredoc), Bash, JSON

---

## Files

| Action | Path |
|--------|------|
| Modify | `plugins/side-quest/scripts/xp.sh` |
| Modify | `plugins/side-quest/skills/side-quest/SKILL.md` |
| Modify | `plugins/side-quest/commands/side-quest.md` |
| Modify | `~/.claude/CLAUDE.md` |
| Create | `~/.claude/side-quest/xp.sh` (copy of updated script) |

---

### Task 1: Add `--source` flag to xp.sh

**Files:**
- Modify: `plugins/side-quest/scripts/xp.sh`

- [ ] **Step 1: Open the award block in xp.sh and replace the argument-parsing lines**

  Current (lines 71–76 of the Python heredoc):
  ```python
  cr = max(1, min(10, int(sys.argv[2])))
  outcome = sys.argv[3]
  if outcome not in ("success", "partial", "wipe"):
      print(f"unknown outcome: {outcome}", file=sys.stderr)
      sys.exit(2)
  quest = " ".join(sys.argv[4:]) or "Unnamed quest"
  ```

  Replace with:
  ```python
  cr = max(1, min(10, int(sys.argv[2])))
  outcome = sys.argv[3]
  if outcome not in ("success", "partial", "wipe"):
      print(f"unknown outcome: {outcome}", file=sys.stderr)
      sys.exit(2)
  rest = sys.argv[4:]
  source = "ambient"
  if len(rest) >= 2 and rest[0] == "--source":
      source = rest[1]
      rest = rest[2:]
  quest = " ".join(rest) or "Unnamed quest"
  ```

- [ ] **Step 2: Add `source` to the history entry**

  Current (in the `award` block, the `data["history"].append(...)` call):
  ```python
  data["history"].append({
      "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
      "quest": quest, "cr": cr, "outcome": outcome, "xp": awarded,
  })
  ```

  Replace with:
  ```python
  data["history"].append({
      "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
      "quest": quest, "cr": cr, "outcome": outcome, "xp": awarded,
      "source": source,
  })
  ```

- [ ] **Step 3: Verify the script parses correctly**

  ```bash
  bash -n plugins/side-quest/scripts/xp.sh
  ```
  Expected: no output (no syntax errors).

- [ ] **Step 4: Smoke-test the new flag**

  ```bash
  LEDGER=$(mktemp /tmp/xp-test-XXXX.json)
  # Override LEDGER path by temporarily patching: run Python inline instead
  python3 - <<'PY'
  import json, sys, tempfile, os
  from pathlib import Path

  # Point script at a temp ledger
  os.environ["XP_TEST_LEDGER"] = "/tmp/xp-smoke-test.json"
  PY

  # Run award without --source (should default to "ambient")
  bash plugins/side-quest/scripts/xp.sh award 2 success "Test quest no source" 2>/dev/null
  python3 -c "
  import json; from pathlib import Path
  d = json.loads(Path.home().joinpath('.claude/side-quest/xp.json').read_text())
  last = d['history'][-1]
  assert last['source'] == 'ambient', f'Expected ambient, got {last[\"source\"]}'
  print('PASS: default source = ambient')
  "

  # Run award with --source side-quest
  bash plugins/side-quest/scripts/xp.sh award 2 success --source side-quest "Test quest with source" 2>/dev/null
  python3 -c "
  import json; from pathlib import Path
  d = json.loads(Path.home().joinpath('.claude/side-quest/xp.json').read_text())
  last = d['history'][-1]
  assert last['source'] == 'side-quest', f'Expected side-quest, got {last[\"source\"]}'
  print('PASS: explicit source = side-quest')
  "
  ```
  Expected output:
  ```
  PASS: default source = ambient
  PASS: explicit source = side-quest
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add plugins/side-quest/scripts/xp.sh
  git commit -m "feat(xp): add --source flag to award command"
  ```

---

### Task 2: Update side-quest command to pass `--source side-quest`

**Files:**
- Modify: `plugins/side-quest/commands/side-quest.md`

- [ ] **Step 1: Find the award call in commands/side-quest.md**

  Current (in the "Award the XP" section):
  ```
  "${CLAUDE_PLUGIN_ROOT}/scripts/xp.sh" award <cr> <success|partial|wipe> "<quest name>"
  ```

  Replace with:
  ```
  "${CLAUDE_PLUGIN_ROOT}/scripts/xp.sh" award <cr> <success|partial|wipe> --source side-quest "<quest name>"
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add plugins/side-quest/commands/side-quest.md
  git commit -m "feat(side-quest): pass --source side-quest to xp award"
  ```

---

### Task 3: Update SKILL.md with setup note and `--source side-quest`

**Files:**
- Modify: `plugins/side-quest/skills/side-quest/SKILL.md`

- [ ] **Step 1: Add a "Setup" section near the top of SKILL.md (after the `---` frontmatter closing, before "# Side Quest")**

  Add:
  ```markdown
  ## First-time setup

  Copy `xp.sh` to a stable location so the CLAUDE.md ambient-XP rule can reference it independently of plugin cache paths:

  ```bash
  mkdir -p ~/.claude/side-quest
  cp "$(dirname "$0")/../scripts/xp.sh" ~/.claude/side-quest/xp.sh
  chmod +x ~/.claude/side-quest/xp.sh
  ```

  Run this once after installing the plugin (or after updating it). The ledger at `~/.claude/side-quest/xp.json` is shared between the stable copy and the plugin script.
  ```

- [ ] **Step 2: Update the award call example in the "Award the XP" section of SKILL.md**

  Current:
  ```
  "${CLAUDE_PLUGIN_ROOT}/scripts/xp.sh" award <cr> <outcome> "<quest name>"
  ```

  Replace with:
  ```
  "${CLAUDE_PLUGIN_ROOT}/scripts/xp.sh" award <cr> <outcome> --source side-quest "<quest name>"
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add plugins/side-quest/skills/side-quest/SKILL.md
  git commit -m "docs(side-quest): add setup note for stable xp.sh path; update award call"
  ```

---

### Task 4: Install the updated script to the stable path

**Files:**
- Create: `~/.claude/side-quest/xp.sh`

- [ ] **Step 1: Copy the updated xp.sh**

  ```bash
  mkdir -p ~/.claude/side-quest
  cp plugins/side-quest/scripts/xp.sh ~/.claude/side-quest/xp.sh
  chmod +x ~/.claude/side-quest/xp.sh
  ```

- [ ] **Step 2: Verify the copy is executable and runs**

  ```bash
  ~/.claude/side-quest/xp.sh status
  ```
  Expected: JSON with `total_xp`, `level`, `quests_completed`, `next_level_at`.

---

### Task 5: Add ambient XP rule to `~/.claude/CLAUDE.md`

**Files:**
- Modify: `~/.claude/CLAUDE.md`

- [ ] **Step 1: Add the Ambient XP section**

  Append the following section to `~/.claude/CLAUDE.md` (after the existing content, before any trailing newline):

  ```markdown
  ## Ambient XP

  After completing any task the user asked for, silently award XP by running this via Bash — **no mention in the response text**:

  ```bash
  ~/.claude/side-quest/xp.sh award <cr> <outcome> "<one-line task summary>" 2>/dev/null || true
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

- [ ] **Step 2: Verify the section was appended correctly**

  ```bash
  grep -n "Ambient XP" ~/.claude/CLAUDE.md
  ```
  Expected: one matching line with the section header.

- [ ] **Step 3: Smoke-test the rule fires correctly**

  Ask Claude to perform a trivial task (e.g., "what is 2+2") and verify the XP ledger total increments. Check:
  ```bash
  ~/.claude/side-quest/xp.sh status
  ```
  The `total_xp` value should have increased, and the last history entry should have `"source": "ambient"`.

---

## Self-review

**Spec coverage:**
- ✅ `xp.sh --source` flag — Task 1
- ✅ `commands/side-quest.md` passes `--source side-quest` — Task 2
- ✅ `SKILL.md` setup note + updated award call — Task 3
- ✅ Stable script installation at `~/.claude/side-quest/xp.sh` — Task 4
- ✅ CLAUDE.md behavioral rule — Task 5
- ✅ Default source = `ambient` (script default when flag omitted) — Task 1 Step 1
- ✅ Backward compat: existing entries without `source` field are implicitly side-quest (no migration needed — the field is additive) — covered by spec, no code needed

**Placeholder scan:** No TBDs. All code blocks are complete.

**Type consistency:** `source` field name used consistently across Task 1 Steps 1–2, Task 2 Step 1, and Task 5 Step 1.
