# Changelog

## [1.0.2] — 2026-08-23

### Fixed
- `wp-local-ops` and `SKILL.md` hardcoded script paths at
  `~/.claude/skills/wp-local/scripts/`, which is not where a
  marketplace-installed plugin's files actually live — a real install
  would 404 on every operation. Fixed to use
  `${CLAUDE_PLUGIN_ROOT}/skills/wp-local/scripts/`, resolved at runtime
  for whichever path the plugin is actually installed under. No deploy
  step needed: unlike side-quest/self-improvement, wp-local's scripts
  only ever run inside a live Bash tool call, never from a hook or
  daemon outside the session.

## [1.0.1] — 2026-06-17

### Changed
- `create` now skips auto-admin setup — WordPress standard browser install wizard instead
- WP-CLI is still installed in the container at create time for later use
- Fixed health check to verify HTTP status code rather than page content (was failing on 302 redirect before first setup)

## [1.0.0] — 2026-06-17

### Added
- `create` — spin up a new WordPress site with Docker Compose and WP-CLI
- `list` — show all sites in ~/wordpress-sites/ with running/stopped status
- `start` — bring a stopped site back online
- `stop` — pause a running site (data is preserved)
- `destroy` — permanently tear down a site (requires explicit confirmation)
- `wp-local-ops` Haiku agent for stateless operations (check-deps, list, start, stop)
