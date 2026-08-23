# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Claude Code plugin marketplace. Plugins live under `plugins/`; `.claude-plugin/marketplace.json` at the repo root registers them all.

Install path:
```
/plugin marketplace add trtmn/agent-plugins
/plugin install <plugin-name>@agent-plugins
```

## Plugin Directory Structure and Conventions

**See `AGENTS.md`** — it is the canonical source for the required plugin directory layout, `plugin.json`/`SKILL.md`/`CHANGELOG.md` conventions, the `$CLAUDE_PLUGIN_ROOT` path convention (and its exceptions), when a plugin needs a setup command, and the PII rule. Read it before creating or modifying any plugin.

## Existing Plugins

cowsay, font-extractor, home-assistant, homebrew-dev, imsg, jellyfin, mastodon-cli, obsidian-cli, preflight-check, pushover, quack, recipe-fetch, self-improvement, side-quest, skills-manager, tailscale-policy-manager, touch_file, unifi-api, video-extract, wp-custom-theme, wp-local, youtube-data-api.

`self-improvement` is the full **learning loop** in one plugin (as of v2.0.0 it absorbed the former standalone `learnings` plugin). It ships two skills + three agents:
- **Capture** (`learnings` skill + agent) — autonomous. Main Claude delegates to the `learnings` subagent **in the background** on every correction/error/suggestion; it appends `Status: pending` entries to `~/.learnings/`.
- **Review + auto-promote** (`self-improvement` skill + agent, plus the `learning-investigator` agent) — autonomous *and* manual. A gated `SessionEnd` hook spawns a detached headless `claude -p` review; `/self-improvement` runs the same pipeline foreground. The `learning-investigator` judges each entry against a conservative bar and the orchestrator auto-promotes qualifiers (user-scope) into `CLAUDE.md`, logging a revertible trail to `~/.learnings/CHANGELOG.md`. Undo with `/self-improvement:revert <PROMO-hex>`. Wire it up with `/self-improvement:setup`.

## Files to Know

- `AGENTS.md` — canonical plugin directory structure and authoring conventions; read before creating or modifying any plugin
- `.claude-plugin/marketplace.json` — marketplace manifest listing all plugins
- `.gitignore` — excludes `**/.claude/settings.local.json`, `**/evals/`, workspace dirs, `.DS_Store`

## Local User-Scope Symlinks

For day-to-day use on the author's machine, plugin agents/commands can be symlinked into `~/.claude/` so they resolve at runtime outside plugin-install context:

```bash
ln -sf "$(pwd)/plugins/self-improvement/agents/learnings.md" ~/.claude/agents/learnings.md
ln -sf "$(pwd)/plugins/self-improvement/agents/self-improvement.md" ~/.claude/agents/self-improvement.md
ln -sf "$(pwd)/plugins/self-improvement/agents/learning-investigator.md" ~/.claude/agents/learning-investigator.md
ln -sf "$(pwd)/plugins/self-improvement/commands/self-improvement.md" ~/.claude/commands/self-improvement.md
```

Or just run `/self-improvement:setup` (which also deploys the scripts, merges the SessionEnd hook, and patches `~/.claude/CLAUDE.md`).

## History

Split out from [trtmn/agent-skills](https://github.com/trtmn/agent-skills) as a fresh, PII-scrubbed, plugin-formatted rewrite. Fresh history; no legacy.
