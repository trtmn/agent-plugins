Install or update the side-quest plugin's runtime files and settings on this machine.

Delegate to the `side-quest-setup` subagent via the Agent tool (`subagent_type: side-quest-setup`), launched with `run_in_background: true` per its own description. Tell the user it's running in the background and you'll report when it finishes — do not poll or block on it.

The subagent is idempotent — safe to re-run after every plugin update. It:
- Deploys `xp.sh`, `xp_core.py`, `xp-sync-daemon.sh`, and `statusline-command.sh` to their stable paths under `~/.claude/`.
- Installs the cross-machine MQTT sync daemon as a launchd agent (macOS) or systemd user service (Linux).
- Merges the `statusLine` block, the `Stop` hook, and the `PostToolUse` tick hook into `~/.claude/settings.json` — without touching any other hooks already there.
- Asks for approval (via `AskUserQuestion`) before adding the ambient XP rule to `~/.claude/CLAUDE.md`.

When the notification arrives, relay the subagent's final checklist report verbatim.

If the plugin isn't installed, tell the user to run `/plugin install side-quest@agent-plugins` first.
