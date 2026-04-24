---
name: imsg
description: Terminal-based iMessage and SMS management via the command line. Use this skill whenever the user mentions texting, messaging, iMessage, SMS, conversations, chat history, message backups, or any interaction with their Messages database. Trigger for requests to send/receive messages, view conversation history, list chats, watch for incoming texts, export or backup messages, or manage iMessage/SMS data—even if the user doesn't explicitly say "iMessage" or "SMS". This is the right skill for anything involving text messages, group chats, or the Messages app accessed from the terminal.
---

# imsg

The `imsg` command-line tool enables you to send and read iMessage and SMS messages directly from the terminal, query your Messages database, and watch for incoming messages.

## ⚠️ Important Privacy & Database Notes

- **Database Access**: `imsg` reads from your local Messages database (`~/Library/Messages/chat.db`). This is a sensitive file containing your complete message history.
- **Permissions**: macOS may prompt for permissions when accessing the Messages database. Terminal needs Full Disk Access on newer macOS versions.
- **Data Sensitivity**: Be cautious when working with message history — it contains private conversations.
- **Database Locking**: If Messages.app is open, the database may be locked. Close Messages.app if you encounter access issues.

## Commands Overview

`imsg` has four main commands:

1. **`chats`** — List your recent iMessage/SMS conversations
2. **`history`** — Show message history for a specific chat
3. **`watch`** — Stream incoming messages in real-time
4. **`send`** — Send a message (text and/or attachment)
5. **`rpc`** — Run JSON-RPC over stdin/stdout (advanced)

---

## chats — List Conversations

List recent iMessage and SMS conversations from your Messages database.

### Usage
```
imsg chats [options]
```

### Options
- `--limit <number>` — Number of chats to list (e.g., `--limit 5`)
- `--json` or `-j` — Output as machine-readable JSON
- `--db <path>` — Custom path to chat.db (defaults to `~/Library/Messages/chat.db`)
- `-v, --verbose` — Enable verbose logging
- `--log-level <level>` — Set log level: `trace|verbose|debug|info|warning|error|critical`

### Examples
```bash
# List 10 most recent conversations
imsg chats --limit 10

# List conversations as JSON (easier to parse)
imsg chats --limit 5 --json

# List all conversations (no limit)
imsg chats
```

---

## history — Show Message History

Retrieve message history for a specific conversation. Requires a chat ID (which you get from `imsg chats`).

### Usage
```
imsg history [options]
```

### Options
- `--chat-id <id>` — Chat ID from `imsg chats` (required unless using `--participants`)
- `--limit <number>` — Number of messages to show
- `--participants <handles>` — Filter by participant phone/email (e.g., `+15551234567` or `user@example.com`)
- `--start <ISO8601>` — Start date (inclusive), e.g., `2025-01-01T00:00:00Z`
- `--end <ISO8601>` — End date (exclusive)
- `--attachments` — Include attachment metadata in results
- `--json` or `-j` — Output as JSON
- `--db <path>` — Custom path to chat.db
- `-v, --verbose` — Enable verbose logging
- `--log-level <level>` — Set log level

### Examples
```bash
# Last 20 messages from chat ID 1
imsg history --chat-id 1 --limit 20

# Last 50 messages with attachment info
imsg history --chat-id 1 --limit 50 --attachments

# Messages in date range (as JSON)
imsg history --chat-id 1 --start 2025-01-01T00:00:00Z --end 2025-02-01T00:00:00Z --json

# Messages from specific participant
imsg history --chat-id 1 --participants +15551234567 --limit 10
```

---

## watch — Stream Incoming Messages

Watch for and stream incoming iMessage/SMS messages in real-time. Useful for monitoring conversations without opening Messages.app.

### Usage
```
imsg watch [options]
```

### Options
- `--chat-id <id>` — Limit to a specific chat (optional)
- `--since-rowid <id>` — Start watching after this message rowid (skip old messages)
- `--participants <handles>` — Filter by participant phone/email
- `--start <ISO8601>` — ISO8601 start time (inclusive)
- `--end <ISO8601>` — ISO8601 end time (exclusive)
- `--debounce <duration>` — Debounce filesystem events (e.g., `250ms`) to avoid duplicate notifications
- `--attachments` — Include attachment metadata
- `--json` or `-j` — Output as JSON (one JSON object per message)
- `--db <path>` — Custom path to chat.db
- `-v, --verbose` — Enable verbose logging
- `--log-level <level>` — Set log level

