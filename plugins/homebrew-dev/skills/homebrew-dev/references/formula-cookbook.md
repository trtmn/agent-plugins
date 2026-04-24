# Formula Cookbook

Complete, annotated formula patterns for common build systems and scenarios.

---

## Autoconf/Make

The most common C/C++ build pattern. `std_configure_args` adds `--prefix`, `--disable-debug`, etc.

```ruby
class Htop < Formula
  desc "Improved top (interactive process viewer)"
  homepage "https://htop.dev"
  url "https://github.com/htop-dev/htop/releases/download/3.3.0/htop-3.3.0.tar.xz"
  sha256 "abc123..."
  license "GPL-2.0-or-later"

  depends_on "autoconf" => :build   # only needed at build time
  depends_on "automake" => :build
  depends_on "ncurses"              # runtime dependency

  def install
    system "autoreconf", "--force", "--install", "--verbose"
    system "./configure", "--disable-silent-rules",
                          "--enable-unicode",
                          *std_configure_args   # adds --prefix=#{prefix}, etc.
    system "make", "install"
  end

  test do
    # --version or --help is the minimal test pattern
    assert_match version.to_s, shell_output("#{bin}/htop --version")
  end
end
```

---

## CMake

```ruby
class Ripgrep < Formula
  desc "Search tool like grep and The Silver Searcher"
  homepage "https://github.com/BurntSushi/ripgrep"
  url "https://github.com/BurntSushi/ripgrep/archive/refs/tags/14.1.0.tar.gz"
  sha256 "abc123..."
  license "MIT"

  depends_on "cmake" => :build
  depends_on "rust" => :build   # if CMake calls cargo internally

  def install
    system "cmake", "-S", ".", "-B", "build",
                    "-DCMAKE_BUILD_TYPE=Release",
                    *std_cmake_args   # adds -DCMAKE_INSTALL_PREFIX=#{prefix}, etc.
    system "cmake", "--build", "build"
    system "cmake", "--install", "build"

    # Install shell completions if generated
    generate_completions_from_executable(bin/"rg", "--generate", shells: [:bash, :zsh, :fish])
  end

  test do
    (testpath/"test.txt").write("hello world\n")
    assert_match "hello world", shell_output("#{bin}/rg hello #{testpath}")
  end
end
```

---

## Cargo (Rust)

`std_cargo_args` adds `--root #{prefix}` and the release flag.

```ruby
class Bat < Formula
  desc "Clone of cat(1) with syntax highlighting and Git integration"
  homepage "https://github.com/sharkdp/bat"
  url "https://github.com/sharkdp/bat/archive/refs/tags/v0.24.0.tar.gz"
  sha256 "abc123..."
  license any_of: ["Apache-2.0", "MIT"]

  depends_on "rust" => :build

  def install
    system "cargo", "install", *std_cargo_args

    # Completions generated at build time into OUT_DIR
    bash_completion.install "target/release/build/bat-#{version}/out/assets/completions/bat.bash"
    zsh_completion.install "target/release/build/bat-#{version}/out/assets/completions/bat.zsh"
    fish_completion.install "target/release/build/bat-#{version}/out/assets/completions/bat.fish"

    man1.install "target/release/build/bat-#{version}/out/assets/manual/bat.1"
  end

  test do
    assert_match "bat #{version}", shell_output("#{bin}/bat --version")
    (testpath/"test.rb").write("puts 'hello'")
    assert_match "hello", shell_output("#{bin}/bat --plain #{testpath}/test.rb")
  end
end
```

---

## Go

`std_go_args` adds ldflags for stripping debug info and injecting version strings.

```ruby
class Lazygit < Formula
  desc "Simple terminal UI for git commands"
  homepage "https://github.com/jesseduffield/lazygit"
  url "https://github.com/jesseduffield/lazygit/archive/refs/tags/v0.40.2.tar.gz"
  sha256 "abc123..."
  license "MIT"

  depends_on "go" => :build

  def install
    system "go", "build", *std_go_args(ldflags: "-s -w -X main.version=#{version}"),
                          "-o", bin/"lazygit", "."
    # Or for a cmd subdirectory:
    # system "go", "build", *std_go_args, "-o", bin/"lazygit", "./cmd/lazygit"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/lazygit --version")
  end
end
```

---

## Pre-built Binary (no build step)

Use when distributing pre-compiled binaries. Architecture conditionals handle Apple Silicon vs Intel.

```ruby
class Mycli < Formula
  desc "My custom CLI tool"
  homepage "https://example.com/mycli"
  license "MIT"

  on_arm do
    url "https://example.com/mycli-1.0-darwin-arm64.tar.gz"
    sha256 "arm64_sha256..."
  end

  on_intel do
    url "https://example.com/mycli-1.0-darwin-amd64.tar.gz"
    sha256 "amd64_sha256..."
  end

  version "1.0"

  def install
    bin.install "mycli"                                # binary → $(brew --prefix)/bin/
    man1.install "mycli.1" if File.exist?("mycli.1")   # optional manpage
    bash_completion.install "completions/mycli.bash" if File.exist?("completions/mycli.bash")
    zsh_completion.install "completions/_mycli"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/mycli --version")
  end
end
```

---

## Architecture Conditionals

