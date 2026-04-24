# Cask Cookbook

Complete, annotated cask patterns for distributing macOS apps, fonts, CLIs, and arbitrary files.

---

## DMG with .app Artifact

The most common macOS app packaging pattern.

```ruby
cask "rectangle" do
  version "0.80"
  sha256 "abc123..."

  # #{version} interpolation keeps url and sha in sync
  url "https://github.com/rxhanson/Rectangle/releases/download/v#{version}/Rectangle#{version}.dmg"
  name "Rectangle"                    # human-readable display name
  desc "Move and resize windows using keyboard shortcuts or snap areas"
  homepage "https://rectangleapp.com"

  # Will be installed to /Applications/Rectangle.app
  app "Rectangle.app"

  # zap removes all traces when the user runs `brew uninstall --zap`
  zap trash: [
    "~/Library/Application Support/Rectangle",
    "~/Library/Preferences/com.knollsoft.Rectangle.plist",
    "~/Library/Saved Application State/com.knollsoft.Rectangle.savedState",
  ]
end
```

---

## ZIP with Font Artifacts

Fonts go to `~/Library/Fonts/`. Name the cask with a `font-` prefix.

```ruby
cask "font-jetbrains-mono" do
  version "2.304"
  sha256 "abc123..."

  url "https://github.com/JetBrains/JetBrainsMono/releases/download/v#{version}/JetBrainsMono-#{version}.zip"
  name "JetBrains Mono"
  desc "Typeface made for developers"
  homepage "https://www.jetbrains.com/lp/mono/"

  # Each font variant is a separate stanza
  font "fonts/ttf/JetBrainsMono-Regular.ttf"
  font "fonts/ttf/JetBrainsMono-Bold.ttf"
  font "fonts/ttf/JetBrainsMono-Italic.ttf"
  font "fonts/ttf/JetBrainsMono-BoldItalic.ttf"

  # Variable fonts in a subfolder
  font "fonts/variable/JetBrainsMonoNL[wght].ttf"
end
```

---

## ZIP with Arbitrary artifact + Custom target

Use `artifact` for files that need to land somewhere specific (completions, configs, etc.).

```ruby
cask "mycli" do
  version "1.2.0"
  sha256 "abc123..."

  url "https://example.com/mycli-#{version}-macos.zip"
  name "MyCLI"
  desc "Example CLI distributed as a cask"
  homepage "https://example.com/mycli"

  # Binary goes to $(brew --prefix)/bin/
  binary "mycli"

  # Shell completions placed at the expected paths
  artifact "completions/mycli.bash",
           target: "#{HOMEBREW_PREFIX}/share/bash-completion/completions/mycli"
  artifact "completions/_mycli",
           target: "#{HOMEBREW_PREFIX}/share/zsh/site-functions/_mycli"
  artifact "completions/mycli.fish",
           target: "#{HOMEBREW_PREFIX}/share/fish/vendor_completions.d/mycli.fish"

  # Man page
  artifact "man/mycli.1",
           target: "#{HOMEBREW_PREFIX}/share/man/man1/mycli.1"
end
```

---

## PKG Installer with uninstall + zap

PKGs require an `uninstall` stanza so `brew uninstall` can cleanly remove them.

```ruby
cask "virtualbox" do
  version "7.0.14,161095"

  # Version with a comma — first part is display version, second is build
  url "https://download.virtualbox.org/virtualbox/#{version.before_comma}/VirtualBox-#{version.before_comma}-#{version.after_comma}-OSX.dmg"
  sha256 "abc123..."
  name "VirtualBox"
  desc "Virtualizer for x86 hardware"
  homepage "https://www.virtualbox.org/"

  pkg "VirtualBox.pkg"

  # pkgutil identifier(s) from: pkgutil --pkgs | grep virtualbox
  uninstall pkgutil: [
    "org.virtualbox.pkg.vboxkexts",
    "org.virtualbox.pkg.virtualbox",
    "org.virtualbox.pkg.vboxstartupdaemon",
  ],
            script: {
              executable: "/Library/Application Support/VirtualBox/uninstall.sh",
              sudo: true,
            }

  zap trash: [
    "~/Library/Preferences/org.virtualbox.app.VirtualBox.plist",
    "~/Library/Saved Application State/org.virtualbox.app.VirtualBox.savedState",
    "~/Library/VirtualBox",
  ],
      rmdir: "/Library/Application Support/VirtualBox"
end
```

### Finding the pkgutil identifier
```bash
# After manually installing the PKG:
pkgutil --pkgs | grep -i myapp
# Then verify what it installed:
pkgutil --files com.example.myapp
```

---

## Architecture-Conditional Cask (Universal vs native)

Use when the vendor distributes separate ARM and Intel builds.

```ruby
cask "myapp" do
  version "3.1.0"

  on_arm do
    url "https://example.com/MyApp-#{version}-apple-silicon.dmg"
    sha256 "arm64_sha256_here..."
  end

  on_intel do
    url "https://example.com/MyApp-#{version}-intel.dmg"
    sha256 "intel_sha256_here..."
  end

  name "MyApp"
  desc "Cross-platform productivity app"
  homepage "https://example.com/myapp"

  app "MyApp.app"

  zap trash: "~/Library/Application Support/MyApp"
end
```

