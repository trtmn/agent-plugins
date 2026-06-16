# Changelog

All notable changes to the `jellyfin` plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-06-16

### Added
- Initial release.
- `jellyfin` CLI wrapper (`scripts/jellyfin`) — a thin curl wrapper that injects the
  API key (`X-Emby-Token` header) and server URL from a single 1Password item via
  `op run`. Neither the secret nor the hostname is committed, echoed, or placed on argv.
- Shorthands: `scan`, `libraries`, `search`, `sessions`, `users`, `system-info`, `tasks`.
- Raw HTTP escape hatch: `get` / `post` / `put` / `delete <path> [body]` reaches any
  Jellyfin endpoint; JSON responses are pretty-printed with `jq`.
- SKILL.md documenting library/search, scan/refresh, sessions/playback, and users/system
  operation groups, plus installation steps.

### Notes
- The restish + OpenAPI-spec approach was abandoned during development: restish
  stack-overflows loading Jellyfin's official spec (deeply recursive schemas). The
  curl wrapper is the reliable, lightweight alternative.
