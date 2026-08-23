import yt_dlp
import click
import subprocess
import os
import json
import requests
import socket
import shutil
import re
from dotenv import load_dotenv


# This will be populated after argument parsing
List_of_videos_to_download = []

LOCAL_DOWNLOADS = "downloads/"

# Load environment variables from a .env file in the current working
# directory (see SKILL.md for the one-time setup that creates this).
load_dotenv()

# Remote sync target, e.g. "user@host.example.com". Unset -> sync is skipped
# entirely and downloads stay local; there is intentionally no default here.
REMOTE_HOST = os.environ.get("YTDLP_REMOTE_HOST", "").strip() or None

# Remote destination dir. Required if REMOTE_HOST is set. A trailing slash is
# enforced so rsync/copy treat it as a directory.
REMOTE_PATH = os.environ.get("YTDLP_REMOTE_PATH", "").strip() or None
if REMOTE_PATH and not REMOTE_PATH.endswith("/"):
    REMOTE_PATH += "/"


def get_hostname():
    """Get the current machine's hostname."""
    return socket.gethostname()


def _remote_short_hostname():
    """
    Short hostname portion of REMOTE_HOST (strips 'user@' and any domain
    suffix), used to detect "we're already on the remote machine" so sync
    becomes a local copy instead of an SSH round-trip to ourselves.
    """
    if not REMOTE_HOST:
        return None
    host = REMOTE_HOST.split("@")[-1]
    return host.split(".")[0]


def escape_remote_path(path):
    """
    Backslash-escape characters the remote shell would treat specially.
    macOS ships openrsync (no --protect-args), so the remote path is parsed by
    the remote shell — spaces and '&' in album folders like "Singles & Specials"
    must be escaped or the path gets split/backgrounded.
    """
    return re.sub(r"([^A-Za-z0-9_./-])", r"\\\1", path)


def copy_file_local(local_file_path, dest_dir):
    """
    Copy a file to a local directory.
    Skips if file already exists (matching rsync --ignore-existing behavior).
    Returns True if successful, False otherwise.
    """
    try:
        # Ensure destination directory exists
        os.makedirs(dest_dir, exist_ok=True)

        # Get filename and destination path
        filename = os.path.basename(local_file_path)
        dest_path = os.path.join(dest_dir, filename)

        # Check if file already exists (ignore-existing behavior)
        if os.path.exists(dest_path):
            print(f"⏭ Skipping {filename} (already exists at destination)")
            # Still remove local file since it's already at destination
            try:
                os.remove(local_file_path)
                print(f"✓ Cleaned up local file: {filename}")
            except OSError as e:
                print(f"⚠ Warning: Could not remove local file {filename}: {e}")
            return True

        print(f"Copying {filename} to {dest_dir}...")

        # Copy file (shutil.copy2 preserves metadata)
        shutil.copy2(local_file_path, dest_path)

        print(f"✓ Successfully copied {filename}")

        # Remove local file after successful copy
        try:
            os.remove(local_file_path)
            print(f"✓ Cleaned up local file: {filename}")
        except OSError as e:
            print(f"⚠ Warning: Could not remove local file {filename}: {e}")

        return True

    except Exception as e:
        try:
            filename = os.path.basename(local_file_path)
        except UnicodeDecodeError:
            filename = "file with special characters"
        print(f"✗ Error copying {filename}: {str(e)}")
        return False


