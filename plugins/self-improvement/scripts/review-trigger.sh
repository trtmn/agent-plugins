#!/usr/bin/env bash
# SessionEnd hook target. Decides whether to launch an autonomous self-improvement
# review, and if so spawns it as a DETACHED, HEADLESS `claude -p` process that
# survives the CLI exiting. This script must NEVER block and must always exit 0
# quickly — it only gates and spawns; the real work happens in the detached child.
#
# Gating: a review runs only when (a) no other review holds the lock, (b) enough
# user-level pending entries have accumulated, and (c) the cooldown has elapsed.
set -uo pipefail   # NOT -e: a session-end hook must never abort with nonzero.

LEARNINGS_DIR="$HOME/.learnings"
SELF_DIR="$HOME/.claude/self-improvement"
LOCK="$LEARNINGS_DIR/.review.lock"
LAST="$LEARNINGS_DIR/.last-review"
LOG="$LEARNINGS_DIR/.review.log"
CONFIG="$LEARNINGS_DIR/config"

# Defaults — override any of these in ~/.learnings/config (KEY=value lines).
REVIEW_THRESHOLD=5      # min user-level pending entries to trigger a review
COOLDOWN_HOURS=6        # min hours between autonomous reviews
REVIEW_MODEL=sonnet     # model for the headless review (smaller = cheaper; sonnet is the sweet spot)
STALE_LOCK_MIN=120      # reclaim a lock older than this (crashed prior run)

mkdir -p "$LEARNINGS_DIR"
# shellcheck disable=SC1090
[[ -f "$CONFIG" ]] && source "$CONFIG"

# ── Read SessionEnd JSON from stdin; pull transcript_path (best-effort) ──────────
STDIN_JSON="$(cat 2>/dev/null || true)"
TRANSCRIPT="$(printf '%s' "$STDIN_JSON" | python3 -c 'import sys,json
try:
    print((json.load(sys.stdin) or {}).get("transcript_path","") or "")
except Exception:
    print("")' 2>/dev/null || true)"

# ── Acquire lock BEFORE any decision (mkdir is atomic; avoids TOCTOU races) ──────
# Reclaim a stale lock left behind by a crashed prior run.
if [[ -d "$LOCK" ]] && find "$LOCK" -maxdepth 0 -mmin +"$STALE_LOCK_MIN" >/dev/null 2>&1; then
  rmdir "$LOCK" 2>/dev/null || true
fi
mkdir "$LOCK" 2>/dev/null || exit 0   # another review owns the lock → bail silently

# If we decide NOT to spawn, we must release the lock ourselves (the child releases it otherwise).
release_and_exit() { rmdir "$LOCK" 2>/dev/null || true; exit 0; }

# ── Gate 1: pending count (user-level only → deterministic regardless of cwd) ────
COUNT=0
if [[ -x "$SELF_DIR/pending-count.sh" ]]; then
  COUNT="$(bash "$SELF_DIR/pending-count.sh" 2>/dev/null || echo 0)"
fi
[[ "$COUNT" =~ ^[0-9]+$ ]] || COUNT=0
(( COUNT < REVIEW_THRESHOLD )) && release_and_exit

# ── Gate 2: cooldown (last review newer than the cooldown window) ────────────────
if [[ -f "$LAST" ]] && find "$LAST" -maxdepth 0 -mmin -"$(( COOLDOWN_HOURS * 60 ))" >/dev/null 2>&1; then
  release_and_exit
fi

# ── Resolve OP token for Pushover. setsid does NOT source a login profile, so a
# GUI-launched session won't have it from ~/.zprofile. Prefer the inherited env
# (covers terminal launches); else a dedicated chmod-600 token file (covers GUI).
# Never echo the value; only export it into the child's environment.
TOKEN="${OP_SERVICE_ACCOUNT_TOKEN:-}"
if [[ -z "$TOKEN" && -r "$HOME/.config/op/service-account-token" ]]; then
  TOKEN="$(cat "$HOME/.config/op/service-account-token" 2>/dev/null || true)"
fi
[[ -n "$TOKEN" ]] && export OP_SERVICE_ACCOUNT_TOKEN="$TOKEN"   # inherited by child, not in argv

# ── Spawn the detached, headless review. The CHILD holds the lock for its whole
# run and releases it on exit. nohup + disown fully detaches it so it survives both
# this hook process and the CLI quitting (macOS has no setsid; this is the portable
# equivalent). Token travels via the exported env above, never on the command line.
REVIEW_PROMPT="Run the self-improvement autonomous review now using the self-improvement skill. Sweep the ended-session transcript (path below, if any) for learnings that passive capture missed and write them as Status: pending entries. Then read every Status: pending entry in ~/.learnings/LEARNINGS.md, ERRORS.md, and FEATURE_REQUESTS.md, dispatch a learning-investigator subagent per candidate, and AUTO-PROMOTE only the qualifiers — user-level scope only — into ~/.claude/CLAUDE.md. Log every PROMO and SKIP to ~/.learnings/CHANGELOG.md and remove those entries from the pending files. Leave uncertain and project-scoped entries pending. Respect the per-run promotion cap. Finish by sending a Pushover summary. This is unattended: never wait for input."

nohup bash -c '
  claude -p "'"$REVIEW_PROMPT"' (ended-session transcript: '"$TRANSCRIPT"')" \
    --model "'"$REVIEW_MODEL"'" \
    --dangerously-skip-permissions \
    > "'"$LOG"'" 2>&1
  rmdir "'"$LOCK"'" 2>/dev/null || true
' < /dev/null > /dev/null 2>&1 &

CHILD=$!
disown "$CHILD" 2>/dev/null || true
# Stamp the cooldown ONLY after confirming the child actually launched — so a failed
# spawn does not wedge a silent multi-hour cooldown with no review having run.
if kill -0 "$CHILD" 2>/dev/null; then
  touch "$LAST" 2>/dev/null || true
else
  rmdir "$LOCK" 2>/dev/null || true
fi

exit 0
