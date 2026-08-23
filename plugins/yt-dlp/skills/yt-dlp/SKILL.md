---
name: yt-dlp
description: Download YouTube videos, thumbnails, and subtitles with yt-dlp, transcode anything not natively Apple TV-compatible to HEVC/AAC MP4, and optionally sync the result to a remote media server with a Jellyfin library refresh. Use this skill whenever the user wants to download a YouTube video, grab a video's thumbnail, or types "/ytdlp <url>". Works out of the box with no configuration (downloads land in a local folder); remote sync and Jellyfin integration are optional, per-machine settings.
allowed-tools: Bash, AskUserQuestion
---

# yt-dlp

Download YouTube videos/thumbnails/subtitles, fix up anything Apple TV can't play natively, and (optionally) ship the result to a media server.

## First-time setup

The script needs a stable working directory outside the plugin cache — `downloads/`, an optional `cookies.txt`, and an optional `.env` all live there and must survive plugin updates. Create one once:

```bash
mkdir -p ~/.claude/yt-dlp
```

If remote sync or Jellyfin integration is wanted, create `~/.claude/yt-dlp/.env` with any of these (all optional — omit a var entirely to disable that feature, there is no working default to fall back to):

```
# Remote media server to sync downloads to over rsync/SSH.
# Leave both unset to keep downloads local only.
YTDLP_REMOTE_HOST=user@remote-host.example.com
YTDLP_REMOTE_PATH=/path/on/remote/YouTube/

# Jellyfin library refresh, triggered after a successful sync.
JELLYFIN_URL=https://your-jellyfin-server
JELLYFIN_API_KEY=<your-api-key>
JELLYFIN_LIBRARY_ID=<optional-specific-library-id>
```

If this machine *is* the remote media server itself (its hostname matches the host portion of `YTDLP_REMOTE_HOST`), the script copies files locally instead of round-tripping over SSH.

### Requirements

- **`uv`** — runs the script with its dependencies fetched on the fly (`yt-dlp`, `click`, `requests`, `python-dotenv`); no project install step needed.
- **`deno`** — enables YouTube's JS challenge solver. Without it you'll see warnings and fewer available formats. `brew install deno` (macOS) or see https://deno.land.
- **`ffmpeg` / `ffprobe`** — required for the Apple TV compatibility conversion step. If absent, conversion is skipped with a warning (files still download and sync, just not re-encoded). `brew install ffmpeg`.
- **`rsync` + SSH key access to the remote host** — only needed if `YTDLP_REMOTE_HOST` is set.
- **`cookies.txt`** in `~/.claude/yt-dlp/` — optional, helps with age-restricted or private videos.

## Usage

```
/ytdlp <youtube-url>
/ytdlp --thumbnails-only <youtube-url>
/ytdlp --skip-sync <youtube-url>
/ytdlp --skip-convert <youtube-url>          # skip the Apple TV compatibility re-encode
/ytdlp --sw-encode <youtube-url>             # force CPU (libx265) encode instead of GPU
/ytdlp --thumbnails-only --skip-sync <youtube-url>
```

## How it works

1. Downloads the requested YouTube video (or thumbnail/subtitles only).
2. Converts any Apple TV-incompatible video (e.g. VP9/AV1 video, Opus audio, WebM) to HEVC/AAC MP4 before syncing — hardware-accelerated (`hevc_videotoolbox`) on Apple Silicon, falling back to software `libx265` elsewhere.
3. If `YTDLP_REMOTE_HOST`/`YTDLP_REMOTE_PATH` are set, syncs the result there via rsync (or a local copy if already on that host). If unset, files simply stay in `~/.claude/yt-dlp/downloads/`.
4. Triggers a Jellyfin library scan when the sync succeeds and `JELLYFIN_URL`/`JELLYFIN_API_KEY` are set.

## How to run

**Delegate the actual run to a background Haiku subagent** so the verbose yt-dlp/ffmpeg/rsync output never enters the main model's context. The script does all the work (download → convert → sync → Jellyfin scan); the subagent just runs it and reports a short summary back.

Use the `Agent` tool with:
- `subagent_type: general-purpose`
- `model: haiku`
- `run_in_background: true`

Give the subagent a prompt like (forwarding any user flags verbatim into the command):

```
Run this command and report back ONLY: the video title(s), whether each download
succeeded, whether any Apple TV conversion happened, and the final sync/Jellyfin
result. Do not paste raw ffmpeg/yt-dlp progress output.

cd ~/.claude/yt-dlp && uv run --with yt-dlp --with click --with requests --with python-dotenv \
  python3 "$CLAUDE_PLUGIN_ROOT/skills/yt-dlp/scripts/ytdlp.py" "<youtube-url>"
```

For example, if the user invoked `/ytdlp --thumbnails-only https://www.youtube.com/watch?v=aqz-KE-bpKQ`, the command inside the prompt becomes:

```bash
cd ~/.claude/yt-dlp && uv run --with yt-dlp --with click --with requests --with python-dotenv \
  python3 "$CLAUDE_PLUGIN_ROOT/skills/yt-dlp/scripts/ytdlp.py" --thumbnails-only "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
```

Relay the subagent's summary to the user when it completes. (If the user explicitly asks to watch live output, you can fall back to running the command directly in the foreground.)

## Outputs

- Downloaded files land in `~/.claude/yt-dlp/downloads/`.
- On successful sync, files are moved to `${YTDLP_REMOTE_HOST}:${YTDLP_REMOTE_PATH}` and removed locally.
- A Jellyfin library refresh is triggered if `JELLYFIN_URL` and `JELLYFIN_API_KEY` are set.

## When something fails

- **JS challenge warnings / fewer formats than expected:** ensure `deno` is installed and on `PATH`.
- **Conversion skipped / fails:** ensure `ffmpeg` and `ffprobe` are on `PATH`. HEVC output is tagged `hvc1` for Apple compatibility; a failed convert leaves the original file untouched and it still syncs. Use `--skip-convert` to bypass entirely.
- **Rsync / SSH fails:** verify the remote host in `YTDLP_REMOTE_HOST` is reachable (network/VPN/Tailscale as applicable) and that SSH key auth is set up — the script does not prompt for a password.
- **Sync silently does nothing:** `YTDLP_REMOTE_HOST` or `YTDLP_REMOTE_PATH` is unset — this is the no-remote-configured default, not an error. Check `~/.claude/yt-dlp/.env`.
- **Jellyfin scan fails:** check `~/.claude/yt-dlp/.env` for `JELLYFIN_URL` and `JELLYFIN_API_KEY`, and that the Jellyfin server is reachable from this machine.
