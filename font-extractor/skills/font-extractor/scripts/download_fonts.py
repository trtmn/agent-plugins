#!/usr/bin/env python3
"""
Download fonts from a JSON map of { family: [url, ...] } into ./fonts/<family>/.
Usage:
    python download_fonts.py --fonts-json '{"Inter": ["https://..."]}' --output-dir ./fonts
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

CONTENT_TYPE_EXTENSIONS = {
    "font/woff2": ".woff2",
    "font/woff": ".woff",
    "font/ttf": ".ttf",
    "font/otf": ".otf",
    "application/font-woff2": ".woff2",
    "application/font-woff": ".woff",
    "application/x-font-woff": ".woff",
    "application/x-font-ttf": ".ttf",
    "application/x-font-otf": ".otf",
    "application/vnd.ms-fontobject": ".eot",
}


def sanitize_dirname(name: str) -> str:
    """Make a family name safe to use as a directory name."""
    # Strip characters invalid in directory names
    name = re.sub(r'[/\\:*?"<>|]', "", name)
    name = name.strip()
    return name or "Unknown"


def guess_extension(url: str, content_type: str) -> str:
    """Guess font file extension from URL or Content-Type."""
    # Try URL first
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.split("?")[0]
    ext = os.path.splitext(path)[1].lower()
    if ext in {".woff2", ".woff", ".ttf", ".otf", ".eot"}:
        return ext

    # Try Content-Type
    ct = content_type.lower().split(";")[0].strip()
    return CONTENT_TYPE_EXTENSIONS.get(ct, ".woff2")


def download_url(url: str, dest_path: Path, referer: str = "") -> int:
    """Download a URL to dest_path. Returns file size in bytes."""
    req = urllib.request.Request(url, headers=dict(HEADERS))
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=20) as resp:
        content_type = resp.headers.get("Content-Type", "")
        data = resp.read()

    # Fix extension if the dest_path has a generic or missing one
    if not dest_path.suffix or dest_path.suffix not in {".woff2", ".woff", ".ttf", ".otf", ".eot"}:
        ext = guess_extension(url, content_type)
        dest_path = dest_path.with_suffix(ext)

    dest_path.write_bytes(data)
    return len(data)


def main():
    parser = argparse.ArgumentParser(description="Download fonts organized by family")
    parser.add_argument("--fonts-json", required=True,
                        help='JSON string: {"Family Name": ["url1", "url2"], ...}')
    parser.add_argument("--output-dir", default="./fonts",
                        help="Root output directory (default: ./fonts)")
    parser.add_argument("--referer", default="",
                        help="Referer header to send with requests (helps with CDN 403s)")
    args = parser.parse_args()

    try:
        font_map: dict = json.loads(args.fonts_json)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    output_root = Path(args.output_dir)
    total_files = 0
    total_bytes = 0
    failed = []

    for family, urls in font_map.items():
        dir_name = sanitize_dirname(family)
        family_dir = output_root / dir_name
        family_dir.mkdir(parents=True, exist_ok=True)

        for url in urls:
            # Derive filename from URL
            parsed = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed.path.split("?")[0])
            if not filename:
                filename = f"font_{abs(hash(url)) % 100000}"

            dest = family_dir / filename

            try:
                size = download_url(url, dest, referer=args.referer)
                print(f"  ✓ {dir_name}/{dest.name}  ({size:,} bytes)")
                total_files += 1
                total_bytes += size
            except Exception as e:
                print(f"  ✗ {dir_name}/{filename}  FAILED: {e}", file=sys.stderr)
                failed.append((family, url, str(e)))

    print(f"\nDone: {total_files} file(s), {total_bytes / 1024:.1f} KB total")
    if failed:
        print(f"\n{len(failed)} download(s) failed:")
        for fam, url, err in failed:
            print(f"  [{fam}] {url}\n    → {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
