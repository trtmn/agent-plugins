#!/usr/bin/env bash
# xp.sh — side-quest XP ledger CLI. Thin wrapper around xp_core.py, which
# holds the actual ledger logic (unit-tested in tests/test_xp_core.py).
#
# Usage:
#   xp.sh award <cr> <success|partial|wipe> [--source X] <quest name...>
#   xp.sh tick
#   xp.sh status
#   xp.sh statusline
#   xp.sh apply-remote <event-json>   # used by the sync daemon
#   xp.sh flush-outbox                # used by the sync daemon
#   xp.sh flush-ticks                 # used by the sync daemon
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/xp_core.py" "$@"
