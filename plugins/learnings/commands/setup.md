Wire up the learnings plugin after installation. This creates the agent symlink and patches CLAUDE.md so passive logging activates.

1. Read `~/.claude/plugins/installed_plugins.json` and find the `installPath` for `learnings@agent-plugins`.
2. Run `bash <installPath>/scripts/setup.sh` and show the output.
3. If the plugin isn't installed, tell the user to run `/plugin install learnings@agent-plugins` first.