For builds from a single source that need different compile-time flags per arch, use `Hardware::CPU.arm?` inside methods (`on_arm`/`on_intel` are class-level DSL and can't be called inside `def install`):

```ruby
class Myapp < Formula
  desc "Cross-platform tool"
  homepage "https://example.com"
  url "https://example.com/source-1.0.tar.gz"
  sha256 "source_sha..."
  license "Apache-2.0"

  def install
    arch_args = Hardware::CPU.arm? ? ["--arch=arm64"] : ["--arch=x86_64"]

    system "./configure", *std_configure_args, *arch_args
    system "make", "install"
  end

  test do
    system "#{bin}/myapp", "--help"
  end
end
```

`on_arm`/`on_intel` blocks at the **class level** are for declaring different URLs or dependencies per arch (see the Pre-built Binary section above for an example).

---

## Services (launchd)

For daemons that run in the background via `brew services`.

```ruby
class Redis < Formula
  desc "Persistent key-value database, with built-in net interface"
  homepage "https://redis.io"
  url "https://download.redis.io/releases/redis-7.2.4.tar.gz"
  sha256 "abc123..."
  license "BSD-3-Clause"

  def install
    system "make", "install", "PREFIX=#{prefix}"
    etc.install "redis.conf"
  end

  service do
    run [opt_bin/"redis-server", etc/"redis.conf"]
    keep_alive true
    log_path var/"log/redis.log"
    error_log_path var/"log/redis.log"
  end

  test do
    port = free_output_port
    fork { exec bin/"redis-server", "--port", port.to_s }
    sleep 1
    assert_match "PONG", shell_output("#{bin}/redis-cli -p #{port} ping")
  end
end
```

---

## Dependency Types

```ruby
# Build-time only (not installed with the formula)
depends_on "cmake" => :build
depends_on "pkg-config" => :build

# Test-time only
depends_on "python@3.12" => :test

# Optional (not installed by default; user opts in)
depends_on "readline" => :optional

# Recommended (installed by default; user opts out with --without-readline)
depends_on "readline" => :recommended

# Minimum macOS version
depends_on :macos => :monterey    # 12
depends_on :macos => :ventura     # 13
depends_on :macos => :sonoma      # 14

# Homebrew's Python (use this, not system Python)
depends_on "python@3.12"
```

---

## Test Patterns

```ruby
test do
  # Run binary with --version (always include this)
  assert_match version.to_s, shell_output("#{bin}/mytool --version")

  # Expect failure (non-zero exit) — use shell_output with exit code check
  assert_match "error", shell_output("#{bin}/mytool invalid_arg 2>&1", 1)

  # Create a temp file in testpath (isolated temp dir)
  (testpath/"input.txt").write("hello world\n")
  output = shell_output("#{bin}/mytool #{testpath}/input.txt")
  assert_match "hello", output

  # Run a server briefly (fork + sleep)
  port = free_output_port
  fork { exec bin/"myserver", "--port", port.to_s }
  sleep 1
  assert_match "OK", shell_output("curl -s http://localhost:#{port}/health")

  # Test help output
  system "#{bin}/mytool", "--help"  # just checks it exits 0
end
```

---

## inreplace (Patching)

Edit files during install to fix hardcoded paths:

```ruby
def install
  # Simple string substitution
  inreplace "Makefile", "/usr/local", HOMEBREW_PREFIX

  # Regex substitution
  inreplace "config.h", /VERSION\s*=\s*"[^"]*"/, "VERSION = \"#{version}\""

  # Multiple files at once
  inreplace ["lib/config.rb", "bin/mytool"], "/usr/share", "#{share}"

  system "./configure", *std_configure_args
  system "make", "install"
end
```

---

## Virtual/Python Packages

For Python CLI tools distributed via PyPI:

```ruby
class Mypy < Formula
  desc "Optional static typing for Python"
  homepage "https://mypy-lang.org"
  url "https://files.pythonhosted.org/packages/.../mypy-1.9.0.tar.gz"
  sha256 "abc123..."
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    (testpath/"test.py").write("x: int = 1\n")
    assert_match "Success", shell_output("#{bin}/mypy #{testpath}/test.py")
  end
end
```

---

## Python Package with Resources

Use this pattern when your formula installs a Python CLI tool from PyPI that has PyPI dependencies beyond the stdlib. Homebrew sandboxes the install, so you must vendor every dependency as a `resource` block — you cannot `pip install` at build time.

**Auto-generate all resource blocks:**
```bash
brew update-python-resources mytool
```
This command resolves the full PyPI dependency tree for `mytool` and prints ready-to-paste `resource` blocks with correct URLs and sha256s. Run it first — do not write resource blocks by hand.

**Annotated example:**
```ruby
class Mytool < Formula
  desc "A CLI tool written in Python"
  homepage "https://example.com/mytool"
  url "https://files.pythonhosted.org/packages/.../mytool-1.0.tar.gz"
  sha256 "abc123..."
  license "MIT"

  depends_on "python@3.12"

  # Each PyPI dependency becomes a resource block.
  # Generate these with: brew update-python-resources mytool
  resource "click" do
    url "https://files.pythonhosted.org/packages/.../click-8.1.7.tar.gz"
    sha256 "deadbeef..."
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/.../requests-2.31.0.tar.gz"
    sha256 "cafebabe..."
  end

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/.../certifi-2024.2.2.tar.gz"
    sha256 "..."
  end

  def install
    # Installs the package and all resources into an isolated virtualenv
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/mytool --version")
  end
end
```

**Key points:**
- `virtualenv_install_with_resources` creates a virtualenv, installs all `resource` blocks into it, then installs the formula itself.
- Re-run `brew update-python-resources mytool` whenever you bump the version to refresh dependency shas.
- If a transitive dependency fails the audit (e.g. `chardet` pulled in by `requests`), add it as a resource too.

---

## Useful Links

- Formula Cookbook: https://docs.brew.sh/Formula-Cookbook
- Ruby API docs: https://rubydoc.brew.sh/Formula
- Acceptable Formulae: https://docs.brew.sh/Acceptable-Formulae
