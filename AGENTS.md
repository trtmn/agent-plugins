# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, etc.) for creating and modifying plugins in this repository. `CLAUDE.md` at the repo root points here for anything plugin-authoring related — this is the canonical source.

## Repository Overview

A Claude Code plugin marketplace. Plugins live under `plugins/`; `.claude-plugin/marketplace.json` at the repo root registers them all.

## Plugin Directory Structure

Each plugin lives under `plugins/`. **Folder name matches the plugin name** (`plugin.json` → `name`):

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json               # Required — {name, version, description}
├── CHANGELOG.md                  # Required — version history (Keep a Changelog format)
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
- **plugin.json is minimal.** Just `{name, version, description}` — description copied verbatim from SKILL.md frontmatter. Version follows SemVer (`MAJOR.MINOR.PATCH`). Every plugin must have one — check with:
  ```bash
  for f in plugins/*/.claude-plugin/plugin.json; do python3 -c "import json;print('$f', json.load(open('$f')).get('version','MISSING'))"; done
  ```
- **CHANGELOG.md is required.** Lives at the plugin root. Add a `## [x.y.z] — YYYY-MM-DD` entry when bumping the version. Patch = fix/tweak, Minor = new capability, Major = breaking change.
- **Scripts run standalone.** Only their output enters Claude's context. Bash scripts use `set -e`, status to stderr, machine-readable JSON to stdout.
- **References stay separate.** Large API docs and specs go in `references/` so they aren't loaded until the skill needs them.
- **Agent definitions default to background.** Any subagent shipped under `agents/` must include `"ALWAYS launch this agent with run_in_background: true"` in its description, so callers don't block the main conversation.
- **No shared build step.** Plugins are distributed as-is.
- **No automated tests, as a rule.** Evals in `evals/` are manual (invoke + verify) and gitignored. Exception: `side-quest` ships a real `pytest` suite (`tests/`) for its ledger/sync logic — that logic has enough state-machine complexity (event dedup, XP tiers, MQTT sync, coalescing) to warrant it. Follow the no-tests default unless a plugin's logic is similarly nontrivial and stateful, not just a thin CLI wrapper.
- **Absolute paths and identifiers are PII.** Never commit `/Users/<name>/` paths — use `~/`, `$HOME/`, or `$CLAUDE_PLUGIN_ROOT`. Don't hardcode personal hostnames, vault names, 1Password item UUIDs, or real email addresses in example output, design docs, or test fixtures — use `example.com`, `octocat`, `jane@example.com`, `<vault>`, `<item>` placeholders. This applies everywhere in the repo, not just `plugins/` — `docs/` design specs get committed and pushed to the public GitHub mirror too, and a personal Tailscale MagicDNS hostname, an SSH username, and real machine names leaked into git history this way once already (required a `git filter-repo` rewrite across every branch to remove). If a script needs a piece of personal infra (an MQTT broker host, a specific server), require it via an env var with **no hardcoded personal default** — fail loudly (`${VAR:?must be set}`) rather than silently falling back to your own infrastructure.
- **`$CLAUDE_PLUGIN_ROOT` resolves to the plugin root** (the directory containing `.claude-plugin/`), not the skill directory. A script at `plugins/<name>/skills/<name>/scripts/foo.sh` must be referenced as `${CLAUDE_PLUGIN_ROOT}/skills/<name>/scripts/foo.sh` — the `skills/<name>/` segment is easy to drop by accident (font-extractor and wp-local both shipped with this bug: `$CLAUDE_PLUGIN_ROOT/scripts/foo` pointing at a path that doesn't exist). Verify with a quick sweep before shipping:
  ```bash
  grep -rn "CLAUDE_PLUGIN_ROOT" plugins/*/skills/*/SKILL.md plugins/*/agents/*.md plugins/*/commands/*.md
  ```
  and check each result's path actually exists under the plugin directory. **Exception**: plugins whose scripts must also run *outside* any live Claude Code session — as a `settings.json` hook command, or a background daemon (launchd/systemd) — can't rely on `$CLAUDE_PLUGIN_ROOT` (it's only set inside a running session). Those plugins (`side-quest`, `self-improvement`) hoist their `scripts/` to the plugin root instead of nesting under `skills/<name>/`, and ship a setup step (see below) that deploys copies to a stable `$HOME` path.
- **Plugins that install anything outside the plugin cache need a setup command.** If a plugin merges hooks into `~/.claude/settings.json`, installs a daemon, or deploys scripts to a stable path so they work from a hook/daemon context (see above), it needs: (1) a setup **agent** that does the actual idempotent installation work (backgrounded per the rule above), and (2) a `/plugin-name:setup` **slash command** in `commands/` that wraps it, so users don't have to know to invoke the agent by name. `self-improvement` (`/self-improvement:setup`) and `side-quest` (`/side-quest:setup`) are the reference implementations. A plugin whose scripts only ever run inside a live Bash tool call (the common case) does not need this — `$CLAUDE_PLUGIN_ROOT` already resolves correctly at runtime, no deploy step required.

## Security

Never commit sensitive information to this repository. This includes, but is not limited to, API keys, secrets, credentials, private certificates, or any personally identifiable information (see the PII convention above for specifics on this repo's recurring failure mode). Always use environment variables, 1Password `op://` references, or other secret management to handle sensitive data required by skills or scripts.
