# Changelog

## [1.0.0] — 2026-06-17

### Added
- `create` — spin up a new WordPress site with Docker Compose and WP-CLI
- `list` — show all sites in ~/wordpress-sites/ with running/stopped status
- `start` — bring a stopped site back online
- `stop` — pause a running site (data is preserved)
- `destroy` — permanently tear down a site (requires explicit confirmation)
- `wp-local-ops` Haiku agent for stateless operations (check-deps, list, start, stop)