### Examples
```bash
# Watch all incoming messages
imsg watch

# Watch specific chat only (with attachments)
imsg watch --chat-id 1 --attachments

# Watch from specific participant
imsg watch --participants +15551234567

# Watch with debouncing (less spam)
imsg watch --chat-id 1 --debounce 500ms --json
```

---

## send — Send a Message

Send an iMessage or SMS message. You can send text, attachments, or both.

### Usage
```
imsg send [options]
```

### Target Options (choose one method)
- `--to <handle>` — Phone number or email address (e.g., `+14155551212` or `user@example.com`)
- `--chat-id <id>` — Send to an existing chat by rowid
- `--chat-identifier <id>` — Send to chat identifier string (e.g., `iMessage;+;chat...`)
- `--chat-guid <guid>` — Send to chat by GUID

### Message Options
- `--text <message>` — Message body (plain text)
- `--file <path>` — Path to attachment file (e.g., `~/Desktop/photo.jpg`)
- `--service <type>` — Service: `imessage|sms|auto` (default: `auto`)
  - `auto` — Automatically choose iMessage if available, fallback to SMS
  - `imessage` — Force iMessage (may fail if recipient not on iMessage)
  - `sms` — Force SMS

### Other Options
- `--region <code>` — Default region for phone number normalization (e.g., `US`)
- `--json` or `-j` — Output result as JSON
- `--db <path>` — Custom path to chat.db
- `-v, --verbose` — Enable verbose logging
- `--log-level <level>` — Set log level

### Examples
```bash
# Send SMS to a phone number
imsg send --to +14155551212 --text "Hi there!"

# Send iMessage with attachment (auto-falls back to SMS if needed)
imsg send --to user@example.com --text "Check this out" --file ~/Desktop/photo.jpg --service auto

# Send to existing chat
imsg send --chat-id 1 --text "Hello from the terminal!"

# Send with JSON output (useful for scripting)
imsg send --to +14155551212 --text "Hi" --json
```

### Service Selection (`auto` Fallback)
When using `--service auto` (recommended):
- If the recipient is on iMessage, the message sends as iMessage (free, full features)
- If iMessage fails, it automatically falls back to SMS (costs may apply, carrier fees)
- This ensures reliable delivery across Apple and non-Apple devices

---

## rpc — JSON-RPC (Advanced)

For advanced use cases, `imsg` supports JSON-RPC over stdin/stdout. This allows programmatic interaction with the tool. See `imsg rpc --help` for details.

---

## General Options (All Commands)

- `--db <path>` — Override default chat.db location (defaults to `~/Library/Messages/chat.db`)
- `--log-level <level>` — Set verbosity: `trace|verbose|debug|info|warning|error|critical`
- `-v, --verbose` — Enable verbose output
- `--json` or `-j` — Output as JSON (available on most commands)

---

## Workflow Examples

### 1. Find a Conversation and Read Recent Messages
```bash
# List recent chats
imsg chats --limit 10

# Read last 20 messages from chat ID 3
imsg history --chat-id 3 --limit 20
```

### 2. Send a Message to Someone
```bash
# Send SMS or iMessage (auto-selects)
imsg send --to +14155551212 --text "Hello!"

# Or send to an existing chat
imsg chats --limit 5
imsg send --chat-id 2 --text "Hi there!"
```

### 3. Monitor a Conversation in Real-Time
```bash
# Watch for new messages in chat ID 1
imsg watch --chat-id 1 --debounce 500ms

# Watch with JSON output
imsg watch --chat-id 1 --json
```

### 4. Extract Messages for Backup or Analysis
```bash
# Get all messages from a chat as JSON
imsg history --chat-id 1 --json > backup.json

# Get messages from a date range
imsg history --chat-id 1 --start 2024-01-01T00:00:00Z --end 2024-12-31T23:59:59Z --json
```

---

## Tips & Troubleshooting

- **Messages.app Lock**: If you get database locked errors, close Messages.app first
- **Permissions**: On newer macOS (Ventura+), Terminal needs Full Disk Access to read the Messages database. Grant it in System Settings > Privacy & Security
- **Phone Number Formatting**: Use international format (e.g., `+14155551212` for US numbers)
- **JSON Output**: Most commands support `--json` for scripting and parsing
- **Debouncing**: When using `watch`, set `--debounce` to avoid spam from rapid file system events
- **Private Data**: Remember that message history is sensitive — be careful with backups and logs

