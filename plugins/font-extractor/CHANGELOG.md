# Changelog

## [1.0.1] — 2026-08-23

### Fixed
- `SKILL.md` referenced `organize_fonts.py` via
  `$CLAUDE_PLUGIN_ROOT/scripts/organize_fonts.py`, but the script
  actually lives at `skills/font-extractor/scripts/organize_fonts.py`
  — a real install would fail with "No such file". Fixed to
  `$CLAUDE_PLUGIN_ROOT/skills/font-extractor/scripts/organize_fonts.py`.

## [1.0.0] — 2026-06-09
Initial versioned release.
