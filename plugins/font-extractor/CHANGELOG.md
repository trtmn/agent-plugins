# Changelog

## [1.0.2] — 2026-08-23

### Removed
- `download_fonts.py` — dead code, never called by `SKILL.md`. The
  actual workflow downloads flat via `curl` (Step 1) then organizes by
  reading each font's internal name table (`organize_fonts.py`, Step
  2); this script duplicated that job via a different, unused
  family→URL-mapping approach.

## [1.0.1] — 2026-08-23

### Fixed
- `SKILL.md` referenced `organize_fonts.py` via
  `$CLAUDE_PLUGIN_ROOT/scripts/organize_fonts.py`, but the script
  actually lives at `skills/font-extractor/scripts/organize_fonts.py`
  — a real install would fail with "No such file". Fixed to
  `$CLAUDE_PLUGIN_ROOT/skills/font-extractor/scripts/organize_fonts.py`.

## [1.0.0] — 2026-06-09
Initial versioned release.
