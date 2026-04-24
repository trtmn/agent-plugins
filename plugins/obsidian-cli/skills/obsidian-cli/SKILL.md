---
name: obsidian-cli
description: >
  Use this skill for ANY task involving Obsidian, vaults, notes, daily notes, backlinks, tags,
  properties, frontmatter, tasks/todos, templates, wikilinks, knowledge management, searching notes,
  note metadata, plugins, themes, CSS snippets, vault structure, orphan notes, graph analysis,
  bookmarks, aliases, bases (Obsidian databases), note history, word counts, outlines, publish,
  or any interaction with an Obsidian vault. Trigger when the user mentions Obsidian, their vault,
  their notes, or wants to find/read/create/modify notes programmatically.
allowed-tools:
  - Bash(obsidian *)
---

# Obsidian CLI Skill

The user has the `obsidian` CLI installed, which communicates with a running Obsidian instance over a local REST API. Use it to search, read, create, modify, and analyze notes without touching files directly on disk.

## When to Use CLI vs Direct File Access

| Use CLI | Use Direct Read/Edit | Use Both |
|---------|---------------------|----------|
| Search (`search`, `search:context`) | Large content edits requiring precise line-level changes | Find notes with CLI, then Read/Edit their files |
| Graph analysis (backlinks, orphans, deadends, unresolved) | Multi-line insertions at specific positions | Get vault path with `vault info=path`, then Glob/Grep |
| Properties/tags (read, set, list, count) | Complex regex replacements | List tasks with CLI, edit file to restructure |
| Tasks (list, toggle, filter) | Reading very large files with offset/limit | |
| Daily notes (read, append, prepend) | | |
| Templates (list, read, insert) | | |
| Vault-wide counts and statistics | | |
| Opening files in Obsidian UI | | |

**Key principle:** Use CLI for discovery and metadata; use direct file access for surgical edits. Combine them for find-then-edit workflows.

## CLI Syntax Conventions

```
obsidian <command> [key=value ...] [bare-flags]
```

- **`file=`** resolves by name like wikilinks (no extension needed): `file=Meeting Notes`
- **`path=`** is an exact vault-relative path: `path=Journal/2024-01-15.md`
- **Quote values with spaces:** `file="Project Planning"`, `content="Hello World"`
- **Newlines in content:** Use `\n` — e.g., `content="Line 1\nLine 2"`
- **Bare boolean flags** have no value: `total`, `verbose`, `counts`, `done`, `todo`
- **`vault=`** targets a specific vault: `vault="Work Vault"`
- **`format=json`** for structured/parseable output (prefer this for programmatic use)
- **Most commands default to the active file** when `file=`/`path=` is omitted

## Safe vs Destructive Operations

### Safe (no confirmation needed)
- All read commands: `read`, `search`, `search:context`, `file`, `files`, `folders`, `outline`, `wordcount`, `recents`
- All list commands: `tags`, `properties`, `tasks`, `backlinks`, `links`, `orphans`, `deadends`, `unresolved`, `aliases`, `bookmarks`, `templates`, `bases`, `plugins`, `themes`, `snippets`, `hotkeys`, `commands`, `tabs`, `workspace`
- Single-value reads: `tag`, `property:read`, `daily:read`, `daily:path`, `template:read`, `random:read`, `vault`, `vaults`, `version`, `history`, `history:list`, `history:read`, `diff`, `publish:list`, `publish:site`, `publish:status`, `base:query`, `base:views`
- UI navigation: `open`, `daily`, `search:open`, `tab:open`, `web`

### Mutating (use with normal judgment)
- Content modification: `append`, `prepend`, `create`, `daily:append`, `daily:prepend`
- Properties: `property:set`, `property:remove`
- Tasks: `task` with `toggle`/`done`/`todo`/`status=`
- Bookmarks: `bookmark`
- Templates: `template:insert`
- Bases: `base:create`

### Destructive (confirm with user first)
- `delete` — moves to trash (or permanent with `permanent` flag)
- `move`, `rename` — changes file location/name
- `history:restore` — overwrites current file with historical version
- `plugin:install`, `plugin:uninstall`, `plugin:enable`, `plugin:disable` — changes plugin state
- `theme:install`, `theme:uninstall`, `theme:set` — changes theme
- `snippet:enable`, `snippet:disable` — changes CSS snippets
- `plugins:restrict` — toggles restricted mode
- `publish:add`, `publish:remove` — affects published site
- `reload`, `restart` — disrupts the running app
- `command` — executes arbitrary Obsidian commands

## Core Command Patterns

### Search & Discovery

```bash
# Full-text search
obsidian search query="project planning" format=json

# Search with line context (shows matching lines)
obsidian search:context query="TODO" path=Projects limit=10

# Count matches
obsidian search query="meeting" total

# List all markdown files in a folder
obsidian files folder=Projects ext=md

# Recently opened files
obsidian recents
```

### Reading Notes

```bash
# Read by wikilink name
obsidian read file="Meeting Notes"

# Read by exact path
obsidian read path="Journal/2024-01-15.md"

# Get file metadata
obsidian file file="My Note"

# Show heading outline
obsidian outline file="My Note" format=json

# Word count
obsidian wordcount file="My Note"
```

### Writing & Modifying Notes

```bash
# Create a new note
obsidian create name="New Note" content="# New Note\n\nContent here"

# Create from template
obsidian create name="Meeting 2024-01-15" template="Meeting Template"

# Append to a note
obsidian append file="My Note" content="\n## New Section\n\nAdded content"

# Prepend to a note
obsidian prepend file="My Note" content="Important update at the top\n"
```

### Properties (Frontmatter)

