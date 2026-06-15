Wire up the self-improvement plugin (capture + autonomous review) after installation or update.

1. Read `~/.claude/plugins/installed_plugins.json` and find the `installPath` for `self-improvement@agent-plugins`.
2. Run `bash <installPath>/scripts/setup.sh` and show the output.
3. If the plugin isn't installed, tell the user to run `/plugin install self-improvement@agent-plugins` first.

The setup script is idempotent. It:
- Symlinks the `learnings`, `self-improvement`, and `learning-investigator` agents into `~/.claude/agents/` (force-overwriting any stale `learnings.md` link from the old standalone plugin, and verifying each link resolves).
- Symlinks the `/self-improvement` and `/self-improvement:revert` commands into `~/.claude/commands/`.
- Deploys `review-trigger.sh`, `pending-count.sh`, and `revert.sh` to `~/.claude/self-improvement/`.
- Merges the gated `SessionEnd` review hook into `~/.claude/settings.json`.
- Patches `~/.claude/CLAUDE.md` (passive-logging delegation + autonomous-review note).

After running, note the prerequisite it prints: for the Pushover summary to fire from the autonomous run, `OP_SERVICE_ACCOUNT_TOKEN` must be reachable by background processes (exported in your shell profile, or in the file the trigger reads).
