# Obsidian CLI Command Reference

Complete catalog of all `obsidian` CLI commands. Organized by category.

## Search & Discovery

| Command | Description | Key Options |
|---------|-------------|-------------|
| `search` | Search vault for text | `query=` (required), `path=`, `limit=`, `total`, `case`, `format=text\|json` |
| `search:context` | Search with matching line context | `query=` (required), `path=`, `limit=`, `case`, `format=text\|json` |
| `search:open` | Open search view in Obsidian UI | `query=` |
| `files` | List files in the vault | `folder=`, `ext=`, `total` |
| `folders` | List folders in the vault | `folder=`, `total` |
| `recents` | List recently opened files | `total` |
| `random` | Open a random note | `folder=`, `newtab` |
| `random:read` | Read a random note | `folder=` |

## Reading & File Info

| Command | Description | Key Options |
|---------|-------------|-------------|
| `read` | Read file contents | `file=`, `path=` |
| `file` | Show file metadata | `file=`, `path=` |
| `folder` | Show folder info | `path=` (required), `info=files\|folders\|size` |
| `outline` | Show headings for a file | `file=`, `path=`, `format=tree\|md\|json`, `total` |
| `wordcount` | Count words and characters | `file=`, `path=`, `words`, `characters` |

## Writing & Modifying Notes

| Command | Description | Key Options |
|---------|-------------|-------------|
| `create` | Create a new file | `name=`, `path=`, `content=`, `template=`, `overwrite`, `open`, `newtab` |
| `append` | Append content to a file | `file=`, `path=`, `content=` (required), `inline` |
| `prepend` | Prepend content to a file | `file=`, `path=`, `content=` (required), `inline` |
| `delete` | Delete a file | `file=`, `path=`, `permanent` |
| `move` | Move or rename a file | `file=`, `path=`, `to=` (required) |
| `rename` | Rename a file | `file=`, `path=`, `name=` (required) |

## Properties (Frontmatter)

| Command | Description | Key Options |
|---------|-------------|-------------|
| `properties` | List properties in vault or file | `file=`, `path=`, `name=`, `total`, `sort=count`, `counts`, `format=yaml\|json\|tsv`, `active` |
| `property:read` | Read a property value | `name=` (required), `file=`, `path=` |
| `property:set` | Set a property on a file | `name=` (required), `value=` (required), `type=text\|list\|number\|checkbox\|date\|datetime`, `file=`, `path=` |
| `property:remove` | Remove a property from a file | `name=` (required), `file=`, `path=` |

## Tags

| Command | Description | Key Options |
|---------|-------------|-------------|
| `tags` | List tags in vault or file | `file=`, `path=`, `total`, `counts`, `sort=count`, `format=json\|tsv\|csv`, `active` |
| `tag` | Get tag info | `name=` (required), `total`, `verbose` |

## Aliases

| Command | Description | Key Options |
|---------|-------------|-------------|
| `aliases` | List aliases in vault or file | `file=`, `path=`, `total`, `verbose`, `active` |

## Graph & Links

| Command | Description | Key Options |
|---------|-------------|-------------|
| `backlinks` | List backlinks to a file | `file=`, `path=`, `counts`, `total`, `format=json\|tsv\|csv` |
| `links` | List outgoing links from a file | `file=`, `path=`, `total` |
| `orphans` | List files with no incoming links | `total`, `all` |
| `deadends` | List files with no outgoing links | `total`, `all` |
| `unresolved` | List unresolved (broken) links | `total`, `counts`, `verbose`, `format=json\|tsv\|csv` |

## Tasks

| Command | Description | Key Options |
|---------|-------------|-------------|
| `tasks` | List tasks in vault | `file=`, `path=`, `total`, `done`, `todo`, `status="<char>"`, `verbose`, `format=json\|tsv\|csv`, `active`, `daily` |
| `task` | Show or update a single task | `ref=<path:line>`, `file=`, `path=`, `line=`, `toggle`, `done`, `todo`, `daily`, `status="<char>"` |

## Daily Notes

| Command | Description | Key Options |
|---------|-------------|-------------|
| `daily` | Open today's daily note | `paneType=tab\|split\|window` |
| `daily:read` | Read daily note contents | |
| `daily:append` | Append content to daily note | `content=` (required), `inline`, `open`, `paneType=` |
| `daily:prepend` | Prepend content to daily note | `content=` (required), `inline`, `open`, `paneType=` |
| `daily:path` | Get daily note file path | |

## Templates

| Command | Description | Key Options |
|---------|-------------|-------------|
| `templates` | List available templates | `total` |
| `template:read` | Read template content | `name=` (required), `resolve`, `title=` |
| `template:insert` | Insert template into active file | `name=` (required) |

## Bookmarks

| Command | Description | Key Options |
|---------|-------------|-------------|
| `bookmarks` | List bookmarks | `total`, `verbose`, `format=json\|tsv\|csv` |
| `bookmark` | Add a bookmark | `file=`, `subpath=`, `folder=`, `search=`, `url=`, `title=` |