```bash
# List all properties across the vault with counts
obsidian properties counts sort=count format=json

# Read a specific property from a file
obsidian property:read name=status file="My Project"

# Set a property
obsidian property:set name=status value=active file="My Project"

# Set a date property
obsidian property:set name=due value=2024-03-15 type=date file="My Task"

# Set a list property
obsidian property:set name=tags value="[work, urgent]" type=list file="My Note"

# Remove a property
obsidian property:remove name=draft file="Published Post"

# Show properties for a specific file
obsidian properties file="My Note" format=yaml
```

### Tags

```bash
# List all tags with counts, sorted by frequency
obsidian tags counts sort=count format=json

# Get info about a specific tag
obsidian tag name=project verbose

# Count how many times a tag is used
obsidian tag name=work total

# Tags for a specific file
obsidian tags file="My Note"
```

### Graph & Links

```bash
# Find what links TO a note (backlinks)
obsidian backlinks file="My Note" counts format=json

# Find what a note links TO (outgoing)
obsidian links file="My Note"

# Find orphan notes (nothing links to them)
obsidian orphans

# Count orphans
obsidian orphans total

# Find dead-end notes (they link to nothing)
obsidian deadends

# Find broken/unresolved links
obsidian unresolved counts verbose format=json
```

### Tasks

```bash
# List all incomplete tasks
obsidian tasks todo

# List completed tasks
obsidian tasks done

# Tasks in a specific file
obsidian tasks file="Project Plan" verbose

# Tasks from daily note
obsidian tasks daily todo

# Count incomplete tasks
obsidian tasks todo total

# Tasks as JSON for processing
obsidian tasks todo format=json

# Toggle a task (by file and line number)
obsidian task file="My Note" line=15 toggle

# Mark a task done
obsidian task file="My Note" line=15 done

# Mark a daily note task done
obsidian task daily line=5 done
```

### Daily Notes

```bash
# Read today's daily note
obsidian daily:read

# Get the daily note's file path
obsidian daily:path

# Append to today's daily note
obsidian daily:append content="\n- [ ] New task for today"

# Prepend to daily note
obsidian daily:prepend content="## Morning Update\n\nStarting the day with..."

# Open daily note in Obsidian
obsidian daily
```

### Templates

```bash
# List available templates
obsidian templates

# Read a template's content
obsidian template:read name="Meeting Template"

# Read with variables resolved
obsidian template:read name="Meeting Template" resolve title="Q1 Planning"

# Insert template into active file
obsidian template:insert name="Meeting Template"
```

### Bookmarks

```bash
# List all bookmarks
obsidian bookmarks format=json

# Bookmark a file
obsidian bookmark file="Important Note"

# Bookmark a heading within a file
obsidian bookmark file="Project Plan" subpath="## Timeline"

# Bookmark a search query
obsidian bookmark search="TODO urgent"
```

### History & Versions

```bash
# List history versions for a file
obsidian history file="My Note"

# List all files that have history
obsidian history:list

# Read a specific version
obsidian history:read file="My Note" version=2

# Diff two versions
obsidian diff file="My Note" from=1 to=3
```

### Bases (Obsidian Databases)

```bash
# List all base files
obsidian bases

# List views in a base
obsidian base:views file="Tasks DB"

# Query a base view
obsidian base:query file="Tasks DB" view="Active Tasks" format=json

# Create a new item in a base
obsidian base:create file="Tasks DB" name="New Task" content="Task description"
```

### Plugins, Themes, Snippets

```bash
# List community plugins with versions
obsidian plugins filter=community versions format=json

# Get info about a specific plugin
obsidian plugin id=dataview

# List enabled plugins
obsidian plugins:enabled

# List installed themes
obsidian themes versions

# Show active theme
obsidian theme

# List CSS snippets
obsidian snippets
```

### Vault Info

```bash
# Full vault info
obsidian vault

# Just the vault path
obsidian vault info=path

# Just vault name
obsidian vault info=name

# File and folder counts
obsidian vault info=files
obsidian vault info=folders

# List all known vaults
obsidian vaults verbose

# Obsidian version
obsidian version
```

### Opening Files in Obsidian UI

```bash
# Open a file
obsidian open file="My Note"

# Open in new tab
obsidian open file="My Note" newtab

# Open daily note
obsidian daily

# Open search with query
obsidian search:open query="project"

# Execute any Obsidian command
obsidian command id=graph:open
```

## Best Practices

1. **Use `format=json` for structured output** — easier to parse and process programmatically
2. **Use `total` for counts** — returns just a number instead of listing everything
3. **Batch appends** — combine multiple items into one `content=` with `\n` separators rather than making multiple CLI calls
4. **Check before mutating** — read the current state before setting properties or modifying content
5. **Get vault path dynamically** — use `obsidian vault info=path` rather than hardcoding paths, then combine with Read/Edit for file operations
6. **Use `file=` for convenience, `path=` for precision** — `file=` is shorter but may be ambiguous if multiple files share a name
7. **Use `verbose` for detailed output** — many list commands support `verbose` for extra context (file paths, counts, types)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Obsidian is not running" or connection refused | Obsidian desktop app must be open. Start it first. |
| "No active file" error | Some commands default to the active file. Specify `file=` or `path=` explicitly. |
| "File not found" | Check the name with `obsidian search query="partial name"` or `obsidian files`. Use `path=` for exact match. |
| Spaces in file/folder names | Always quote: `file="My Note"`, `path="My Folder/note.md"` |
| Multi-vault | Specify `vault="Vault Name"` to target a specific vault |
| Command returns nothing | The file may be empty, or the query had no matches. Use `total` to confirm zero results. |

## Full Command Reference

For the complete catalog of all 80+ commands with all options, read:
`references/command-reference.md` (relative to this skill's directory)