def rsync_file_to_remote(local_file_path):
    """
    Sync a single file to the remote machine using rsync, or copy locally if
    we're already on the remote machine. Returns True if successful, False
    otherwise. If no remote is configured (YTDLP_REMOTE_HOST/YTDLP_REMOTE_PATH
    unset), the file is left in place in downloads/ and this returns False
    without treating it as an error.
    """
    if not REMOTE_HOST or not REMOTE_PATH:
        return False

    # If we're already on the remote machine, just copy locally.
    hostname = get_hostname()
    if hostname == _remote_short_hostname():
        return copy_file_local(local_file_path, REMOTE_PATH)

    # Not on the remote machine, use SSH to copy to remote
    try:
        # Safely handle filename with special characters
        try:
            filename = os.path.basename(local_file_path)
            print(f"Syncing {filename} to remote machine...")
        except UnicodeDecodeError:
            # Fallback for problematic filenames
            filename = os.path.basename(
                local_file_path.encode("utf-8", errors="replace").decode("utf-8")
            )
            print(f"Syncing {filename} to remote machine...")

        # Build rsync command with progress and no overwrite options
        rsync_cmd = [
            "rsync",
            "-avh",  # archive mode, verbose, human-readable
            "--progress",  # show progress
            "--ignore-existing",  # don't overwrite existing files
            "--exclude=.DS_Store",  # exclude macOS system files
            local_file_path,
            f"{REMOTE_HOST}:{escape_remote_path(REMOTE_PATH)}",
        ]

        # Run rsync command with proper encoding handling
        result = subprocess.run(
            rsync_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode == 0:
            try:
                filename = os.path.basename(local_file_path)
            except UnicodeDecodeError:
                filename = "file with special characters"
            print(f"✓ Successfully synced {filename}")

            # Remove local file after successful sync
            try:
                os.remove(local_file_path)
                print(f"✓ Cleaned up local file: {filename}")
            except OSError as e:
                print(f"⚠ Warning: Could not remove local file {filename}: {e}")

            return True
        else:
            # Handle stderr with proper encoding
            error_msg = result.stderr if result.stderr else "Unknown error"
            try:
                filename = os.path.basename(local_file_path)
            except UnicodeDecodeError:
                filename = "file with special characters"
            print(f"✗ Failed to sync {filename}: {error_msg}")
            return False

    except Exception as e:
        # Safely handle filename in error message
        try:
            filename = os.path.basename(local_file_path)
        except UnicodeDecodeError:
            filename = "file with special characters"
        print(f"✗ Error syncing {filename}: {str(e)}")
        return False


def load_cookies():
    """
    Load cookies from a file if it exists.
    Returns the cookies string or None if no cookies file found.
    """
    cookie_file = "cookies.txt"
    if os.path.exists(cookie_file):
        try:
            with open(cookie_file, "r") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Could not load cookies from {cookie_file}: {e}")
    return None


def scan_jellyfin_library():
    """
    Trigger a library scan in Jellyfin after files are uploaded.
    Returns True if successful, False otherwise.
    """
    jellyfin_url = os.getenv("JELLYFIN_URL")
    jellyfin_api_key = os.getenv("JELLYFIN_API_KEY")
    jellyfin_library_id = os.getenv("JELLYFIN_LIBRARY_ID")  # Optional

    if not jellyfin_url or not jellyfin_api_key:
        print("⚠ Warning: Jellyfin configuration not found. Skipping library scan.")
        print(
            "  Set JELLYFIN_URL and JELLYFIN_API_KEY in .env file to enable library scanning."
        )
        return False

    try:
        # Build the API endpoint URL
        # Ensure URL doesn't end with a slash before adding the endpoint
        base_url = jellyfin_url.rstrip("/")
        endpoint = f"{base_url}/Library/Refresh"

        # Prepare headers
        headers = {"X-Emby-Token": jellyfin_api_key, "Content-Type": "application/json"}

        # Prepare request body (with optional LibraryId)
        data = {}
        if jellyfin_library_id:
            data["LibraryId"] = jellyfin_library_id

        print("Triggering Jellyfin library scan...")

        # Make POST request to trigger library scan
        response = requests.post(endpoint, headers=headers, json=data, timeout=30)

        if response.status_code == 204 or response.status_code == 200:
            print("✓ Successfully triggered Jellyfin library scan")
            return True
        else:
            print(
                f"✗ Failed to trigger Jellyfin library scan: HTTP {response.status_code}"
            )
            if response.text:
                print(f"  Response: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(
            f"✗ Connection Error: Could not connect to Jellyfin server at {jellyfin_url}"
        )
        print("  Please verify the server is accessible and the URL is correct")
        print("  (If using Tailscale, ensure you're connected to the VPN)")
        return False
    except requests.exceptions.Timeout:
        print("✗ Timeout Error: Jellyfin server did not respond within 30 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error connecting to Jellyfin API: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error triggering Jellyfin library scan: {str(e)}")
        return False


# Apple TV compatibility targets.
# Apple TV natively plays H.264 and HEVC video, AAC/AC3/E-AC3/MP3/ALAC audio,
# inside an MP4/M4V/MOV container. Anything else (VP9/AV1 video, Opus/Vorbis
# audio, WebM/MKV container) needs transcoding before it will play.
APPLETV_VIDEO_CODECS = {"h264", "hevc"}
APPLETV_AUDIO_CODECS = {"aac", "ac3", "eac3", "mp3", "alac"}
APPLETV_CONTAINER_EXTS = {".mp4", ".m4v", ".mov"}
# Files we should probe for compatibility (video containers only — skip subs/thumbs).
VIDEO_EXTENSIONS = {
    ".mp4",
    ".m4v",
    ".mov",
    ".mkv",
    ".webm",
    ".avi",
    ".flv",
    ".ts",
    ".wmv",
}


def probe_media(file_path):
    """
    Run ffprobe and return parsed JSON (format + streams), or None on failure.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                file_path,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0 or not result.stdout:
            return None
        return json.loads(result.stdout)
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        return None


def get_media_duration(file_path):
    """Return the media duration in seconds (float), or None if unknown."""
    info = probe_media(file_path)
    if not info:
        return None
    try:
        dur = float(info.get("format", {}).get("duration"))
        return dur if dur > 0 else None
    except (TypeError, ValueError):
        return None


def _format_hms(seconds):
    """Format a duration in seconds as M:SS (or H:MM:SS for long videos)."""
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def ffmpeg_has_encoder(name):
    """Return True if the local ffmpeg lists the named encoder."""
    try:
        out = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return name in (out.stdout or "")
    except Exception:
        return False


def is_appletv_compatible(file_path):
    """
    Return (compatible: bool, reason: str) for a video file.

    A file is considered Apple TV-incompatible if its container, video codec,
    or audio codec is outside the natively supported set. ffprobe failures are
    treated as compatible (don't transcode what we can't inspect).
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in APPLETV_CONTAINER_EXTS:
        return False, f"container '{ext or 'unknown'}' not Apple TV-native"

    info = probe_media(file_path)
    if info is None:
        # Can't inspect — assume OK rather than needlessly re-encoding.
        return True, "ffprobe unavailable/failed; skipping conversion"

    for stream in info.get("streams", []):
        codec_type = stream.get("codec_type")
        codec_name = (stream.get("codec_name") or "").lower()
        if codec_type == "video":
            # Ignore cover-art/thumbnail streams (mjpeg/png attached pics).
            if stream.get("disposition", {}).get("attached_pic"):
                continue
            if codec_name not in APPLETV_VIDEO_CODECS:
                return False, f"video codec '{codec_name}' unsupported"
        elif codec_type == "audio":
            if codec_name not in APPLETV_AUDIO_CODECS:
                return False, f"audio codec '{codec_name}' unsupported"

    return True, "already Apple TV-compatible"


def convert_to_appletv(file_path, use_gpu=True):
    """
    Re-encode an incompatible file to HEVC (H.265) video + AAC audio in an MP4
    container, then replace the original. Returns (success: bool, path: str)
    where path is the resulting file on disk.

    Uses the 'hvc1' tag so Apple players recognize the HEVC stream, and
    +faststart so the moov atom is at the front for streaming.
    """
    try:
        filename = os.path.basename(file_path)
    except UnicodeDecodeError:
        filename = "file with special characters"

    base, _ = os.path.splitext(file_path)
    # Temp output, then atomic-ish replace. Distinct name avoids clobbering the
    # source mid-encode if the source is already .mp4.
    tmp_path = base + ".appletv.mp4"
    final_path = base + ".mp4"

    enc_label = "GPU/VideoToolbox" if use_gpu else "CPU/libx265"
    print(f"Converting {filename} for Apple TV (HEVC/AAC MP4, {enc_label})...")
    duration = get_media_duration(file_path)  # for the progress percentage

    # HEVC video encoder: default to the Apple Silicon hardware encoder
    # (hevc_videotoolbox) for speed; fall back to software libx265 (better
    # compression) when use_gpu is False. Both tag the stream `hvc1` so Apple
    # players recognize the HEVC. VideoToolbox uses -q:v (constant quality,
    # higher=better); libx265 uses -crf.
    if use_gpu:
        video_args = ["-c:v", "hevc_videotoolbox", "-tag:v", "hvc1", "-q:v", "65"]
    else:
        video_args = [
            "-c:v",
            "libx265",
            "-tag:v",
            "hvc1",
            "-crf",
            "23",
            "-preset",
            "medium",
        ]

    # `-progress pipe:1` emits machine-readable key=value progress on stdout;
    # `-nostats -loglevel error` keeps stderr to real errors only. We stream
    # stdout to compute a live percentage/ETA, and send stderr to a log file
    # so a full pipe can't deadlock the encode.
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-nostats",
        "-loglevel",
        "error",
        "-progress",
        "pipe:1",
        "-i",
        file_path,
        "-map",
        "0:v?",
        "-map",
        "0:a?",  # all video + audio streams, if present
        *video_args,
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        tmp_path,
    ]

    err_log_path = tmp_path + ".ffmpeg.log"
    try:
        err_log = open(err_log_path, "w", encoding="utf-8", errors="replace")
    except OSError:
        err_log = subprocess.DEVNULL

    try:
        proc = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=err_log,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        if err_log not in (subprocess.DEVNULL, None):
            err_log.close()
        try:
            os.remove(err_log_path)
        except OSError:
            pass
        print("✗ ffmpeg not found; cannot convert. Leaving original file in place.")
        return False, file_path

    # Stream progress. ffmpeg emits blocks of key=value lines; `out_time_us`
    # is the encoded position in microseconds and `speed` is the realtime
    # multiplier (e.g. 1.5x), which together give a wall-clock ETA.
    last_pct = -1
    speed = 0.0
    try:
        for line in proc.stdout:
            line = line.strip()
            if line.startswith("speed="):
                raw = line.split("=", 1)[1].strip().rstrip("x")
                try:
                    speed = float(raw)
                except ValueError:
                    speed = 0.0
            elif line.startswith("out_time_us="):
                try:
                    secs = int(line.split("=", 1)[1]) / 1_000_000
                except ValueError:
                    continue
                if duration:
                    pct = min(100.0, secs / duration * 100)
                    if int(pct) != last_pct:
                        last_pct = int(pct)
                        eta = (duration - secs) / speed if speed > 0 else None
                        eta_str = f", ~{_format_hms(eta)} left" if eta else ""
                        print(
                            f"\r  {pct:5.1f}%  "
                            f"({_format_hms(secs)}/{_format_hms(duration)}"
                            f"{eta_str}, {speed or '?'}x)",
                            end="",
                            flush=True,
                        )
                else:
                    print(
                        f"\r  {_format_hms(secs)} encoded ({speed or '?'}x)",
                        end="",
                        flush=True,
                    )
            elif line == "progress=end":
                break
    finally:
        proc.wait()
        if last_pct >= 0 or duration is None:
            print()  # end the carriage-return progress line
        if err_log not in (subprocess.DEVNULL, None):
            err_log.close()

    if proc.returncode != 0 or not os.path.exists(tmp_path):
        tail = "unknown error"
        try:
            with open(err_log_path, "r", encoding="utf-8", errors="replace") as f:
                err_lines = [ln for ln in f.read().strip().splitlines() if ln]
                if err_lines:
                    tail = err_lines[-1]
        except OSError:
            pass
        print(f"✗ Conversion failed for {filename}: {tail}")
        # Clean up a partial temp file and the error log if present.
        for p in (tmp_path, err_log_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        return False, file_path

    # Success: drop the error log before replacing the original.
    try:
        os.remove(err_log_path)
    except OSError:
        pass

    # Success: replace the original with the converted file.
    try:
        if os.path.abspath(file_path) != os.path.abspath(final_path):
            os.remove(file_path)  # original had a different extension (e.g. .webm)
        os.replace(tmp_path, final_path)
        print(f"✓ Converted to Apple TV-compatible MP4: {os.path.basename(final_path)}")
        return True, final_path
    except OSError as e:
        print(f"⚠ Warning: converted file created but replace failed: {e}")
        return False, tmp_path


def convert_incompatible_files(use_gpu=True):
    """
    Scan the downloads folder for video files that aren't Apple TV-compatible
    and re-encode them in place. Runs after download/cleanup, before sync.

    use_gpu: prefer the Apple Silicon hardware HEVC encoder; falls back to
    libx265 automatically if hevc_videotoolbox isn't available.
    """
    if not os.path.exists(LOCAL_DOWNLOADS):
        return

    # Verify ffprobe is available once up front.
    if shutil.which("ffprobe") is None or shutil.which("ffmpeg") is None:
        print("⚠ ffmpeg/ffprobe not found; skipping Apple TV compatibility conversion.")
        return

    # Fall back to software libx265 if the hardware encoder isn't present
    # (e.g. not running on an Apple Silicon Mac).
    if use_gpu and not ffmpeg_has_encoder("hevc_videotoolbox"):
        print("⚠ hevc_videotoolbox not available; using libx265 (CPU) instead.")
        use_gpu = False

    converted = 0
    checked = 0
    for filename in sorted(os.listdir(LOCAL_DOWNLOADS)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in VIDEO_EXTENSIONS:
            continue
        file_path = os.path.join(LOCAL_DOWNLOADS, filename)
        if not os.path.isfile(file_path):
            continue

        checked += 1
        compatible, reason = is_appletv_compatible(file_path)
        if compatible:
            print(f"✓ {filename}: {reason}")
            continue

        print(f"⚠ {filename}: {reason} — converting")
        success, _ = convert_to_appletv(file_path, use_gpu=use_gpu)
        if success:
            converted += 1

    if checked:
        print(
            f"Apple TV check: {checked} video file(s) scanned, {converted} converted."
        )


def cleanup_part_files():
    """
    Rename .part subtitle files to .vtt if they appear to be complete.
    This handles cases where yt-dlp didn't properly finalize subtitle downloads.
    """
    if not os.path.exists(LOCAL_DOWNLOADS):
        return

    renamed_count = 0
    for filename in os.listdir(LOCAL_DOWNLOADS):
        if filename.endswith(".vtt.part"):
            part_path = os.path.join(LOCAL_DOWNLOADS, filename)
            # Remove .part extension to get the final .vtt filename
            vtt_filename = filename[:-5]  # Remove '.part' (5 characters)
            vtt_path = os.path.join(LOCAL_DOWNLOADS, vtt_filename)

            # Check if the file exists and has content
            if os.path.isfile(part_path) and os.path.getsize(part_path) > 0:
                try:
                    # Check if final .vtt file already exists
                    if os.path.exists(vtt_path):
                        # If both exist, keep the larger one
                        if os.path.getsize(part_path) > os.path.getsize(vtt_path):
                            os.remove(vtt_path)
                            os.rename(part_path, vtt_path)
                            renamed_count += 1
                            print(f"✓ Renamed {filename} to {vtt_filename}")
                        else:
                            os.remove(part_path)
                            print(
                                f"✓ Removed incomplete {filename} (final file exists)"
                            )
                    else:
                        os.rename(part_path, vtt_path)
                        renamed_count += 1
                        print(f"✓ Renamed {filename} to {vtt_filename}")
                except OSError as e:
                    print(f"⚠ Warning: Could not rename {filename}: {e}")

    if renamed_count > 0:
        print(f"Cleaned up {renamed_count} subtitle file(s)")


def sync_downloads_folder():
    """
    Sync all files in the downloads folder to the remote machine.
    Remove local files only after successful sync. If no remote is
    configured, files simply stay in downloads/.
    """
    if not os.path.exists(LOCAL_DOWNLOADS):
        print("Downloads folder doesn't exist, nothing to sync.")
        return

    if not REMOTE_HOST or not REMOTE_PATH:
        print(
            "No remote configured (YTDLP_REMOTE_HOST/YTDLP_REMOTE_PATH unset) — "
            f"leaving files in {LOCAL_DOWNLOADS}."
        )
        return

    # Get list of files in downloads folder (excluding system files)
    files_to_sync = []
    excluded_files = [
        ".DS_Store",
        "Thumbs.db",
        ".Spotlight-V100",
        ".Trashes",
    ]  # Common system files to exclude

    for filename in os.listdir(LOCAL_DOWNLOADS):
        # Skip system files
        if filename in excluded_files:
            print(f"Skipping system file: {filename}")
            continue

        file_path = os.path.join(LOCAL_DOWNLOADS, filename)
        if os.path.isfile(file_path):
            files_to_sync.append(file_path)

    if not files_to_sync:
        print("No files found in downloads folder to sync.")
        return

    print(f"Found {len(files_to_sync)} files to sync to remote machine...")

    successful_syncs = 0
    failed_syncs = 0

    for file_path in files_to_sync:
        if rsync_file_to_remote(file_path):
            successful_syncs += 1
        else:
            failed_syncs += 1

    print("\nSync Summary:")
    print(f"✓ Successfully synced and cleaned up: {successful_syncs} files")
    if failed_syncs > 0:
        print(f"✗ Failed to sync: {failed_syncs} files")
        print("Note: Failed files were not removed from local storage")

    # Trigger Jellyfin library scan if any files were successfully synced
    if successful_syncs > 0:
        scan_jellyfin_library()


@click.command()
@click.argument("urls", nargs=-1, required=False)
@click.option(
    "--thumbnails-only",
    is_flag=True,
    help="Download only thumbnails, skip video download",
)
@click.option(
    "--skip-sync", is_flag=True, help="Skip syncing to remote machine after download"
)
@click.option(
    "--skip-convert",
    is_flag=True,
    help="Skip Apple TV compatibility conversion of downloaded videos",
)
@click.option(
    "--sw-encode",
    is_flag=True,
    help="Use software libx265 for conversion instead of the GPU (VideoToolbox) encoder",
)
def main(urls, thumbnails_only, skip_sync, skip_convert, sw_encode):
    """
    Download YouTube videos, thumbnails, and subtitles.

    URLs can be provided as arguments or will be prompted if not provided.
    """
    # Get video URLs from command line, global list, or prompt
    global List_of_videos_to_download
    if urls:
        # URLs provided as command-line arguments
        List_of_videos_to_download = list(urls)
    elif len(List_of_videos_to_download) == 0:
        # No URLs provided, prompt user
        List_of_videos_to_download = [
            click.prompt("Please enter the URL of the video you want to download")
        ]

    # Load cookies if available
    cookies = load_cookies()

    # Configure yt-dlp options
    ydl_opts = {
        "outtmpl": "downloads/%(title)s [%(id)s].%(ext)s",  # Download to downloads folder
        "writeinfojson": False,  # Don't create info JSON files
        # Default OFF: a synced .webp/.jpg thumbnail gets indexed by Jellyfin as
        # a separate "photo" item, duplicating every video. Only --thumbnails-only
        # re-enables it (see below).
        "writethumbnail": False,
        "writeallthumbnails": False,  # Only download the best thumbnail
        "no_playlist": True,  # Download only the video, not the entire playlist
        "quiet": False,  # Show download progress
        "no_warnings": False,  # Show warnings
        "windowsfilenames": True,  # Replace colons and other shell-problematic chars in filenames
        # Add headers to bypass detection
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-us,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
            "Connection": "keep-alive",
        },
        # Enable remote JS challenge solver for YouTube (requires deno runtime)
        "remote_components": ["ejs:github"],
        # Additional options to help with 403 errors
        "extractor_retries": 3,
        "fragment_retries": 3,
        "retries": 3,
        "sleep_interval": 1,
        "max_sleep_interval": 5,
    }

    # Add cookies if available
    if cookies:
        ydl_opts["cookies"] = cookies
        print("Using cookies for authentication")

    # We'll download subtitles separately after video download to avoid subtitle errors blocking video download
    print(
        "Subtitle download enabled: All available languages (manual and auto-generated)"
    )

    # Configure format based on whether we're downloading thumbnails only
    if thumbnails_only:
        ydl_opts["skip_download"] = True  # Skip video download
        ydl_opts["writethumbnail"] = True  # Ensure thumbnail is downloaded
    else:
        # Max quality: take the highest-resolution streams available. YouTube only
        # publishes >1080p in VP9/AV1, so the old avc1-only filter capped us at 1080p.
        # We sort by resolution FIRST, then tie-break toward H.264/AAC so that when a
        # given resolution is available in avc1 (i.e. <=1080p) we grab it and skip the
        # Apple TV re-encode entirely; we only fall to VP9/AV1 when that's the only way
        # to a higher resolution (1440p/4K), and the conversion step re-encodes those
        # to HEVC. Merge into MP4 where muxable; yt-dlp falls back to MKV otherwise and
        # the convert step then remuxes/transcodes to MP4.
        ydl_opts["format"] = "bestvideo+bestaudio/best"
        ydl_opts["format_sort"] = ["res", "fps", "vcodec:h264", "acodec:aac", "ext:mp4"]
        ydl_opts["merge_output_format"] = "mp4"

    instance = yt_dlp.YoutubeDL(ydl_opts)

    # Download videos
    print("Starting video downloads...")
    print("Note: Subtitles will be downloaded as separate .vtt files")

    for i, url in enumerate(List_of_videos_to_download, 1):
        print(f"\nDownloading video {i}/{len(List_of_videos_to_download)}: {url}")
        try:
            # Extract info first to see what formats are available
            info = instance.extract_info(url, download=False)
            print(f"Video title: {info.get('title', 'Unknown')}")
            print(f"Available formats: {len(info.get('formats', []))}")

            # Download video first (without subtitles to avoid subtitle errors blocking video)
            instance.download(url)
            print(f"✓ Successfully downloaded video: {url}")

            # Now download subtitles separately
            print("Downloading subtitles...")
            subtitle_opts = ydl_opts.copy()
            subtitle_opts["skip_download"] = True  # Don't re-download video
            subtitle_opts["writesubtitles"] = True  # Download manual subtitles
            subtitle_opts["writeautomaticsub"] = (
                True  # Download auto-generated subtitles
            )
            subtitle_opts["subtitlesformat"] = "vtt"  # Use VTT format
            subtitle_opts["skip_unavailable_fragments"] = (
                True  # Continue if subtitle download fails
            )

            subtitle_instance = yt_dlp.YoutubeDL(subtitle_opts)
            try:
                subtitle_instance.download(url)
                print("✓ Successfully downloaded subtitles")
            except Exception as sub_e:
                print(
                    f"⚠ Warning: Subtitle download failed (video was downloaded successfully): {str(sub_e)}"
                )
                # Continue - video is already downloaded

        except yt_dlp.utils.DownloadError as e:
            print(f"✗ Download error for {url}: {str(e)}")
            print("This might be due to:")
            print("  - Video is private or restricted")
            print("  - Video is age-restricted")
            print("  - YouTube is blocking the request")
            print("  - No compatible format available")
            print("  - Try using cookies for authentication")
            continue
        except Exception as e:
            print(f"✗ Failed to download {url}: {str(e)}")
            print("This might be due to:")
            print("  - Video is private or restricted")
            print("  - Video is age-restricted")
            print("  - YouTube is blocking the request")
            print("  - Network connectivity issues")
            print("  - Try using cookies for authentication")
            continue

    print("\nDownloads completed.")

    # Clean up any .part subtitle files
    cleanup_part_files()

    # Convert any Apple TV-incompatible videos before syncing (unless skipped
    # or we only fetched thumbnails, in which case there's no video to convert)
    if not skip_convert and not thumbnails_only:
        print("Checking downloaded videos for Apple TV compatibility...")
        convert_incompatible_files(use_gpu=not sw_encode)
    elif skip_convert:
        print("Skipping Apple TV compatibility conversion (--skip-convert flag used)")

    # Sync downloaded files to remote machine (unless skipped)
    if not skip_sync:
        print("Starting sync to remote machine...")
        sync_downloads_folder()
    else:
        print("Skipping sync to remote machine (--skip-sync flag used)")

    print("\nAll operations completed!")


if __name__ == "__main__":
    main()
