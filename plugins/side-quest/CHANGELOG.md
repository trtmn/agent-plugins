# Changelog

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
