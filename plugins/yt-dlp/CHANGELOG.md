# Changelog

All notable changes to the `yt-dlp` plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-08-23

### Added
- Initial plugin release, ported from a personal `~/.claude/skills/yt-dlp` skill.
- `ytdlp.py` — download (video/thumbnails/subtitles), Apple TV compatibility
  conversion (HEVC/AAC MP4 via `ffmpeg`, hardware-accelerated on Apple
  Silicon with a software fallback), optional rsync/SSH sync to a remote
  media server, and an optional Jellyfin library-refresh trigger.
- `/ytdlp` slash command, delegating the actual run to a background Haiku
  subagent so verbose yt-dlp/ffmpeg/rsync output never enters the main
  model's context.
- All personal infrastructure (remote host, remote path, local-machine
  detection) is now driven entirely by environment variables with no
  hardcoded defaults — the original personal skill hardcoded a specific
  Tailscale hostname, SSH username, and remote filesystem path.
