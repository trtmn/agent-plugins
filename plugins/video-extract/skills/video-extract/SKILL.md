---
name: video-extract
description: >
  Download videos from any website and optionally send them to a Jellyfin server.
  Supports YouTube, Vimeo, Twitter/X, TikTok, Instagram, Reddit, Twitch, and virtually
  any platform hosting video content. Downloads directly on the Jellyfin host over SSH
  (or locally to /tmp + SCP as fallback), triggers a library rescan, and cleans up any
  local file. Server details (SSH host/user, Jellyfin URL, API key, media base path)
  are read from a single 1Password item. Use this skill whenever the user wants to
  download, extract, rip, save, or grab a video from a URL — even if they don't say
  "extract" explicitly. Also trigger for "get this video", "save this clip",
  "download this for Jellyfin", or any URL that clearly points to a video.
allowed-tools:
  - Bash
  - Read
  - Write
  - Agent
---

# Video Extract

Extract and download videos from any URL using the video-extractor agent.

## Usage

```
/video-extract <URL>
```

## What it does

1. Launches the `video-extractor` agent with the provided URL
2. The agent downloads the video to `/tmp` in the best available quality
3. SCPs the file to the Jellyfin server (configured via 1Password)
4. Triggers a Jellyfin library rescan so the video appears immediately
5. Cleans up the local temp file

## Instructions

When this skill is invoked, delegate immediately to the `video-extractor` agent (subagent_type: "video-extractor") with `run_in_background: true`. Always run the agent in the background so the user can continue working while the download and transfer happen. Pass along the URL from the user's arguments and any additional context (e.g., which Jellyfin directory to use).

If no URL is provided in the arguments, immediately respond with: "Usage: `/video-extract <URL>`" and stop. Do not launch the agent without a URL.

Default behavior is to send the video to Jellyfin's YouTube directory. If the user specifies a different destination (Movies, TV Shows, etc.), pass that along to the agent.
