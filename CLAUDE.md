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

**See `AGENTS.md`** — it is the canonical source for the required plugin directory layout, `plugin.json`/`SKILL.md`/`CHANGELOG.md` conventions, the `$CLAUDE_PLUGIN_ROOT` path convention (and its exceptions), and when a plugin needs a setup command. Read it before creating or modifying any plugin.

## PII Prevention — applies to every commit, not just plugin work

This repo mirrors to a **public** GitHub repo. Before committing *anything* — plugin code, `docs/`, root-level files — see `AGENTS.md`'s "PII Prevention" section and run its mandatory pre-commit sweep. It has already happened once (a personal Tailscale hostname, SSH username, and machine names leaked via `docs/` and a plugin, requiring a `git filter-repo` history rewrite across every branch). `docs/` is not exempt — everything in this repo gets committed and pushed the same way.

## Existing Plugins

cowsay, font-extractor, home-assistant, homebrew-dev, imsg, jellyfin, mastodon-cli, obsidian-cli, preflight-check, pushover, quack, recipe-fetch, self-improvement, side-quest, skills-manager, tailscale-policy-manager, touch_file, unifi-api, video-extract, wp-custom-theme, wp-local, youtube-data-api, yt-dlp.

`self-improvement` is the full **learning loop** in one plugin (as of v2.0.0 it absorbed the former standalone `learnings` plugin). It ships two skills + three agents:
- **Capture** (`learnings` skill + agent) — autonomous. Main Claude delegates to the `learnings` subagent **in the background** on every correction/error/suggestion; it appends `Status: pending` entries to `~/.learnings/`.
- **Review + auto-promote** (`self-improvement` skill + agent, plus the `learning-investigator` agent) — autonomous *and* manual. A gated `SessionEnd` hook spawns a detached headless `claude -p` review; `/self-improvement` runs the same pipeline foreground. The `learning-investigator` judges each entry against a conservative bar and the orchestrator auto-promotes qualifiers (user-scope) into `CLAUDE.md`, logging a revertible trail to `~/.learnings/CHANGELOG.md`. Undo with `/self-improvement:revert <PROMO-hex>`. Wire it up with `/self-improvement:setup`.

## Files to Know

- `AGENTS.md` — canonical plugin directory structure and authoring conventions, including the mandatory pre-commit PII sweep; read before creating or modifying any plugin, and before any commit
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