## History & Versions

| Command | Description | Key Options |
|---------|-------------|-------------|
| `history` | List file history versions | `file=`, `path=` |
| `history:list` | List files with history | |
| `history:read` | Read a history version | `file=`, `path=`, `version=` (default: 1) |
| `history:restore` | Restore a history version | `file=`, `path=`, `version=` (required) |
| `history:open` | Open file recovery UI | `file=`, `path=` |
| `diff` | List or diff versions | `file=`, `path=`, `from=`, `to=`, `filter=local\|sync` |

## Bases (Obsidian Databases)

| Command | Description | Key Options |
|---------|-------------|-------------|
| `bases` | List all base files in vault | |
| `base:views` | List views in a base file | |
| `base:query` | Query a base and return results | `file=`, `path=`, `view=`, `format=json\|csv\|tsv\|md\|paths` |
| `base:create` | Create a new item in a base | `file=`, `path=`, `view=`, `name=`, `content=`, `open`, `newtab` |

## Plugins, Themes, Snippets

| Command | Description | Key Options |
|---------|-------------|-------------|
| `plugins` | List installed plugins | `filter=core\|community`, `versions`, `format=json\|tsv\|csv` |
| `plugins:enabled` | List enabled plugins | `filter=core\|community`, `versions`, `format=json\|tsv\|csv` |
| `plugin` | Get plugin info | `id=` (required) |
| `plugin:enable` | Enable a plugin | `id=` (required), `filter=core\|community` |
| `plugin:disable` | Disable a plugin | `id=` (required), `filter=core\|community` |
| `plugin:install` | Install a community plugin | `id=` (required), `enable` |
| `plugin:uninstall` | Uninstall a community plugin | `id=` (required) |
| `plugin:reload` | Reload a plugin | `id=` (required) |
| `plugins:restrict` | Toggle restricted mode | `on`, `off` |
| `themes` | List installed themes | `versions` |
| `theme` | Show active theme or get info | `name=` |
| `theme:set` | Set active theme | `name=` (required) |
| `theme:install` | Install a community theme | `name=` (required), `enable` |
| `theme:uninstall` | Uninstall a theme | `name=` (required) |
| `snippets` | List CSS snippets | |
| `snippets:enabled` | List enabled CSS snippets | |
| `snippet:enable` | Enable a CSS snippet | `name=` (required) |
| `snippet:disable` | Disable a CSS snippet | `name=` (required) |

## Vault & System

| Command | Description | Key Options |
|---------|-------------|-------------|
| `vault` | Show vault info | `info=name\|path\|files\|folders\|size` |
| `vaults` | List known vaults | `total`, `verbose` |
| `version` | Show Obsidian version | |
| `reload` | Reload the vault | |
| `restart` | Restart the app | |
| `hotkeys` | List hotkeys | `total`, `verbose`, `format=json\|tsv\|csv`, `all` |
| `hotkey` | Get hotkey for a command | `id=` (required), `verbose` |

## Navigation & UI

| Command | Description | Key Options |
|---------|-------------|-------------|
| `open` | Open a file in Obsidian | `file=`, `path=`, `newtab` |
| `daily` | Open daily note | `paneType=tab\|split\|window` |
| `tabs` | List open tabs | `ids` |
| `tab:open` | Open a new tab | `group=`, `file=`, `view=` |
| `workspace` | Show workspace tree | `ids` |
| `web` | Open URL in web viewer | `url=` (required), `newtab` |
| `command` | Execute any Obsidian command | `id=` (required) |
| `commands` | List available command IDs | `filter=` |

## Publish

| Command | Description | Key Options |
|---------|-------------|-------------|
| `publish:list` | List published files | `total` |
| `publish:add` | Publish a file | `file=`, `path=`, `changed` |
| `publish:remove` | Unpublish a file | `file=`, `path=` |
| `publish:open` | Open file on published site | `file=`, `path=` |
| `publish:site` | Show publish site info | |
| `publish:status` | List publish changes | `total`, `new`, `changed`, `deleted` |

## Developer Commands

| Command | Description | Key Options |
|---------|-------------|-------------|
| `eval` | Execute JavaScript | `code=` (required) |
| `dev:cdp` | Chrome DevTools Protocol command | `method=` (required), `params=` |
| `dev:dom` | Query DOM elements | `selector=` (required), `total`, `text`, `inner`, `all`, `attr=`, `css=` |
| `dev:css` | Inspect CSS | `selector=` (required), `prop=` |
| `dev:console` | Show console messages | `clear`, `limit=`, `level=` |
| `dev:errors` | Show captured errors | `clear` |
| `dev:screenshot` | Take a screenshot | `path=` |
| `dev:debug` | Attach/detach debugger | `on`, `off` |
| `dev:mobile` | Toggle mobile emulation | `on`, `off` |
| `devtools` | Toggle Electron dev tools | |
