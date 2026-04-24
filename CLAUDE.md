# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Claude Code plugin marketplace. Plugins live under `plugins/`; `.claude-plugin/marketplace.json` at the repo root registers them all.

Install path:
```
/plugin marketplace add trtmn/agent-plugins
/plugin install <plugin-name>@agent-plugins
```

## Plugin Directory Structure

Each plugin lives under `plugins/`. **Folder name matches the plugin name** (`plugin.json` → `name`):

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json               # Required — {name, description}
├── skills/<plugin-name>/
│   ├── SKILL.md                  # Canonical skill definition (YAML frontmatter + body)
│   ├── scripts/                  # Optional executables invoked by the skill
│   └── references/               # Optional reference docs loaded on-demand
├── agents/                       # Optional subagent definitions (plugin root, NOT under skills/)
├── commands/                     # Optional slash command definitions (plugin root)
└── evals/                        # Optional manual test prompts (gitignored)
```

`agents/` and `commands/` live at the **plugin root**, not inside `skills/<name>/`. Only skill content lives under `skills/<name>/`.

## Conventions

- **SKILL.md is the contract.** YAML frontmatter must include `name`, `description`, and `allowed-tools`. The `name` must match the folder name and the `skills/<name>/` directory name.
- **plugin.json is minimal.** Just `{name, description}` — description copied verbatim from SKILL.md frontmatter.
- **Scripts run standalone.** Only their output enters Claude's context. Bash scripts use `set -e`, status to stderr, machine-readable JSON to stdout.
- **References stay separate.** Large API docs and specs go in `references/` so they aren't loaded until the skill needs them.
- **Agent definitions default to background.** Any subagent shipped under `agents/` must include `"ALWAYS launch this agent with run_in_background: true"` in its description, so callers don't block the main conversation.
- **No shared build step.** Plugins are distributed as-is.
- **No automated tests.** Evals in `evals/` are manual (invoke + verify) and gitignored.
- **Absolute paths and identifiers are PII.** Never commit `/Users/<name>/` paths — use `~/`, `$HOME/`, or `$CLAUDE_PLUGIN_ROOT`. Don't hardcode personal hostnames, vault names, 1Password item UUIDs, or real email addresses in example output; use `example.com`, `octocat`, `jane@example.com`, `<vault>`, `<item>` placeholders.

## Existing Plugins

cowsay, font-extractor, home-assistant, homebrew-dev, imsg, learnings, mastodon-cli, obsidian-cli, preflight-check, pushover, quack, recipe-fetch, self-improvement, skills-manager, tailscale-policy-manager, touch_file, unifi-api, wp-custom-theme, youtube-data-api.

`learnings` and `self-improvement` are a pair:
- `learnings` — autonomous capture. Main Claude delegates to the `learnings` subagent **in the background** on every correction/error/suggestion.
- `self-improvement` — user-triggered review/promote. `/self-improvement` delegates to the `self-improvement` subagent, which proposes promotions to CLAUDE.md for human approval.

## Files to Know

- `AGENTS.md` — AI agent guidance for creating and modifying plugins
- `.claude-plugin/marketplace.json` — marketplace manifest listing all plugins
- `.gitignore` — excludes `**/.claude/settings.local.json`, `**/evals/`, workspace dirs, `.DS_Store`

## Local User-Scope Symlinks

For day-to-day use on the author's machine, plugin agents/commands can be symlinked into `~/.claude/` so they resolve at runtime outside plugin-install context:

```bash
ln -sf "$(pwd)/plugins/learnings/agents/learnings.md" ~/.claude/agents/learnings.md
ln -sf "$(pwd)/plugins/self-improvement/agents/self-improvement.md" ~/.claude/agents/self-improvement.md
ln -sf "$(pwd)/plugins/self-improvement/commands/self-improvement.md" ~/.claude/commands/self-improvement.md
```

## History

Split out from [trtmn/agent-skills](https://github.com/trtmn/agent-skills) as a fresh, PII-scrubbed, plugin-formatted rewrite. Fresh history; no legacy.
