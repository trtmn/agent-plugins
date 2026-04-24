# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

This is a **Claude Code skill** for controlling Home Assistant smart home devices via the REST API. It follows the [skills.sh](https://skills.sh) specification and lives within the `agent-skills` monorepo.

A skill is not a traditional software project — it's a set of instructions (SKILL.md), reference docs, and helper scripts that Claude Code uses at runtime to perform tasks on behalf of the user.

## Structure

- `SKILL.md` — The skill definition. This is the core file: it contains the trigger description, allowed tools, setup flow, workflow instructions, and all operational guidance Claude follows when the skill is invoked. Changes here directly affect how Claude behaves.
- `references/rest-api.md` — Complete Home Assistant REST API endpoint reference. Claude reads this when it needs detailed API info beyond what SKILL.md covers.
- `scripts/discover_entities.sh` — Bash script that queries HA's `/api/states` endpoint and groups entities by domain. Accepts an optional domain filter argument. Requires `HA_URL` and `HA_TOKEN` env vars (loaded from `~/.config/home-assistant/.env`).
- `evals/evals.json` — Evaluation prompts and expected outputs for testing skill behavior.
- `.claude/settings.local.json` — Auto-approved tool permissions (WebFetch for HA docs, Bash for sourcing env).

## Key Architectural Details

- **Authentication**: Credentials (`HA_URL`, `HA_TOKEN`) are stored in `~/.config/home-assistant/.env` with 600 permissions. The skill sources this file before any API call.
- **All HA interaction is via curl**: The skill uses `curl` against the REST API — no HA Python libraries or WebSocket connections.
- **Confirmation before actions**: SKILL.md mandates that Claude must ask for user confirmation before any service call that changes device state. This is a deliberate safety constraint for physical-world actions.
- **Entity discovery pattern**: The standard workflow is discover → query → confirm → act. The discovery script maps friendly names to entity IDs so Claude can translate natural language to API calls.

## Running Evals

Evals are defined in `evals/evals.json`. Each eval has a prompt and expected output description. There is no automated eval runner in this repo — evals are tested manually by invoking the skill with each prompt and verifying the behavior matches expectations.

## Editing Guidelines

- When modifying `SKILL.md`, keep the `allowed-tools` frontmatter in sync with what the skill actually needs. The current allowlist is: sourcing the env file, curl commands, and bash commands.
- The `<skill-path>` placeholder in SKILL.md is resolved at runtime by the skill loader — do not replace it with a hardcoded path.
- `references/rest-api.md` should stay in sync with the [official HA REST API docs](https://developers.home-assistant.io/docs/api/rest/).
