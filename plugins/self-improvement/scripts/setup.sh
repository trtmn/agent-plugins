#!/usr/bin/env bash
# Wires up the merged self-improvement plugin (capture + autonomous review):
#   1. Symlinks the learnings, self-improvement, and learning-investigator agents
#      into ~/.claude/agents/ (force-overwriting any stale link; verifying each resolves).
#   2. Symlinks the /self-improvement command into ~/.claude/commands/.
#   3. Deploys review-trigger.sh, pending-count.sh, revert.sh to ~/.claude/self-improvement/.
#   4. Merges the gated SessionEnd review hook into ~/.claude/settings.json (idempotent).
#   5. Appends the Passive Logging delegation block to ~/.claude/CLAUDE.md (idempotent).
# Idempotent — safe to re-run after updates.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

AGENTS_DIR="$HOME/.claude/agents"
COMMANDS_DIR="$HOME/.claude/commands"
DEPLOY_DIR="$HOME/.claude/self-improvement"
SETTINGS="$HOME/.claude/settings.json"
CLAUDE_MD="$HOME/.claude/CLAUDE.md"

mkdir -p "$AGENTS_DIR" "$COMMANDS_DIR" "$DEPLOY_DIR"

# ── 1. Agent symlinks (force + verify) ──────────────────────────────────────────
link_agent() {
  local name="$1"
  local src="$PLUGIN_ROOT/agents/$name"
  local dest="$AGENTS_DIR/$name"
  if [[ ! -f "$src" ]]; then
    echo "ERROR: agent source not found: $src" >&2; exit 1
  fi
  ln -sf "$src" "$dest"          # force-overwrite any stale link (e.g. old standalone learnings)
  if [[ ! -f "$dest" ]]; then    # follows the link — fails if it dangles
    echo "ERROR: agent symlink does not resolve: $dest -> $src" >&2; exit 1
  fi
  echo "✓ agent: $dest -> $src"
}

link_agent "learnings.md"
link_agent "self-improvement.md"
link_agent "learning-investigator.md"

# ── 2. Command symlink ──────────────────────────────────────────────────────────
# /self-improvement (foreground manual run). The :revert and :setup commands come
# from the installed plugin's own namespaced registration.
ln -sf "$PLUGIN_ROOT/commands/self-improvement.md" "$COMMANDS_DIR/self-improvement.md"
echo "✓ command: $COMMANDS_DIR/self-improvement.md"

# ── 3. Deploy scripts to a stable path ──────────────────────────────────────────
for s in review-trigger.sh pending-count.sh revert.sh; do
  cp "$PLUGIN_ROOT/scripts/$s" "$DEPLOY_DIR/$s"
  chmod +x "$DEPLOY_DIR/$s"
  echo "✓ deployed: $DEPLOY_DIR/$s"
done

# ── 4. Merge SessionEnd hook into settings.json (idempotent) ─────────────────────
SETTINGS="$SETTINGS" python3 <<'PY'
import json, os, sys

path = os.environ["SETTINGS"]
hook_cmd = "bash ~/.claude/self-improvement/review-trigger.sh"

try:
    data = json.load(open(path, encoding="utf-8")) if os.path.isfile(path) else {}
except Exception as e:
    print(f"⚠ settings.json is not valid JSON ({e}); not touching it. "
          f"Add a SessionEnd hook for {hook_cmd!r} manually.", file=sys.stderr)
    sys.exit(0)

hooks = data.setdefault("hooks", {})
session_end = hooks.setdefault("SessionEnd", [])

# Idempotency: bail if any SessionEnd hook already references review-trigger.sh.
already = any(
    "review-trigger.sh" in h.get("command", "")
    for block in session_end
    for h in block.get("hooks", [])
)
if already:
    print("✓ SessionEnd review hook already present")
    sys.exit(0)

session_end.append({
    "matcher": "",
    "hooks": [{"type": "command", "command": hook_cmd, "async": True, "timeout": 15}],
})

# Write to a temp file and validate before replacing.
tmp = path + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
json.load(open(tmp, encoding="utf-8"))   # validate
os.replace(tmp, path)
print("✓ merged SessionEnd review hook into settings.json")
PY

# ── 5. CLAUDE.md passive-logging delegation (idempotent) ─────────────────────────
PATCH_MARKER="## Passive Logging"
if grep -qF "$PATCH_MARKER" "$CLAUDE_MD" 2>/dev/null; then
  echo "✓ CLAUDE.md already has Passive Logging section"
else
  cat >> "$CLAUDE_MD" << 'EOF'

## Passive Logging

When a trigger fires (user correction, command failure, feature gap, knowledge gap, useful
suggestion), delegate to the `learnings` subagent via the Agent tool, with
`run_in_background: true`. Do not ask first. Acknowledge in one line after handing off.

Triggers and entry schemas: see the `learnings` skill. Pending entries are reviewed and
auto-promoted to CLAUDE.md by the `self-improvement` pipeline — autonomously when a session
ends (gated SessionEnd hook), or on demand via `/self-improvement`. Undo a promotion with
`/self-improvement:revert <PROMO-hex>`.
EOF
  echo "✓ patched CLAUDE.md with Passive Logging section"
fi

echo ""
echo "Setup complete — capture is active and autonomous review is wired to SessionEnd."
echo ""
echo "Prerequisite for the Pushover summary on autonomous runs:"
echo "  The detached review inherits the launching process's environment (nohup/setsid does"
echo "  NOT source your login profile). For Pushover to fire, OP_SERVICE_ACCOUNT_TOKEN must be"
echo "  either (a) exported in your shell profile so terminal-launched sessions inherit it, or"
echo "  (b) present at ~/.config/op/service-account-token (chmod 600) for GUI-launched sessions."
echo "  Without it, reviews still run and promote — only the push is skipped."
echo ""
echo "Tunables (optional) in ~/.learnings/config:  REVIEW_THRESHOLD, COOLDOWN_HOURS,"
echo "  REVIEW_MODEL, MAX_PROMOTIONS_PER_RUN, STALE_LOCK_MIN."
