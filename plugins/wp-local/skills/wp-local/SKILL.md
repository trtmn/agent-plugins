---
name: wp-local
description: "Spin up and manage local WordPress demo sites using Docker Compose and WP-CLI. Use this skill whenever the user wants to create a local WordPress site, start or stop an existing site, list their local WordPress sites, or permanently destroy a site. Trigger on: \"spin up a WordPress site\", \"local WordPress\", \"new WordPress dev environment\", \"create a demo site\", \"WordPress demo\", \"start my WordPress\", \"stop my WordPress\", \"destroy WordPress site\", \"list my WordPress sites\", \"wp-local\"."
allowed-tools:
  - Bash
  - Agent
  - AskUserQuestion
---

# wp-local — Local WordPress Site Manager

Spin up fully functional local WordPress sites using Docker Compose. Each site gets its own port, isolated MySQL database, and WP-CLI-configured admin account with a forced password change on first login.

Sites persist in `~/wordpress-sites/<name>/` and survive reboots as long as Docker is running.

## Scripts

All scripts live at `~/.claude/skills/wp-local/scripts/`. They output JSON to stdout; progress and errors go to stderr.

| Script | Purpose |
|---|---|
| `check-deps.sh` | Verify Docker and Docker Compose are available and the daemon is running |
| `list.sh` | List all sites in `~/wordpress-sites/` with their running/stopped status |
| `create.sh <name> [title]` | Create a new site — takes ~1-2 min first run (image pull) |
| `start.sh <name>` | Start a stopped site |
| `stop.sh <name>` | Stop a running site (data is preserved) |
| `destroy.sh <name> <name>` | Permanently destroy a site — second arg must match first (safety guard) |

## Workflow

### Step 1: Check dependencies

Delegate to the `wp-local-ops` agent synchronously (NOT in background — the result is needed before proceeding):

> Operation: check-deps

Parse the JSON response. If `ok` is false, display each message from the `errors` array clearly and stop. Do not proceed until Docker is running and Compose is available.

### Step 2: Determine intent

If the user's message already specifies the action (e.g. "create a site called my-demo", "stop my WordPress site", "list my sites", "destroy the test site"), go directly to that action — skip the question.

Otherwise, ask:

```
AskUserQuestion:
  question: "What would you like to do with your local WordPress sites?"
  options:
    - Create a new site — spin up a fresh WordPress instance with WP-CLI
    - List my sites — show all local WordPress sites and their status
    - Start a site — bring a stopped site back online
    - Stop a site — pause a running site (data is preserved)
    - Destroy a site — permanently delete a site and all its data
```

### Step 3: Execute the action

---

#### Create

1. **Site name:** Extract from the user's message if present. Otherwise ask:
   > "What should the site be called? Use lowercase letters and hyphens only (e.g. `my-demo`)."

2. **Site title:** Extract from context if obvious. Otherwise use the site name as the title (do not ask unless the user volunteers it — keep the flow fast).

3. Tell the user:
   > "Creating WordPress site `<name>` — this takes about 1-2 minutes the first time while Docker pulls images. I'll give you the setup URL when it's ready."

4. Run via Bash:
   ```bash
   bash ~/.claude/skills/wp-local/scripts/create.sh "<name>" "<title>"
   ```
   (stderr will show progress; capture stdout as JSON)

5. Parse the JSON result:
   - **If `ok` is true**, send the user to the setup wizard:

     ```
     WordPress is ready! Complete your setup in the browser:

     Setup URL:   http://localhost:<port>/wp-admin/install.php
     Site URL:    http://localhost:<port>

     WP-CLI is installed in the container for later use:
       docker exec --user www-data <name>-wordpress-1 wp <command>
     ```

   - **If `ok` is false**, show the `message` field and suggest:
     - Check Docker is running: `docker ps`
     - Check container logs: `docker logs <name>-wordpress-1`
     - If it was a name conflict, suggest a different name.

---

#### List

Delegate to `wp-local-ops` synchronously:

> Operation: list

Format the JSON array as a readable table:

```
Name          Status    URL                         Path
-----------   --------  --------------------------  ----------------------------------
my-demo       running   http://localhost:8080        ~/wordpress-sites/my-demo
old-project   stopped   http://localhost:8081        ~/wordpress-sites/old-project
```

If the array is empty, tell the user they have no local WordPress sites yet and offer to create one.

---

#### Start

1. Get the site name (from user's message, or ask: "Which site would you like to start?").
2. Delegate to `wp-local-ops` synchronously:
   > Operation: start `<name>`
3. On success, show the site URL. On failure, surface the `message`.

---

#### Stop

1. Get the site name (from user's message, or ask: "Which site would you like to stop?").
2. Delegate to `wp-local-ops` synchronously:
   > Operation: stop `<name>`
3. Confirm stopped, or surface the `message` on failure.

---

#### Destroy

This is irreversible. Follow these steps carefully:

1. Get the site name if not already known.

2. Warn the user explicitly before asking anything:
   > "This will permanently delete the `<name>` site and ALL its data — the database, uploaded files, plugins, and themes. This **cannot be undone**."

3. Ask for confirmation:
   ```
   AskUserQuestion:
     question: "Are you sure you want to permanently destroy '<name>'?"
     options:
       - "Yes, destroy <name> — I understand this cannot be undone"
       - "No, cancel — keep the site"
   ```

4. **If cancelled:** Confirm: "Cancelled. Site `<name>` is untouched."

5. **If confirmed:** Run via Bash:
   ```bash
   bash ~/.claude/skills/wp-local/scripts/destroy.sh "<name>" "<name>"
   ```

6. On success: "Site `<name>` has been destroyed. All data is permanently deleted."
7. On failure: surface the `message` from the JSON response.

---

## Error Handling

| Situation | Response |
|---|---|
| Script returns `{"ok":false,...}` | Surface the `message` field with relevant context |
| Docker not running | "Please open Docker Desktop and try again." |
| Site name conflict on create | "A site named `<name>` already exists. Use `list` to see your sites or choose a different name." |
| Create timeout | Show: `docker logs <name>-wordpress-1` for debugging |
| Scripts not found | "The wp-local scripts are not installed. Run: `/plugin install wp-local@agent-plugins`" |

## Notes

- **Multiple sites run simultaneously** — each gets its own port (starting at 8080) and isolated Docker Compose project.
- **Sites are persistent** — data lives in Docker named volumes and survives container restarts.
- **WP-CLI is installed at create time** — subsequent commands: `docker exec --user www-data <name>-wordpress-1 wp <command>`
- **Secrets are in `.env`** — stored at `~/wordpress-sites/<name>/.env` (chmod 600). Do not print this file.
