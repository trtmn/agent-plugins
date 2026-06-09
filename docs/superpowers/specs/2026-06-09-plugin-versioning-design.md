# Plugin Versioning Design

**Date:** 2026-06-09
**Status:** Approved

## Goals

- **Tracking** — every plugin has an explicit version that reflects its current state
- **Upgrade visibility** — a human-readable CHANGELOG per plugin shows what changed and when
- **Version pinning** — consumers can reference a specific version by reading `plugin.json`

## Versioning Scheme

SemVer (`MAJOR.MINOR.PATCH`):

| Bump | When |
|------|------|
| Patch | Bug fix, wording tweak, script fix — no behavior change a consumer would notice |
| Minor | New capability added, backward-compatible (new trigger phrases, new optional feature) |
| Major | Breaking change — renamed skill, removed behavior, changed required config |

## Per-Plugin Structure Changes

Each plugin gains two additions:

### 1. `plugin.json` — add `version` field

```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "description": "..."
}
```

### 2. `CHANGELOG.md` — new file at plugin root

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json          ← version field added here
├── CHANGELOG.md             ← new file
├── skills/
└── ...
```

CHANGELOG format (loose [Keep a Changelog](https://keepachangelog.com) conventions):

```markdown
# Changelog

## [1.0.0] — 2026-06-09
Initial versioned release.
```

Subsequent entries are prepended (newest first). No strict `Added/Changed/Fixed` sections required, but they're welcome for larger changes.

## Bump Ritual

A version bump requires exactly two edits:

1. Update `"version"` in `plugin.json`
2. Prepend a `## [x.y.z] — YYYY-MM-DD` entry in `CHANGELOG.md`

No scripts, no CI enforcement, no git tags.

## Initial State

All 21 existing plugins start at `1.0.0` with a single CHANGELOG entry:

```
## [1.0.0] — 2026-06-09
Initial versioned release.
```

## Out of Scope

- `marketplace.json` plugin entries do not get a version field — the platform reads version from `plugin.json` directly
- No tooling to diff installed-vs-available versions
- No git tags per plugin release
- No CI enforcement of version bumps

## Plugins Covered

cowsay, font-extractor, home-assistant, homebrew-dev, imsg, learnings, mastodon-cli, obsidian-cli, preflight-check, pushover, quack, recipe-fetch, self-improvement, side-quest, skills-manager, tailscale-policy-manager, touch_file, unifi-api, video-extract, wp-custom-theme, youtube-data-api
