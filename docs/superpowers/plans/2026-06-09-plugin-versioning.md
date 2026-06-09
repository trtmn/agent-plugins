# Plugin Versioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `"version": "1.0.0"` to every plugin's `plugin.json` and create a `CHANGELOG.md` stub in every plugin directory.

**Architecture:** Two mechanical edits per plugin — insert a version field into the existing JSON manifest, and create a one-entry CHANGELOG at the plugin root. No new dependencies, no tooling, no automation. All 21 plugins start at `1.0.0`.

**Tech Stack:** `jq` (JSON editing), bash, git

---

### Task 1: Add `version` field to all `plugin.json` files

**Files:**
- Modify: `plugins/*/. claude-plugin/plugin.json` (21 files)

The `jq` command below rewrites each `plugin.json` in-place, inserting `"version": "1.0.0"` as the second field (after `name`, before `description`).

- [ ] **Step 1: Preview the transformation on one plugin**

```bash
jq '. | {name, version: "1.0.0"} + .' \
  plugins/cowsay/.claude-plugin/plugin.json
```

Expected output:
```json
{
  "name": "cowsay",
  "version": "1.0.0",
  "description": "Generates an ASCII cow saying custom text..."
}
```

- [ ] **Step 2: Apply to all 21 plugins**

```bash
for f in plugins/*/.claude-plugin/plugin.json; do
  tmp=$(mktemp)
  jq '. | {name, version: "1.0.0"} + .' "$f" > "$tmp" && mv "$tmp" "$f"
done
```

- [ ] **Step 3: Verify all 21 files now have a version field**

```bash
grep -r '"version"' plugins/*/.claude-plugin/plugin.json
```

Expected: 21 lines, each showing `"version": "1.0.0"`.

```bash
# Also verify no file lost its name or description
for f in plugins/*/.claude-plugin/plugin.json; do
  echo "=== $f ===" && jq '{name,version,description_length: (.description | length)}' "$f"
done
```

Expected: every entry has `name`, `version: "1.0.0"`, and a non-zero `description_length`.

---

### Task 2: Create `CHANGELOG.md` for all plugins

**Files:**
- Create: `plugins/<name>/CHANGELOG.md` (21 files)

- [ ] **Step 1: Generate all CHANGELOG stubs**

```bash
for plugin in \
  cowsay font-extractor home-assistant homebrew-dev imsg \
  learnings mastodon-cli obsidian-cli preflight-check pushover \
  quack recipe-fetch self-improvement side-quest skills-manager \
  tailscale-policy-manager touch_file unifi-api video-extract \
  wp-custom-theme youtube-data-api; do
  cat > "plugins/$plugin/CHANGELOG.md" <<'EOF'
# Changelog

## [1.0.0] — 2026-06-09
Initial versioned release.
EOF
done
```

- [ ] **Step 2: Verify all 21 CHANGELOG files exist and have correct content**

```bash
find plugins -name CHANGELOG.md | sort
```

Expected: 21 paths, one per plugin.

```bash
# Spot-check three plugins
for p in cowsay side-quest youtube-data-api; do
  echo "=== $p ===" && cat "plugins/$p/CHANGELOG.md"
done
```

Expected for each:
```
# Changelog

## [1.0.0] — 2026-06-09
Initial versioned release.
```

---

### Task 3: Commit

**Files:** All modified `plugin.json` files + all new `CHANGELOG.md` files

- [ ] **Step 1: Stage all changes**

```bash
git add plugins/*/. claude-plugin/plugin.json plugins/*/CHANGELOG.md
```

- [ ] **Step 2: Verify staged files**

```bash
git diff --cached --name-only | sort
```

Expected: 42 lines — 21 `plugin.json` paths and 21 `CHANGELOG.md` paths.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: add semver versioning to all plugins (v1.0.0)"
```

Expected: `[main <sha>] feat: add semver versioning to all plugins (v1.0.0)` with `42 files changed`.
