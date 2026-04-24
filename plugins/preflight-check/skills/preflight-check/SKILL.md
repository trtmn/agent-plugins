---
name: preflight-check
description: >
  Validate all external service connections before starting work. Trigger this skill proactively
  whenever a task involves GitHub (gh CLI, repos, PRs, issues), Atlassian (Jira, Confluence, any
  mcp__claude_ai_Atlassian__ tool), or UniFi (network management, UNIFI_API_KEY). Also trigger
  when the user explicitly says "preflight", "check connections", "validate services", "are my
  APIs working", "check my integrations", "test my setup", or "verify access". If any external
  service call fails unexpectedly during a task, trigger this skill to diagnose the issue. The
  goal is to catch auth problems early rather than failing mid-task.
---

# Preflight Connection Validator

Validate external service connections and report a clear status table before proceeding with work.

## Why this exists

Nothing wastes more time than getting halfway through a task only to discover an API key expired or an MCP server is down. This skill front-loads that pain — check everything first, fix what's broken, then start real work with confidence.

## Services to validate

Check each of these in order. For each service, make the minimal request that proves authentication works.

### 1. GitHub (`gh` CLI)

Run `gh auth status` via Bash. Look for the "Logged in" confirmation line. Extract:
- Account name
- Active scopes
- Auth method (keyring, token, etc.)

If it fails, suggest `gh auth login`.

### 2. Atlassian (MCP server)

Call `mcp__claude_ai_Atlassian__atlassianUserInfo` with no parameters. If it returns user info (name, email, account_id), the MCP connection and OAuth are working. Extract:
- User name
- Email
- Account status

If it fails, the MCP server may not be running or the OAuth token may have expired. Tell the user to check their MCP server configuration or re-authenticate.

### 3. UniFi (API key)

Load `UNIFI_API_KEY` from the environment. The key should be available as an environment variable. Make a request to the UniFi controller to verify the key works:

```python
import urllib.request
import ssl
import os
import json

key = os.environ.get("UNIFI_API_KEY", "")
if not key:
    print("MISSING: UNIFI_API_KEY not set")
else:
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(
        "https://192.168.1.1/proxy/network/integration/v1/sites",
        headers={"X-API-KEY": key, "Accept": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        data = json.loads(resp.read())
        print(f"OK: {len(data.get('data', []))} site(s) found")
    except Exception as e:
        print(f"FAILED: {e}")
```

If `UNIFI_API_KEY` is not in the environment, check for a `.env` file in the project root and load it with `python-dotenv`. Never try to `cat` or `source` the `.env` directly — it may be a 1Password FIFO pipe.

If the key is missing entirely, tell the user to set `UNIFI_API_KEY` (generated in UniFi Network App > Integrations > Create New API Key).

## Output format

Present results as a markdown table:

```
| Service    | Auth Method     | Status | Details                        |
|------------|-----------------|--------|--------------------------------|
| GitHub     | gh CLI/keyring  | OK     | Logged in as octocat           |
| Atlassian  | MCP/OAuth       | OK     | Jane Doe (jane@example.com)    |
| UniFi      | API Key         | OK     | 2 site(s) found                |
```

Use these status values:
- **OK** — authenticated and responsive
- **FAILED** — auth attempted but rejected (include the error)
- **MISSING** — credentials not found (say where to get them)
- **UNREACHABLE** — network/timeout error (could be VPN, firewall, etc.)

## After the check

- If all services show OK, say so briefly and proceed with whatever the user needs.
- If any service failed, stop and report exactly what went wrong with specific error messages. Don't proceed with work that depends on a broken service — help the user fix it first.
- If a service is MISSING or FAILED but isn't needed for the current task, note it as a warning but don't block.

## Adding new services

If the user mentions a new service they want checked, add it to the validation sequence. The pattern is always the same: find credentials, make the smallest possible authenticated request, report the result.
