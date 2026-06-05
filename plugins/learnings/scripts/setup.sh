#!/usr/bin/env bash
# Wires up the learnings plugin after installation:
#   1. Creates ~/.claude/agents/learnings.md symlink
#   2. Patches ~/.claude/CLAUDE.md with the Passive Logging section
# Idempotent — safe to re-run after updates.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

AGENTS_DIR="$HOME/.claude/agents"
CLAUDE_MD="$HOME/.claude/CLAUDE.md"

AGENT_SRC="$PLUGIN_ROOT/agents/learnings.md"
AGENT_DEST="$AGENTS_DIR/learnings.md"

# ── 1. Symlink ────────────────────────────────────────────────────────────────
if [[ ! -f "$AGENT_SRC" ]]; then
  echo "ERROR: agent file not found at $AGENT_SRC" >&2
  exit 1
fi

mkdir -p "$AGENTS_DIR"

if [[ -L "$AGENT_DEST" && "$(readlink "$AGENT_DEST")" == "$AGENT_SRC" ]]; then
  echo "✓ agent symlink already correct"
else
  ln -sf "$AGENT_SRC" "$AGENT_DEST"
  echo "✓ created agent symlink: $AGENT_DEST → $AGENT_SRC"
fi

# ── 2. CLAUDE.md patch ────────────────────────────────────────────────────────
PATCH_MARKER="## Passive Logging"

if grep -qF "$PATCH_MARKER" "$CLAUDE_MD" 2>/dev/null; then
  echo "✓ CLAUDE.md already has Passive Logging section"
else
  cat >> "$CLAUDE_MD" << 'EOF'

## Passive Logging

When a trigger fires (user correction, command failure, feature gap, knowledge gap, useful
suggestion), delegate to the `learnings` subagent via the Agent tool, with
`run_in_background: true`. Do not ask first. Acknowledge in one line after handing off.

Triggers, entry schemas, and file locations: see the `learnings` skill in agent-plugins.
EOF
  echo "✓ patched CLAUDE.md with Passive Logging section"
fi

echo ""
echo "Setup complete — learnings capture is active."
