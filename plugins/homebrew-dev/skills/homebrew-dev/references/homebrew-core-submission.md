# Submitting to Homebrew Core / Cask

How to get a formula or cask into the official `homebrew/core` or `homebrew/cask` taps so users can install it without adding a custom tap.

---

## Is My Package Eligible?

Before opening a PR, verify your package meets Homebrew's acceptance criteria.

**For homebrew-core (formulas):**
- Open source with an OSI-approved license
- Stable, versioned releases (no rolling-release-only packages)
- Notable use — typically 75+ GitHub stars, or clear utility to a wide audience
- Does not duplicate a formula that already exists
- Builds from source (or pre-built binaries via `on_arm`/`on_intel` blocks)
- No proprietary dependencies; no phone-home or tracking in the build

**For homebrew-cask (casks):**
- Distributes a macOS `.app`, font, PKG, or similar binary artifact
- Hosted at a stable, versioned URL (or `version :latest` with `sha256 :no_check` for rolling apps)
- Must have a homepage
- Free or freemium apps are fine; paid apps are fine if there is a free trial or free tier

Full criteria: https://docs.brew.sh/Acceptable-Formulae and https://docs.brew.sh/Acceptable-Casks

---

## Fork and Branch

```bash
# Fork the repo (one-time setup)
gh repo fork Homebrew/homebrew-core --clone
# or for casks:
gh repo fork Homebrew/homebrew-cask --clone

# Create a branch named after your package
cd homebrew-core
git checkout -b add-mytool
```

Branch naming convention:
- New package: `add-mytool`
- Version bump: `mytool-1.1` or use `brew bump-formula-pr` (handles this automatically)

---

## Write and Place the Formula / Cask

**homebrew-core formulas** go in `Formula/<first-letter>/mytool.rb`:
```bash
# Example: mytool → Formula/m/mytool.rb
cp ~/path/to/mytool.rb Formula/m/mytool.rb
```

**homebrew-cask casks** go in `Casks/<first-letter>/myapp.rb`:
```bash
# Example: myapp → Casks/m/myapp.rb
cp ~/path/to/myapp.rb Casks/m/myapp.rb
```

---

## Stricter Checks Required

homebrew-core applies stricter audits than personal taps. Run all of these before opening the PR:

```bash
# For formulas
brew install --build-from-source Formula/m/mytool.rb
brew audit --new --strict --online mytool
brew test mytool
brew style Formula/m/mytool.rb

# For casks
brew install --cask Casks/m/myapp.rb
brew audit --new --strict --online --cask myapp
brew test --cask myapp
brew style --cask Casks/m/myapp.rb
```

`--new` enables checks only applied to new (not yet merged) packages — desc format, homepage, license, test block presence.
`--strict` enables RuboCop and stricter formula checks.
`--online` fetches the URL and verifies the sha256 live.

---

## Commit Message Format

Homebrew has a specific commit message convention:

```
mytool 1.0 (new formula)
```

For casks:
```
myapp 1.0 (new cask)
```

For version bumps (if doing manually instead of `brew bump-formula-pr`):
```
mytool 1.1
```

One commit per formula/cask. Do not bundle multiple packages in one PR.

---

## Open the Pull Request

```bash
git add Formula/m/mytool.rb
git commit -m "mytool 1.0 (new formula)"
git push origin add-mytool
gh pr create --repo Homebrew/homebrew-core \
  --title "mytool 1.0 (new formula)" \
  --body "..."
```

**What reviewers check:**
- `desc` is concise, imperative, doesn't start with "A"/"The", no trailing period
- `homepage` is the project's actual website (not GitHub), uses HTTPS
- `license` matches what's in the repo
- `url` is a stable release tarball (not a git archive or `main` branch zip)
- `sha256` is correct
- `test do` block actually exercises the binary
- No unnecessary build dependencies
- Formula installs without errors on both arm64 and x86_64

**Common rejection reasons:**
- No `test do` block, or test only runs `--help` with no assertions
- `desc` violations (starts with article, ends with period, too long)
- Package is too niche or has very few users
- `url` points to a GitHub archive (`/archive/`) instead of a release asset
- Missing or incorrect `license`
- Does not build cleanly (flaky network fetch, missing dependency)

---

## For homebrew-cask

The process mirrors homebrew-core but targets `Homebrew/homebrew-cask`:

```bash
gh repo fork Homebrew/homebrew-cask --clone
cd homebrew-cask
git checkout -b add-myapp

# Place cask
cp ~/path/to/myapp.rb Casks/m/myapp.rb

# Verify
brew install --cask Casks/m/myapp.rb
brew audit --new --strict --online --cask myapp

# Commit and PR
git add Casks/m/myapp.rb
git commit -m "myapp 1.0 (new cask)"
git push origin add-myapp
gh pr create --repo Homebrew/homebrew-cask --title "myapp 1.0 (new cask)"
```

Additional cask-specific checks:
- `zap` stanza should list known preference files and app support directories
- `uninstall` stanza required if using `pkg`
- For apps with built-in auto-updaters: add `auto_updates true`

---

## After Merge

Once your PR is merged:

```bash
brew update
brew install mytool           # available to everyone without a tap
brew install --cask myapp
```

Your personal tap formula/cask can be left in place — installing from the official tap will take precedence once it's merged. You can eventually remove it from your tap to avoid version conflicts.
