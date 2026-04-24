# homebrew skill

Packages macOS apps, fonts, CLI tools, and arbitrary files using Homebrew formulas and casks. Handles the full workflow: scaffolding, checksum computation, writing the formula/cask, setting up a personal tap, testing, and auditing.

## What it does

- **Formulas** — builds or installs CLI tools and libraries (source builds via Autoconf/CMake/Cargo/Go, or pre-built binaries)
- **Casks** — distributes macOS `.app` bundles, fonts, PKG installers, and arbitrary files
- **Taps** — sets up a personal GitHub tap (`homebrew-<name>`) for distributing your own packages

## Trigger phrases

The skill activates when you mention things like:

- "create a Homebrew formula for…"
- "package my macOS app with Homebrew"
- "distribute fonts with brew"
- "set up a personal tap"
- "brew cask for…"
- "package a CLI tool with Homebrew"
- "publish with homebrew"

## Usage

```
/homebrew
```

Then describe what you want to package. For example:

> Package my CLI tool `mytool` — the binary is at `https://example.com/mytool-1.0-macos.tar.gz`

> Create a cask for my macOS app `MyApp.dmg` and set up a personal tap on GitHub

> Package the JetBrains Mono font as a Homebrew cask

## Auto-approved tools

| Tool | Why |
|------|-----|
| `brew` | Scaffold, fetch, test, audit, install formulas/casks |
| `shasum` | Compute SHA-256 checksums for downloads |
| `git` | Initialize and push personal tap repositories |

## References

- [`references/formula-cookbook.md`](references/formula-cookbook.md) — annotated formula patterns (Autoconf, CMake, Cargo, Go, pre-built binaries, services, patching)
- [`references/cask-cookbook.md`](references/cask-cookbook.md) — annotated cask patterns (DMG apps, fonts, arbitrary files, PKG installers, architecture conditionals)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Homebrew Cask Cookbook](https://docs.brew.sh/Cask-Cookbook)
