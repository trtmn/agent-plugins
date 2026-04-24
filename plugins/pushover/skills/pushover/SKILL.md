---
name: pushover
description: Send push notifications and manage delivery groups via the Pushover API using the `pushover` CLI (a restish wrapper with 1Password auth). Use this skill whenever the user wants to send a notification, check message limits, manage groups, or do anything with Pushover. Trigger on phrases like "send a push notification", "notify me", "pushover", "send an alert", "check my message limits", "push a notification to my phone", or any mention of Pushover.
allowed-tools:
  - Bash(pushover *:*)
  - Bash(restish pushover *:*)
---

# Pushover API Skill

Send push notifications to Android, iOS, and Desktop devices via the Pushover API.
Uses a custom OpenAPI spec with [restish](https://rest.sh/) and 1Password for credential injection.

## CLI (restish) — Preferred

A `pushover` CLI wrapper is installed at `~/.local/bin/pushover`. It uses restish with a hand-written OpenAPI spec and injects the app token + user key from 1Password automatically via `op run`.

### Quick send (most common)

```bash
# Simple message
pushover send "Deploy complete"

# With title, priority, and sound
pushover send "Server down!" --title "Alert" --priority 1 --sound siren

# All send options
pushover send "message" \
  --title "Title" \
  --priority 1 \
  --sound cosmic \
  --url "https://example.com" \
  --url-title "Details" \
  --device iPhone-16-Pro \
  --html \
  --ttl 3600
```

### GET endpoints (auto-injected token)

```bash
# Check message quota
pushover get-app-limits

# List available notification sounds
pushover list-sounds

# Check license credits
pushover get-license-credits

# Check emergency receipt status
pushover get-receipt-status RECEIPT_ID
```

### POST endpoints (JSON input, auto-injected credentials)

```bash
# Validate user key
pushover validate-user '{}'

# Send via full JSON (token + user merged automatically)
pushover send-message '{"message":"Hello","title":"Test","priority":0}'

# Pipe JSON
echo '{"message":"Backup done","sound":"cashregister"}' | pushover send-message

# Cancel emergency notification
pushover cancel-receipt '{}' RECEIPT_ID

# Cancel by tag
pushover cancel-by-tag '{}' TAG_NAME
```

### Full command list

Run `pushover --help` (or `restish pushover --help`) for all 18 commands:

| Command | Description |
|---|---|
| `send` | Shorthand — send a notification with flags |
| `send-message` | Send a notification (JSON input) |
| `validate-user` | Validate a user or group key |
| `get-app-limits` | Check monthly message quota |
| `list-sounds` | List available notification sounds |
| `send-glance` | Push data to a Glances widget (Apple Watch) |
| `get-receipt-status` | Check emergency notification status |
| `cancel-receipt` | Cancel emergency notification retries |
| `cancel-by-tag` | Cancel emergency notifications by tag |
| `list-groups` | List delivery groups |
| `create-group` | Create a new delivery group |
| `get-group` | Get group info and members |
| `add-user-to-group` | Add a user to a group |
| `remove-user-from-group` | Remove a user from a group |
| `disable-user-in-group` | Disable a user in a group |
| `enable-user-in-group` | Re-enable a user in a group |
| `rename-group` | Rename a delivery group |
| `migrate-subscription` | Migrate a user key to a subscription key |
| `assign-license` | Assign a license credit |
| `get-license-credits` | Check remaining license credits |

## Restish configuration

- **Config:** `~/Library/Application Support/restish/apis.json` — `pushover` entry with `base: https://api.pushover.net`
- **Spec file:** `~/Library/Application Support/restish/specs/pushover-v1.json` (hand-written — Pushover does not publish an OpenAPI spec)
- **Auth:** App token + user key from 1Password, injected via `op run` in the wrapper
- **Wrapper:** `~/.local/bin/pushover` — handles `op run`, credential injection into GET flags and POST JSON bodies, and the `send` shorthand

### 1Password references

- **App token:** `op://<vault>/<pushover-item>/Applications/<App Token Field>`
- **User key:** `op://<vault>/<pushover-item>/User Key/<User Key Field>`

Pushover supports multiple app tokens in a single 1Password item (one per application). The wrapper picks a default field name; override via the wrapper if you maintain several.

## Priority levels

| Value | Name | Behavior |
|---|---|---|
| `-2` | Lowest | No notification generated |
| `-1` | Low | No sound or vibration |
| `0` | Normal | Default behavior |
| `1` | High | Bypasses quiet hours |
| `2` | Emergency | Repeats until acknowledged; requires `retry` and `expire` |

Emergency priority (`2`) returns a receipt ID for tracking acknowledgment. Use `get-receipt-status` to poll and `cancel-receipt` to stop retries.

## Rate limits

- **Free tier:** 10,000 messages/month per app (25,000 for one team-owned app)
- **HTTP 429** returned when limit exceeded
- **Response headers:** `X-Limit-App-Limit`, `X-Limit-App-Remaining`, `X-Limit-App-Reset`
- **Glances:** max 50 updates/day on Apple Watch, minimum 20 minutes between calls

Check remaining quota with `pushover get-app-limits`.

## Message limits

- **Body:** 1024 4-byte UTF-8 characters
- **Title:** 250 characters
- **URL:** 512 characters
- **URL title:** 100 characters
- **Attachment:** 5 MB maximum

## Response format

**Success (HTTP 200):**
```json
{"status": 1, "request": "uuid"}
```

**Error (HTTP 4xx):**
```json
{"status": 0, "request": "uuid", "errors": ["description"]}
```

## Recreating the restish setup from scratch

If restish or the `pushover` wrapper aren't installed, follow these steps.

**1. Install restish:**
```bash
brew install restish
```

**2. Place the OpenAPI spec:**

Pushover does not publish an OpenAPI spec. The spec at `~/Library/Application Support/restish/specs/pushover-v1.json` was hand-written from the [Pushover API docs](https://pushover.net/api). Copy it from this repo or regenerate from the docs.

**3. Add the pushover API to restish config:**

Add a `pushover` entry to `~/Library/Application Support/restish/apis.json`:
```json
{
  "pushover": {
    "base": "https://api.pushover.net",
    "spec_files": [
      "~/Library/Application Support/restish/specs/pushover-v1.json"
    ]
  }
}
```

**4. Create the wrapper script:**

Copy `scripts/pushover` from this skill to `~/.local/bin/pushover` and make it executable:
```bash
cp scripts/pushover ~/.local/bin/pushover
chmod +x ~/.local/bin/pushover
```

The wrapper handles three modes:
- **`send` shorthand** — parses `--title`, `--priority`, `--sound`, etc. into JSON
- **GET commands** — injects `--token` as a CLI flag
- **POST commands** — merges `token` and `user` into JSON input

All credentials are injected via `op run` from 1Password — never exposed to stdout.

**5. Verify:**
```bash
pushover get-app-limits
pushover send "Test notification"
```

## Common patterns

**Send a simple notification:**
```bash
pushover send "Deploy to production complete" --title "CI/CD"
```

**Send a high-priority alert with a link:**
```bash
pushover send "Disk usage at 95%" --title "Server Alert" --priority 1 --url "https://grafana.local/d/disk"
```

**Send an emergency notification (repeats until acknowledged):**
```bash
pushover send-message '{"message":"Site is DOWN","title":"CRITICAL","priority":2,"retry":60,"expire":3600}'
```

**Check if a user key is valid:**
```bash
pushover validate-user '{}'
```

**List all sounds to pick one:**
```bash
pushover list-sounds
```

**Check remaining monthly quota:**
```bash
pushover get-app-limits
```
