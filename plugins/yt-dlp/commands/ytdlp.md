Download a YouTube video (or thumbnail/subtitles) via yt-dlp, using the `yt-dlp` skill's workflow. `$ARGUMENTS` holds the URL and any flags exactly as the user typed them, e.g. `--thumbnails-only https://youtube.com/watch?v=...`.

1. **Check first-time setup has been done:**
   ```bash
   test -d "$HOME/.claude/yt-dlp"
   ```
   If missing, create it (`mkdir -p ~/.claude/yt-dlp`) and tell the user remote sync / Jellyfin integration are optional — see the `yt-dlp` skill's "First-time setup" section if they want those wired up. Downloads work with zero configuration.

2. **Delegate the run to a background Haiku subagent** (per the skill's "How to run" section) so verbose yt-dlp/ffmpeg/rsync output never enters your context:
   - `subagent_type: general-purpose`
   - `model: haiku`
   - `run_in_background: true`
   - Prompt:
     ```
     Run this command and report back ONLY: the video title(s), whether each download
     succeeded, whether any Apple TV conversion happened, and the final sync/Jellyfin
     result. Do not paste raw ffmpeg/yt-dlp progress output.

     cd ~/.claude/yt-dlp && uv run --with yt-dlp --with click --with requests --with python-dotenv \
       python3 "$CLAUDE_PLUGIN_ROOT/skills/yt-dlp/scripts/ytdlp.py" $ARGUMENTS
     ```

3. Tell the user the download is running in the background and you'll report when it finishes — do not poll or block on it.

4. When the notification arrives, relay the subagent's summary. If the user explicitly asked to watch live output instead, run the command directly in the foreground rather than delegating.
