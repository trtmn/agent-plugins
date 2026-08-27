#!/usr/bin/env bash
# xp-sync-daemon.sh — side-quest cross-machine XP sync listener.
#
# Two supervised loops:
#  1. A persistent-session mosquitto_sub subscriber that applies every
#     incoming XP event to the local ledger (via `xp.sh apply-remote`),
#     and drains the local outbox on every (re)connect.
#  2. A periodic flush of locally-pending ticks, coalesced into one
#     publish every TICK_FLUSH_INTERVAL seconds (see xp_core.py).
#
# Both loops restart on any exit so a network blip or broker restart is
# recovered from automatically — this is the actual "listening for when
# it's available again" behavior, not just a one-shot connection attempt.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
XP_SH="$SCRIPT_DIR/xp.sh"

MQTT_HOST="${XP_MQTT_HOST:?XP_MQTT_HOST must be set to the MQTT broker hostname}"
MQTT_TOPIC="sidequest/xp/events"
MQTT_STATE_TOPIC="sidequest/xp/state"
MACHINE="${XP_MACHINE:-$(hostname -s)}"
CLIENT_ID="sidequest-${MACHINE}"

log() {
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"
}

bootstrap_from_shared_state() {
  # A fresh ledger (new machine, or a reinstall) would otherwise start
  # counting from zero instead of joining the existing shared pool.
  # Fetch the retained state snapshot once at startup and adopt it if
  # this ledger has never earned anything locally (no-op otherwise —
  # see should_bootstrap_from_state in xp_core.py).
  local state
  state="$(mosquitto_sub -h "$MQTT_HOST" -t "$MQTT_STATE_TOPIC" -q 1 -C 1 -W 5 2>>"$LOG_FILE")"
  if [ -n "$state" ]; then
    "$XP_SH" bootstrap "$state" >/dev/null 2>&1 || true
  fi
}

tick_flush_loop() {
  while true; do
    sleep 10
    "$XP_SH" flush-ticks >/dev/null 2>&1 || true
  done
}

subscriber_loop() {
  while true; do
    log "connecting to $MQTT_HOST as $CLIENT_ID"
    # -c: persistent session (broker queues messages while we're offline)
    # -F '%p': print only the JSON payload, one line per message
    mosquitto_sub -h "$MQTT_HOST" -t "$MQTT_TOPIC" -q 1 -c -i "$CLIENT_ID" -F '%p' 2>>"$LOG_FILE" \
      | while IFS= read -r payload; do
          [ -n "$payload" ] || continue
          "$XP_SH" apply-remote "$payload" >/dev/null 2>&1 || true
        done

    log "disconnected, flushing outbox and retrying in 5s"
    "$XP_SH" flush-outbox >/dev/null 2>&1 || true
    sleep 5
  done
}

LOG_FILE="${XP_SYNC_LOG:-$HOME/.claude/side-quest/xp-sync.log}"
mkdir -p "$(dirname "$LOG_FILE")"

bootstrap_from_shared_state

tick_flush_loop &
TICK_PID=$!
trap 'kill "$TICK_PID" 2>/dev/null' EXIT

subscriber_loop
