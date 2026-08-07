# Cross-machine XP sync over MQTT + granular hook-based awards

Date: 2026-08-07
Status: approved, implementing (machine-a first, then rollout)

## Goal

The side-quest XP ledger (`~/.claude/side-quest/xp.json`, driven by `xp.sh`) is
currently per-machine local state. The user works across five machines (machine-a,
machine-b, machine-d/machine-d, machine-c, and the the-broker-host homelab box) and wants a single
shared XP pool: an award earned on any machine should show up on every other
machine's statusline without polling, and small per-tool-call rewards should
land with zero token cost (mechanical hooks, not model-issued Bash calls).

## Scope

In scope: machine-a, machine-b, machine-c (macOS), machine-d/machine-d (Linux). The-broker-host is
broker-only — no Claude Code CLI, no daemon, no statusline there (confirmed
with user; the-broker-host has no CLI installed and this is intentional).

Out of scope: authentication on the MQTT broker (Tailscale-only network is
the trust boundary, per explicit user decision), a public `mqtt.trtmn.io`
hostname (also explicitly deferred — would require a paid Cloudflare
Spectrum upgrade).

## Architecture

Event-sourced, additive, idempotent sync — not last-write-wins state
broadcast. Every XP change (big completion award or small tool-call tick) is
an immutable event with a unique ID. Each machine keeps a full local copy of
`xp.json` and applies events additively; order doesn't affect the running
total, only cosmetic history ordering.

- **Broker**: existing Mosquitto on the-broker-host (`<broker-host>.<tailnet>.ts.net:1883`),
  Tailscale-only, no auth. Topic: `sidequest/xp/events`, QoS 1, not retained.
- **Publisher** (`xp.sh award` / new `xp.sh tick`): write to local `xp.json`
  first (unchanged instant local feedback), then publish the same event to
  MQTT. On publish failure (broker unreachable/timeout), append to a local
  outbox instead of blocking or dropping the event.
- **Listener** (new per-machine daemon): a supervised `mosquitto_sub` loop
  with a persistent client session (`clean_session=false`, stable
  `client_id` per machine), subscribed to `sidequest/xp/events`. Per event:
  skip if `event_id` already applied (dedup — also how a machine ignores the
  echo of its own published event), else add the XP delta to the local
  ledger and append a history entry tagged `source: remote:<machine>`. On
  every (re)connect, also flushes that machine's own outbox.
- **Broker persistence**: `persistence true` +
  `persistence_location /mosquitto/data/` added to the-broker-host's
  `mosquitto.conf` (the path is already bind-mounted) so durable client
  sessions and the QoS 1 in-flight queue survive a broker restart, not just
  a network blip.

## Data model

`xp.json` additions (both additive, non-breaking):

- Each `history[]` entry gains `event_id` (UUID4) and `machine` (short
  hostname, e.g. `machine-a`).
- New top-level `applied_event_ids`: capped ring buffer (last 500) of
  already-applied event IDs — the dedup guard.

MQTT event payload (`sidequest/xp/events`, JSON):

```json
{
  "event_id": "uuid4",
  "machine": "machine-a",
  "ts": "2026-08-07T19:20:00Z",
  "kind": "award | tick",
  "cr": 3,
  "outcome": "success",
  "quest": "...",
  "xp": 700,
  "source": "ambient | hook"
}
```

`kind` distinguishes a big Stop-time completion award from a small
per-tool-call tick — same stream, same dedup/apply logic, different XP
magnitude. Only `kind: award` increments `quests_completed`.

**Tick batching**: ticks fire on every tool call and always update the
*local* ledger instantly. To avoid flooding other machines' statuslines and
the broker with one message per tool call, the listener daemon coalesces
ticks into a single summed event published at most every ~10s (only when
there's something to flush). Big completion awards still publish
immediately, uncoalesced.

## Award triggers

- **Big completion award** (`xp.sh award`, CR-based): unchanged trigger
  mechanism — still the model-issued Bash call from the "Ambient XP"
  CLAUDE.md instruction at end of task, since judging task complexity (CR
  1–5) needs the model's judgment, not something a mechanical hook can
  infer. Now also stamps `event_id`/`machine` and publishes to MQTT.
- **New granular ticks** (`xp.sh tick`, small flat XP): fired by a
  `PostToolUse` hook in `settings.json`, matched on all tools, running
  after every successful tool call — entirely inside the harness, zero
  token cost. The hook backgrounds the call (`xp.sh tick &`) so it can
  never add latency to a tool call; the MQTT publish inside it is
  short-timeout/fire-and-forget with outbox fallback so a slow/unreachable
  broker can never stall a tool call.
- `quests_completed` only increments on `award`, never `tick`.

## Reliability

- **Outbox** (`~/.claude/side-quest/mqtt_outbox.jsonl`): any event that
  fails to publish is appended here instead of dropped. The listener
  daemon drains it on every successful (re)connect, removing each line
  only after its publish actually succeeds (crash-safe).
- **Dedup**: both the publisher (at award/tick time) and every receiving
  machine's listener add `event_id` to `applied_event_ids` before/at the
  moment the delta is applied, so redelivery never double-counts.
- **Broker persistence**: see Architecture above.

## Deployment plan

1. Build and test entirely on machine-a first (per explicit user instruction):
   updated `xp.sh` (+ `tick` subcommand), listener daemon script + launchd
   plist, `PostToolUse` hook wired into machine-a's `settings.json`, broker
   persistence enabled on the-broker-host. Verify end-to-end: award/tick → MQTT →
   applied locally; kill/restore network to exercise outbox + dedup.
2. Once verified on machine-a, roll the same files out via SSH: launchd agents
   to machine-b and machine-c (both macOS, key-auth reachable as `ssh-user` /
   password-auth for machine-c via the `machine-d Admin Password` 1Password
   item), a systemd user service to machine-d/machine-d (Linux, key-auth reachable
   as `ssh-user`). Each machine's `settings.json` is merged non-destructively
   (same pattern the existing `side-quest-setup` agent already uses),
   never overwritten wholesale.
3. The-broker-host: only the `mosquitto.conf` persistence change — no CLI, no
   daemon, no statusline.

## Testing

- Local: award and tick on machine-a, confirm `xp.json` updates and an MQTT
  message appears on `sidequest/xp/events` (`mosquitto_sub` sanity check).
- Offline queue: stop the broker (or block the port), trigger an award,
  confirm it lands in the outbox; restart the broker, confirm the daemon
  flushes it and the event isn't double-counted on the originating
  machine.
- Once a second machine is online: award on machine-a, confirm it lands on the
  second machine's `xp.json` within the ~10s tick-batch window (immediately
  for a big award) and that `quests_completed` semantics hold (ticks don't
  bump it, awards do).
