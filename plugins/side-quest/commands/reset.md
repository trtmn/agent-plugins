Reset the side-quest XP ledger to a specific total. **Pool-wide and destructive** — every machine on the shared MQTT sync adopts the new total.

## 1. Get the target total

`$ARGUMENTS` may already contain the target number. If not, ask the user what total to reset to (a plain question — this is the one number only they can decide). "Wipe" / "start over" means `0`.

## 2. Confirm — always, no exceptions

Show the user, then get an explicit yes via `AskUserQuestion`:

- **Current total** on this machine: run `~/.claude/side-quest/xp.sh status` and quote `total_xp` / `level`.
- **Target total** and what it does: "This bumps a shared epoch and publishes it, so *every* machine syncing on this pool adopts `<target>` — up or down — immediately if online, on reconnect otherwise. The old totals are not recoverable from the ledger."

If the user hasn't clearly asked for a reset in this turn, do not run it just because they invoked the command — confirm first.

## 3. Run it

Check `~/.claude/settings.json` for whether the existing `xp.sh` hook commands are prefixed with `XP_MQTT_HOST=...` (MQTT sync configured). If so, use the same prefix; if not, omit it (local-only).

```
XP_MQTT_HOST=<broker-from-settings> ~/.claude/side-quest/xp.sh reset-ledger <target> --yes
```

Without `--yes` the command prints the warning and exits without changing anything — that's the dry run. `--yes` is required to actually reset.

## 4. Report

Relay the resulting `{total_xp, level, epoch}` JSON. Remind the user that other machines pick it up on their next sync — online ones within seconds, offline ones when their daemon reconnects.