---

## Rolling Release (version :latest)

Use only when the vendor does not publish versioned releases. Prefer stable versions when available.

```ruby
cask "cursor" do
  version :latest
  sha256 :no_check    # can't verify a :latest download

  url "https://download.cursor.sh/mac/installer/universal/dmg"
  name "Cursor"
  desc "AI-powered code editor"
  homepage "https://cursor.sh"

  # auto_updates tells brew not to prompt for upgrades (app self-updates)
  auto_updates true

  app "Cursor.app"

  zap trash: [
    "~/Library/Application Support/Cursor",
    "~/Library/Preferences/com.todesktop.230313mzl4w4u92.plist",
  ]
end
```

---

## Auto-updating App (stable version)

For apps with built-in updaters that are distributed as stable versioned releases:

```ruby
cask "1password" do
  version "8.10.28,80100028"
  sha256 "abc123..."

  url "https://downloads.1password.com/mac/1Password-#{version.before_comma}-universal.zip"
  name "1Password"
  desc "Password manager that keeps all passwords secure behind one password"
  homepage "https://1password.com/"

  # The app updates itself — don't nag users to `brew upgrade`
  auto_updates true

  app "1Password.app"
  # Also installs a CLI companion
  binary "#{appdir}/1Password.app/Contents/MacOS/op", target: "#{HOMEBREW_PREFIX}/bin/op"

  zap trash: [
    "~/Library/Application Support/1Password",
    "~/Library/Group Containers/2BUA8C4S2C.com.1password",
    "~/Library/Preferences/com.1password.1password.plist",
  ]
end
```

---

## Caveats Block

Show instructions to the user after install (use sparingly — only for non-obvious post-install steps).

```ruby
cask "java" do
  version "21.0.2,13"
  sha256 "abc123..."

  url "https://download.java.net/java/GA/jdk#{version.before_comma}/..."
  name "OpenJDK"
  desc "Development kit for the Java programming language"
  homepage "https://openjdk.java.net/"

  pkg "OpenJDK #{version.before_comma}.pkg"
  uninstall pkgutil: "net.java.openjdk.#{version.before_comma}"

  # Shown after install — explain required manual steps
  caveats <<~EOS
    For the system Java wrappers to find this JDK, symlink it with:
      sudo ln -sfn #{opt_prefix}/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-#{version.major}.jdk
  EOS
end
```

---

## postflight Hook

Run arbitrary Ruby code after the cask is installed (use only when necessary):

```ruby
cask "myapp" do
  version "1.0"
  sha256 "abc123..."

  url "https://example.com/MyApp-#{version}.dmg"
  name "MyApp"
  desc "Requires post-install setup"
  homepage "https://example.com/myapp"

  app "MyApp.app"

  # Runs after the app is installed; runs as the current user
  postflight do
    system_command "/usr/bin/defaults",
                   args: ["write", "com.example.myapp", "firstRun", "-bool", "NO"]
  end
end
```

---

## Suite (Multiple Apps from One Archive)

```ruby
cask "libreoffice" do
  version "7.6.4"
  sha256 "abc123..."

  url "https://download.documentfoundation.org/libreoffice/stable/#{version}/mac/x86_64/LibreOffice_#{version}_MacOS_x86-64.dmg"
  name "LibreOffice"
  desc "Free and open-source office suite"
  homepage "https://www.libreoffice.org/"

  # suite installs everything inside the folder
  suite "LibreOffice.app"

  # Or list individual apps:
  # app "LibreOffice.app"
  # app "LibreOffice Impress.app"
end
```

---

## Common zap Patterns

```ruby
zap trash: [
  # User preferences
  "~/Library/Preferences/com.example.myapp.plist",
  # Application support files
  "~/Library/Application Support/MyApp",
  # Caches
  "~/Library/Caches/com.example.myapp",
  # Logs
  "~/Library/Logs/MyApp",
  # Saved state
  "~/Library/Saved Application State/com.example.myapp.savedState",
  # Login items (newer macOS)
  "~/Library/Application Support/com.apple.backgroundtaskmanagementagent/backgrounditems.btm",
  # Containers (sandboxed apps)
  "~/Library/Containers/com.example.myapp",
  # Group containers
  "~/Library/Group Containers/group.com.example.myapp",
]
```

---

## Version String Tricks

```ruby
version "1.2.3,45"

version.major         # => "1"
version.minor         # => "2"
version.patch         # => "3"
version.before_comma  # => "1.2.3"
version.after_comma   # => "45"
version.dots_to_hyphens # => "1-2-3"
version.dots_to_underscores # => "1_2_3"
version.no_dots       # => "123"
```

---

## Useful Links

- Cask Cookbook: https://docs.brew.sh/Cask-Cookbook
- Acceptable Casks: https://docs.brew.sh/Acceptable-Casks
- Cask source for examples: https://github.com/Homebrew/homebrew-cask/tree/master/Casks
