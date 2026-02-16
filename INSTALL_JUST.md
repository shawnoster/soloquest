# Installing `just`

`just` is a cross-platform command runner (like `make`, but better).

## Installation Options

### Option 1: Using Cargo (Rust)
```bash
cargo install just
```

### Option 2: Pre-built Binaries
```bash
# Linux/WSL
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/bin

# Make sure ~/bin is in your PATH
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Option 3: Package Managers

**Windows (PowerShell):**
```powershell
winget install --id Casey.Just
# or
choco install just
# or
scoop install just
```

**Linux:**
```bash
# Debian/Ubuntu (via cargo-binstall)
cargo binstall just

# Arch
sudo pacman -S just

# Homebrew (macOS/Linux)
brew install just
```

**WSL (use Linux methods above)**

## Verify Installation

```bash
just --version
```

## Usage

After installation, run commands like:
```bash
just              # Show all available commands
just test         # Run tests
just check        # Run lint + tests
just branch feat/my-feature  # Create a new branch
```

## Migration from Make

The `justfile` is a drop-in replacement for the `Makefile`:
- `make test` → `just test`
- `make check` → `just check`
- `make branch NAME=feat/x` → `just branch feat/x`

All commands work the same way!
