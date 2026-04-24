---
name: skills-manager
description: Install, remove, list, find, and update Claude Code skills using the `npx skills` CLI. Use this skill whenever the user wants to manage their agent skills — install a new skill, search the skills registry, remove a skill, check for updates, or update all skills. Also trigger for requests like "find me a skill for X", "install the Y skill", "what skills do I have installed", "remove the Z skill", or "are my skills up to date."
---

# Skills Manager

You manage skills using the `npx skills` CLI. Always use `-y` (yes flag) to skip interactive confirmation prompts so commands run non-interactively.

## Commands

### Find skills
```bash
npx skills find <query>
```
Returns a list of matching skills with install counts and URLs. Parse the output: skill identifiers look like `owner/repo@skill-name`.

### Install a skill
```bash
# Global (user-level, available across all projects) — the default
npx skills add <owner/repo@skill> -g -y

# Project-level (only current directory)
npx skills add <owner/repo@skill> -y

# Install to a specific agent
npx skills add <owner/repo@skill> -g -a claude-code -y

# Install all skills from a repo
npx skills add <owner/repo> --all -g -y
```

### List installed skills
```bash
npx skills list -g          # global skills
npx skills list             # project-level skills
npx skills list -g -a claude-code   # filter by agent
```

### Remove a skill
```bash
npx skills remove <skill-name> -g -y    # global
npx skills remove <skill-name> -y       # project
```

### Check for updates
```bash
npx skills check
```

### Update all skills
```bash
npx skills update
```

## Typical workflows

**User asks to find and install a skill:**
1. Run `npx skills find <relevant query>`
2. Show the user the results (name, install count, URL)
3. Ask which one they want, or if the best match is obvious, suggest it
4. Install with `npx skills add <identifier> -g -y`
5. Confirm what was installed and where

**User asks to remove a skill:**
1. If they named it, run `npx skills remove <name> -g -y`
2. If unsure of the exact name, first run `npx skills list -g` to find it

**User asks what skills they have:**
Run `npx skills list -g` and present the results clearly.

**User asks to update skills:**
1. Run `npx skills check` to show what's outdated
2. Run `npx skills update` to update everything, or ask if they want to be selective

## Notes

- Default to global (`-g`) install unless the user is clearly working on a project that should have its own skill set
- The `find` command output is non-interactive when a query argument is given — it prints results and exits
- Skill identifiers use the format `owner/repo@skill-name` (e.g., `vercel-labs/agent-skills@commit`)
- After installing a skill, it becomes available in the current session only after restarting Claude Code (let the user know)
