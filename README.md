# claude-plugins

A Claude Code plugin marketplace by [@trtmn](https://github.com/trtmn).

Each plugin bundles a **skill** (optionally with subagents, slash commands, and scripts) that extends Claude Code. Install individually — no all-or-nothing, pick what you want.

## Install

Add this repo as a plugin marketplace, then install plugins by name:

```
/plugin marketplace add trtmn/claude-plugins
/plugin install <plugin-name>@claude-plugins
```

## Plugins

| Plugin | Summary |
|---|---|
| `cowsay` | Generate ASCII cow art |
| `font-extractor` | Extract and download all fonts from a website |
| `home-assistant` | Control/query Home Assistant via REST API |
| `homebrew-dev` | Create and publish Homebrew formulas and casks |
| `imsg` | Terminal-based iMessage and SMS management |
| `learnings` | Autonomous background capture of corrections, errors, and learnings |
| `mastodon-cli` | Interact with Mastodon via the `toot` CLI |
| `obsidian-cli` | Vault operations via `obsidian-cli` — notes, daily notes, tasks, properties |
| `preflight-check` | Validate external service connections before starting work |
| `pushover` | Send push notifications via the Pushover API |
| `quack` | Rubber-duck debugging session |
| `recipe-fetch` | Fetch recipes from URLs and save as Obsidian markdown |
| `self-improvement` | User-triggered review/promote of captured learnings to CLAUDE.md |
| `skills-manager` | Manage Claude Code skills via `npx skills` CLI |
| `tailscale-policy-manager` | Manage Tailscale ACL policies + GitOps automation |
| `touch_file` | Recovery pattern when Write tool fails on new files |
| `unifi-api` | Query/control a UniFi network via the `unifi` CLI |
| `wp-custom-theme` | WordPress custom theme development |
| `youtube-data-api` | Query YouTube channels, videos, playlists via Data API v3 |

See each plugin's `SKILL.md` (or `skills/<name>/SKILL.md`) for triggers, usage, and required tools.

## Layout

Plugins live under `plugins/`; the marketplace manifest is at the repo root:

```
plugins/<plugin>/
├── .claude-plugin/plugin.json    # manifest — {name, description}
├── skills/<name>/
│   ├── SKILL.md                  # skill contract (YAML frontmatter + body)
│   ├── scripts/                  # optional executables
│   └── references/               # optional reference docs
├── agents/                       # optional subagent definitions (plugin root)
└── commands/                     # optional slash command definitions (plugin root)
```

`.claude-plugin/marketplace.json` at the repo root registers every plugin.

## Related

- Predecessor (older skills-only format): [trtmn/agent-skills](https://github.com/trtmn/agent-skills) — legacy, superseded by this repo
- Claude Code docs: [code.claude.com/docs](https://code.claude.com/docs)

## License

MIT — see [LICENSE](./LICENSE).
