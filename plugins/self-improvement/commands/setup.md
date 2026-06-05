Wire up the self-improvement plugin after installation. This creates the agent symlink and ensures the learnings dependency is also wired up.

1. Read `~/.claude/plugins/installed_plugins.json` and find the `installPath` for `self-improvement@agent-plugins`.
2. Run `bash <installPath>/scripts/setup.sh` and show the output.
3. If the plugin isn't installed, tell the user to run `/plugin install self-improvement@agent-plugins` first.
