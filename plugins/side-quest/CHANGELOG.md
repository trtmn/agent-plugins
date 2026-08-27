# Changelog

## [2.4.0] — 2026-08-26
Rescale the XP classifier — awards were too small and never grew with progress.

- **~10× bigger base awards.** The `respond` floor tiers (the mechanical
  tool-count classifier — this is the "10 XP" simple turns were earning)
  go 10/20/40/80/150/300 → 100/200/400/800/1500/3000. The CR award table
  (`XP_BY_CR`) is multiplied by 10: CR 1 200 → 2,000, CR 5 1,800 →
  18,000, CR 10 5,900 → 59,000.
- **Awards now scale with level.** Every base reward (CR table + response
  floor) is multiplied by `LEVEL_AWARD_GROWTH ** (level − 1)` with
  `LEVEL_AWARD_GROWTH = 1.04` — one percentage point below the
  level-threshold growth (`1.05` in `_build_thresholds`), so each level
  takes ~1% more turns to clear than the one before it. `new_award_event`
  and `new_response_event` take a new `level=` arg; the CLI (`cmd_award`,
  `cmd_respond`) passes the ledger's current level.
- Per-tool tick XP (`DEFAULT_TICK_XP`) is unchanged at 10.

## [2.3.1] — 2026-08-23
Fix a portability gap that broke `/side-quest:setup` on a fresh machine.

- `xp-sync-daemon.sh` hard-requires `XP_MQTT_HOST` and exits immediately
  without it, but neither the launchd plist nor the systemd service
  template ever supplied one, and the setup agent never asked — so a
  fresh install would launch the daemon straight into a silent
  launchd/systemd crash-loop (respawn, fail, respawn, forever).
- `side-quest-setup` now asks (via `AskUserQuestion`) whether to wire up
  cross-machine MQTT sync before installing the daemon; a "no" skips
  daemon install entirely (XP stays fully functional, local-only) and a
  "yes" bakes the given hostname into both templates' new
  `XP_MQTT_HOST` env var and into the `award`/`tick`/`respond` hook
  commands in `settings.json` (hook subprocesses don't inherit the
  daemon's environment, so the CLI path needs it set independently).
  Idempotent — re-running reuses an already-configured broker host
  instead of re-asking.

## [2.3.0] — 2026-08-23
Sync the plugin's shipped scripts and docs with what's actually deployed.

- `respond` (the `Stop` hook's mechanical floor reward) now picks its
  flavor line from a dedicated pool for zero-tool-call turns
  (`random_zero_tool_flavor`) instead of a flat "handled 0 tool calls
  this turn" — it reads like an apology for a turn that may well have
  delivered real value with no tools needed. Turns with tool calls still
  use the existing tick-flavor pool.
- `DEFAULT_TOOL_FILLER` (the generic filler used when a tick has no tool
  name) changed from "the tools" to "the crew".
- No more hardcoded MQTT broker hostname anywhere in the plugin —
  `xp_core.py`/`xp-sync-daemon.sh` now require `XP_MQTT_HOST` to be set
  explicitly rather than falling back to a baked-in default, so the
  plugin ships with no personal infra details.
- `SKILL.md`'s "First-time setup" section had drifted from reality (a
  stale inline Stop-hook script, no mention of the `PostToolUse` tick
  hook at all) — replaced with a pointer to the `side-quest-setup` agent,
  the actual source of truth, plus a new "Ambient and mechanical XP"
  section documenting what the `award`/`tick`/`respond` paths each do.
- New `/side-quest:setup` slash command wrapping the `side-quest-setup`
  agent, matching the discoverable `/self-improvement:setup` pattern
  instead of requiring users to know to invoke the agent by name.

## [2.2.0] — 2026-08-07
Fresh-install bootstrap: new machines join the shared pool instead of
starting at zero.

- Root cause fixed: a newly-installed machine's ledger started counting
  from 0 and only accumulated future deltas, so it permanently diverged
  from every other machine's total instead of joining a shared pool.
- New `xp.sh bootstrap`: the sync daemon fetches the retained
  `sidequest/xp/state` snapshot once at startup, before subscribing to
  the event stream, and adopts it as the starting total *only* if the
  local ledger is genuinely fresh (`should_bootstrap_from_state` —
  never touches a ledger that's already earned anything locally).
  Records a zero-xp `bootstrap` history entry so the adoption is
  visible. Verified end-to-end with a real fresh ledger against the
  live broker.
- `xp.sh award`/`tick`/`respond`/`flush-outbox` now respect
  `XP_MQTT_HOST` for machines that can't resolve the broker's MagicDNS
  hostname (previously only the daemon's subscribe loop did) — needed
  for a machine whose Tailscale client isn't wired into system DNS.
- Daemon fix: `xp-sync-daemon.sh` used `timeout`, which doesn't exist on
  macOS by default; switched to `mosquitto_sub -W` (portable).

## [2.1.0] — 2026-08-07
Retained MQTT state, difficulty-scaled response reward, more flavor variety.

- New `sidequest/xp/state` retained MQTT message published after every
  award/tick-flush/remote-apply — any subscriber (including one that's
  been quiet a while) fetches the current total_xp/level immediately,
  no need to wait for the next event. Verified against the real broker.
- New `xp.sh respond` replaces the old flat-CR1 (200XP) Stop-hook
  fallback. Every response gets a mechanical, difficulty-scaled reward
  with a 10 XP floor — scaled by how many tool calls happened this turn
  (counted from this machine's own tick history, no transcript
  parsing). Self-debounces against a recent `ambient`/`stop-hook`
  award so a turn is never double-rewarded.
- `TICK_FLAVOR_TEMPLATES` expanded from 16 to 116 (all unique), including
  a batch of deliberately unhinged ones.

## [2.0.0] — 2026-08-07
Cross-machine XP sync over MQTT, plus granular hook-based ticks.

- XP ledger logic extracted from the `xp.sh` heredoc into `xp_core.py`
  (unit tested — `tests/test_xp_core.py`, `tests/test_cli.py`). `xp.sh`
  is now a thin CLI wrapper.
- New `xp.sh tick [tool]` — a small flat-XP award with a humorous
  Mad-Libs-style "why" (`TICK_FLAVOR_TEMPLATES`), fired via a
  `PostToolUse` hook so it costs zero tokens and needs no model
  judgment.
- Event-sourced, additive, idempotent sync over MQTT
  (`sidequest/xp/events`): every award/tick is applied locally first,
  then published; the new `xp-sync-daemon.sh` (launchd on macOS,
  systemd on Linux — templates included) subscribes on every machine
  and merges remote events into the local ledger by `event_id`, so the
  same total_xp/level is shared everywhere without last-write-wins data
  loss.
- Offline resilience: a local outbox queues any event that fails to
  publish and is drained on reconnect; ticks are coalesced into one
  publish every ~10s instead of one message per tool call.
- `statusline-command.sh`: the "+XX XP" toast now shows for 8s (was 5s)
  and includes the flavor text.
- Requires `mosquitto_pub`/`mosquitto_sub` (Homebrew: `mosquitto`) and a
  reachable broker — see `docs/superpowers/specs/2026-08-07-mqtt-xp-sync-design.md`
  for the full design and the `side-quest-setup` agent for install
  steps.

## [1.0.0] — 2026-06-09
Initial versioned release.
