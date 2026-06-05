#!/usr/bin/env bash
# Wires up the self-improvement plugin after installation:
#   1. Creates ~/.claude/agents/self-improvement.md symlink
#   2. Runs learnings setup (required dependency) if available
# Idempotent — safe to re-run after updates.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

AGENTS_DIR="$HOME/.claude/agents"
INSTALLED_PLUGINS="$HOME/.claude/plugins/installed_plugins.json"

AGENT_SRC="$PLUGIN_ROOT/agents/self-improvement.md"
AGENT_DEST="$AGENTS_DIR/self-improvement.md"

# ── 1. Symlink ────────────────────────────────────────────────────────────────
if [[ ! -f "$AGENT_SRC" ]]; then
  echo "ERROR: agent file not found at $AGENT_SRC" >&2
  exit 1
fi

mkdir -p "$AGENTS_DIR"

if [[ -L "$AGENT_DEST" && "$(readlink "$AGENT_DEST")" == "$AGENT_SRC" ]]; then
  echo "✓ self-improvement agent symlink already correct"
else
  ln -sf "$AGENT_SRC" "$AGENT_DEST"
  echo "✓ created agent symlink: $AGENT_DEST → $AGENT_SRC"
fi

# ── 2. Learnings dependency ───────────────────────────────────────────────────
echo ""
echo "Checking learnings dependency..."

LEARNINGS_AGENT="$HOME/.claude/agents/learnings.md"

if [[ -f "$LEARNINGS_AGENT" ]]; then
  echo "✓ learnings agent already wired up"
else
  # Try to find and run learnings setup via installed_plugins.json
  if [[ -f "$INSTALLED_PLUGINS" ]]; then
    LEARNINGS_PATH=$(python3 -c "
import json, sys
with open('$INSTALLED_PLUGINS') as f:
    d = json.load(f)
plugins = d.get('plugins', {})
key = next((k for k in plugins if k.startswith('learnings@')), None)
if not key:
    sys.exit(1)
print(plugins[key][0]['installPath'])
" 2>/dev/null) && {
      LEARNINGS_SETUP="$LEARNINGS_PATH/scripts/setup.sh"
      if [[ -f "$LEARNINGS_SETUP" ]]; then
        echo "Running learnings setup..."
        bash "$LEARNINGS_SETUP"
      else
        echo "⚠ learnings plugin found but setup script missing at $LEARNINGS_SETUP"
        echo "  Run: /learnings:setup"
      fi
    } || {
      echo "⚠ learnings plugin not installed — passive capture won't fire."
      echo "  Run: /plugin install learnings@agent-plugins && /learnings:setup"
    }
  else
    echo "⚠ learnings agent not found. Run: /plugin install learnings@agent-plugins && /learnings:setup"
  fi
fi

echo ""
echo "Setup complete."
