---
name: jellyfin
description: Interact with a Jellyfin media server via its REST API using the `jellyfin` CLI (a curl wrapper with 1Password auth). Use this skill whenever the user wants to browse or search their Jellyfin library, trigger a library scan/refresh, inspect active playback sessions or remote-control playback, list users, or check server/system status. Trigger on phrases like "scan my Jellyfin library", "what's playing on Jellyfin", "search Jellyfin for X", "refresh Jellyfin", "list Jellyfin users", "Jellyfin server info", or any mention of Jellyfin.
allowed-tools:
  - Bash(jellyfin *:*)
---

# Jellyfin API Skill

Interact with a [Jellyfin](https://jellyfin.org/) media server through its REST API.
The `jellyfin` CLI is a thin curl wrapper that injects the API key and server URL
from 1Password, so neither the secret nor the (private) hostname is ever printed,
placed on argv, or committed to git.

> **Why curl, not restish?** Jellyfin's official OpenAPI spec has deeply recursive
> schemas that crash restish (stack overflow on load), so the spec-driven approach
> isn't viable. The REST endpoints are simple, so a curl wrapper is both reliable
> and lightweight. Full endpoint reference: <https://api.jellyfin.org/>.

## CLI — `jellyfin`

Installed at `~/.local/bin/jellyfin`. It resolves the API key (`credential`) and
server URL (`hostname`) from one 1Password item via `op run`, sends the key as the
`X-Emby-Token` header, and pretty-prints JSON responses with `jq`.

### Shorthands (most common)

```bash
jellyfin scan                  # trigger a full library scan/refresh (POST /Library/Refresh)
jellyfin libraries             # list libraries / virtual folders
jellyfin search "the matrix"   # search hints across the library
jellyfin search "dune" 5       # ...limited to 5 results
jellyfin sessions              # list active playback sessions
jellyfin users                 # list users
jellyfin system-info           # server system info
jellyfin tasks                 # list scheduled tasks
```

### Raw HTTP

Reach any endpoint in the [Jellyfin API](https://api.jellyfin.org/) directly. A
request body for `post`/`put` is the 3rd argument or piped on stdin.

```bash
jellyfin get  "/Items?searchTerm=blade+runner&limit=5&Recursive=true"
jellyfin get  "/Items/<itemId>"
jellyfin get  "/System/Info/Public"                      # unauthenticated server info
jellyfin post "/Sessions/<sessionId>/Playing/Pause"      # remote playback control
jellyfin post "/Sessions/<sessionId>/Message" '{"Text":"Dinner!","Header":"Note"}'
jellyfin post "/ScheduledTasks/Running/<taskId>"         # run a scheduled task
jellyfin delete "/Items/<itemId>"
```

Responses are pretty-printed JSON; pipe to `jq` to project fields:

```bash
jellyfin sessions | jq '.[] | select(.NowPlayingItem) | {user: .UserName, item: .NowPlayingItem.Name, client: .Client}'
jellyfin users    | jq '.[].Name'
```

## Operation groups

### Library & search
- `get "/Items?…"` — query/browse items (`searchTerm`, `includeItemTypes`, `parentId`, `limit`, `sortBy`, `Recursive=true`, …)
- `get "/Items/<itemId>"` — full details for one item
- `search "<term>" [limit]` — fast search hints (`GET /Search/Hints`)
- `libraries` — list libraries (`GET /Library/VirtualFolders`)

### Library scan / refresh
- `scan` — trigger a full scan of all libraries (`POST /Library/Refresh`). This is the
  same call the `yt-dlp` project uses after adding media. Returns `204 No Content`.

### Sessions & playback
- `sessions` — list active sessions (`GET /Sessions`)
- `post "/Sessions/<sessionId>/Playing/<command>"` — `Pause`, `Unpause`, `Stop`, `NextTrack`, `PreviousTrack`, `Seek`, …
- `post "/Sessions/<sessionId>/System/<command>"` — `GoHome`, `Mute`, `VolumeUp`, …
- `post "/Sessions/<sessionId>/Message"` — display a message on the client (JSON body: `{"Text":"…","Header":"…"}`)

### Users & system
- `users` — list users (`GET /Users`)
- `system-info` — full server/system info (`GET /System/Info`)
- `get "/System/Info/Public"` — minimal info available without auth
- `tasks` — list scheduled tasks (`GET /ScheduledTasks`)
- `post "/ScheduledTasks/Running/<taskId>"` — run a scheduled task
- `get "/Plugins"` — list installed plugins

## Authentication & configuration

A single 1Password item (category `API_CREDENTIAL`) holds both values:

- **`credential`** — the API key, sent as the `X-Emby-Token` header.
- **`hostname`** — the server URL (e.g. `https://jellyfin.example.com`; a bare host
  is assumed `https://`).

Both are injected at call time via `op run` and never touch stdout, argv, or disk.
Create an API key in the Jellyfin server UI under **Dashboard → API Keys**.

`JELLYFIN_URL` in the environment overrides the item's `hostname` field if set.

## Installation

**1. Install the wrapper:**
```bash
cp scripts/jellyfin ~/.local/bin/jellyfin
chmod +x ~/.local/bin/jellyfin
```

**2. Point it at your 1Password item** — edit the two `op://` references near the
bottom of `~/.local/bin/jellyfin` to your vault + item, e.g.:
```
JELLYFIN_API_KEY=op://<vault>/<jellyfin-item>/credential
JELLYFIN_URL=op://<vault>/<jellyfin-item>/hostname
```
Ensure the item's `credential` field holds a valid API key and `hostname` holds the
server URL.

**3. Verify:**
```bash
jellyfin get "/System/Info/Public"   # unauthenticated — confirms URL + connectivity
jellyfin system-info                 # authenticated — confirms the API key works
jellyfin libraries                   # list your libraries
```

## Response notes

- Most `/Items`-style endpoints return an envelope: `{ "Items": [...], "TotalRecordCount": N }`.
- `/Users`, `/Sessions`, and `/Library/VirtualFolders` return bare JSON arrays.
- `scan` and the `/Sessions/.../Playing|System|Message` endpoints return `204 No Content`
  (no body) on success.
- The wrapper uses `curl --fail-with-body`, so HTTP 4xx/5xx exit non-zero and print the
  server's error body to stderr.
