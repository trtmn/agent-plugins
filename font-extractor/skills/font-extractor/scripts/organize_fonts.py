#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["fonttools", "brotli"]
# ///
"""
Organize font files into subdirectories by font family name.

Reads each font file's internal name table to determine its family,
then moves it into ./fonts/<family>/.

Usage:
    uv run organize_fonts.py ./fonts
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

FONT_EXTENSIONS = {".woff2", ".woff", ".ttf", ".otf", ".eot"}


def sanitize_dirname(name: str) -> str:
    """Make a family name safe for use as a directory name."""
    # Keep only printable characters, then strip filesystem-unsafe ones
    name = "".join(c for c in name if c.isprintable())
    name = re.sub(r'[/\\:*?"<>|]', "", name)
    name = name.strip().strip(".")
    return name or "Unknown"


def _looks_like_family_name(name: str) -> bool:
    """Reject names that are clearly not font family names."""
    # Strip non-printable characters
    cleaned = "".join(c for c in name if c.isprintable())
    if not cleaned.strip():
        return False
    lower = cleaned.lower()
    # Copyright notices, license text, URLs
    if any(kw in lower for kw in ("copyright", "license", "licensed", "http", "©")):
        return False
    # Too long to be a family name (probably a description)
    if len(cleaned) > 80:
        return False
    return True


def _family_from_filename(filepath: Path) -> str:
    """Derive a family name from the filename as a last resort."""
    stem = filepath.stem
    # Strip content hashes (e.g., "Sohne.cb178166" → "Sohne")
    stem = re.sub(r'\.[a-f0-9]{6,}$', '', stem)
    # Strip weight/style suffixes
    stem = re.sub(r'[-_](Regular|Bold|Italic|Medium|Light|Thin|Black|Variable|VF|wght|wdth|ital).*$',
                  '', stem, flags=re.IGNORECASE)
    # Replace hyphens/underscores with spaces
    stem = re.sub(r'[-_]+', ' ', stem)
    return stem.strip() or "Unknown"


def get_font_family(filepath: Path) -> str | None:
    """Extract the font family name from a font file's name table.

    Tries multiple name IDs in priority order:
      16 (Typographic Family) → 1 (Font Family) → 4 (Full Name) → 6 (PostScript Name)
    Skips entries that look like copyright notices or license text.
    """
    try:
        font = TTFont(filepath, fontNumber=0)
        name_table = font["name"]

        # Build a lookup: nameID → first Unicode string found
        names: dict[int, str] = {}
        for record in name_table.names:
            if record.nameID not in names:
                try:
                    val = record.toUnicode().strip()
                    if val:
                        names[record.nameID] = val
                except Exception:
                    pass

        font.close()

        # Try IDs in priority order
        for name_id in (16, 1, 4, 6):
            candidate = names.get(name_id)
            if candidate and _looks_like_family_name(candidate):
                # Return only the printable portion
                cleaned = "".join(c for c in candidate if c.isprintable()).strip()
                if cleaned and cleaned != ".":
                    return cleaned

    except Exception:
        pass
    return None


def organize(fonts_dir: Path, dry_run: bool = False) -> None:
    """Move font files into family subdirectories."""
    # Collect all font files at the top level
    font_files = [
        f for f in fonts_dir.iterdir()
        if f.is_file() and f.suffix.lower() in FONT_EXTENSIONS
    ]

    if not font_files:
        print("No font files found at top level of", fonts_dir)
        return

    unknown_counter = 0
    moves: dict[str, list[str]] = {}

    for filepath in sorted(font_files):
        family = get_font_family(filepath)
        if not family:
            family = _family_from_filename(filepath)
        if not family or family == "Unknown":
            unknown_counter += 1
            family = f"Unknown-{unknown_counter}"

        dir_name = sanitize_dirname(family)
        dest_dir = fonts_dir / dir_name
        dest_path = dest_dir / filepath.name

        if not dry_run:
            dest_dir.mkdir(exist_ok=True)
            shutil.move(str(filepath), str(dest_path))

        moves.setdefault(dir_name, []).append(filepath.name)

    # Report
    total = sum(len(files) for files in moves.values())
    print(f"Organized {total} font(s) into {len(moves)} family folder(s):\n")
    for family in sorted(moves):
        files = moves[family]
        print(f"  {family}/")
        for f in sorted(files):
            print(f"    {f}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Organize fonts by family name")
    parser.add_argument("fonts_dir", type=Path,
                        help="Directory containing font files to organize")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without moving files")
    args = parser.parse_args()

    if not args.fonts_dir.is_dir():
        print(f"Error: {args.fonts_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    organize(args.fonts_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
