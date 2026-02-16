# Development Setup Guide

Complete guide to setting up your development environment for soloquest.

---

## Prerequisites

- **Python 3.13+** - Check with `python --version` or `python3 --version`
- **uv** - Python package installer ([installation guide](https://github.com/astral-sh/uv))
- **git** - Version control
- **just** (recommended) or **make** - Task runner

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/soloquest.git
cd soloquest

# Install dependencies
uv sync

# Run the CLI
uv run soloquest

# Run tests
uv run pytest
```

---

## Installing uv

If you don't have `uv` installed:

```bash
# Linux/macOS/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

Verify installation:
```bash
uv --version
```

---

## Installing Just (Recommended)

`just` is a cross-platform command runner that makes development easier.

### Why Just?

- **Cross-platform** - Works identically on Windows (PowerShell), WSL, Linux, and macOS
- **Modern syntax** - Cleaner than Makefiles
- **Better errors** - More helpful error messages
- **Used widely** - Projects like uv, ruff, and other modern Python tools use it

### Installation Options

**Option 1: Pre-built Binaries (Recommended for WSL/Linux)**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/bin

# Add to PATH if needed
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Option 2: Using Cargo (Rust)**
```bash
cargo install just
```

**Option 3: Package Managers**

*Windows (PowerShell):*
```powershell
winget install --id Casey.Just
# or
choco install just
# or
scoop install just
```

*Linux:*
```bash
# Arch
sudo pacman -S just

# Homebrew (macOS/Linux)
brew install just
```

**Verify Installation:**
```bash
just --version
```

### Using Just

```bash
just              # Show all available commands
just test         # Run tests
just check        # Run lint + tests
just run          # Run the CLI
just branch feat/my-feature  # Create a feature branch
```

---

## Alternative: Using Make

If you prefer `make` or can't install `just`, a Makefile is also provided:

```bash
make              # Show help
make test         # Run tests
make check        # Run lint + tests
make run          # Run the CLI
```

**Note:** The Makefile and justfile are functionally equivalent. Choose whichever you prefer.

---

## Development Workflow

### 1. Set Up Your Environment

```bash
# Clone and enter the repository
git clone https://github.com/yourusername/soloquest.git
cd soloquest

# Install dependencies (including dev dependencies)
uv sync

# Verify everything works
just check  # or: make check
```

### 2. Create a Feature Branch

```bash
# Using just (provides guided prompts)
just branch feat/my-feature

# Or manually
git checkout -b feat/my-feature
```

Branch naming conventions:
- `feat/<description>` - New features
- `fix/<description>` - Bug fixes
- `refactor/<description>` - Code restructuring
- `docs/<description>` - Documentation only
- `chore/<description>` - Tooling, dependencies, CI

### 3. Make Your Changes

Edit code, add tests, update documentation.

### 4. Run Quality Checks

```bash
# Run all checks (lint + format + tests)
just check

# Or individually
just lint      # Check for issues
just format    # Auto-format code
just test      # Run tests with coverage
```

### 5. Commit and Push

```bash
# Commit using Conventional Commits format
git add .
git commit -m "feat: add new feature"

# Push to your branch
git push -u origin feat/my-feature
```

### 6. Create a Pull Request

Create a PR on GitHub with:
- Title following Conventional Commits format
- Summary of changes (bullet points)
- Test plan

---

## Available Commands

### Using Just

| Command | Description |
|---------|-------------|
| `just` | List all commands |
| `just install` | Install dependencies |
| `just dev` | Install with dev dependencies |
| `just run` | Run the CLI |
| `just test` | Run tests with coverage |
| `just lint` | Check code with ruff |
| `just format` | Auto-format code |
| `just check` | Lint + format + tests |
| `just clean` | Remove build artifacts |
| `just branch <name>` | Create a new feature branch |
| `just pr` | Create a pull request (requires gh CLI) |

### Using Make

All the same commands work with `make`:
```bash
make test
make check
make run
```

### Direct uv Commands

You can also run commands directly with `uv`:

```bash
# Run the CLI
uv run soloquest
uv run python -m soloquest.main

# Run tests
uv run pytest
uv run pytest --cov=soloquest --cov-report=html

# Linting and formatting
uv run ruff check .
uv run ruff format .
```

---

## Testing

### Running Tests

```bash
# All tests
just test

# Specific test file
uv run pytest tests/test_moves.py

# Specific test
uv run pytest tests/test_moves.py::test_strong_hit

# With verbose output
uv run pytest -v

# With coverage report
uv run pytest --cov=soloquest --cov-report=html
# Open htmlcov/index.html in browser
```

### Manual Testing

For interactive features and UI testing, see [testing.md](testing.md) for the complete manual testing guide.

---

## Code Quality

### Linting

We use `ruff` for linting:

```bash
just lint
# or
uv run ruff check .
```

Fix auto-fixable issues:
```bash
uv run ruff check . --fix
```

### Formatting

We use `ruff` for formatting:

```bash
just format
# or
uv run ruff format .
```

### Type Checking

Type hints are encouraged but not enforced. If you want to check types:

```bash
uv run mypy soloquest
```

---

## Project Structure

```
soloquest/
├── soloquest/          # Main package
│   ├── commands/       # Command handlers
│   ├── engine/         # Game mechanics
│   ├── models/         # Data models
│   ├── state/          # Persistence
│   ├── journal/        # Export system
│   ├── ui/             # Display helpers
│   └── data/           # Game content
├── tests/              # Test suite
├── docs/               # Documentation
├── justfile            # Task runner config
├── Makefile            # Alternative task runner
├── pyproject.toml      # Project configuration
└── uv.lock             # Dependency lock file
```

---

## Troubleshooting

### `uv: command not found`

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### `just: command not found`

Either install just (see above) or use `make` instead:
```bash
make test
make check
```

### Import errors when running tests

Make sure you've installed dependencies:
```bash
uv sync
```

### `ModuleNotFoundError: No module named 'soloquest'`

Run commands with `uv run`:
```bash
uv run pytest
uv run soloquest
```

### Tests fail with "dataforged not found"

The dataforged JSON files should be in `soloquest/data/dataforged/`. If missing:
```bash
git status  # Check if files are tracked
git submodule update --init  # If it's a submodule
```

---

## Migrating from Make to Just

If you've been using `make` and want to switch to `just`:

### Command Equivalents

| Make | Just |
|------|------|
| `make` | `just` |
| `make test` | `just test` |
| `make check` | `just check` |
| `make run` | `just run` |
| `make branch NAME=feat/x` | `just branch feat/x` |
| `make pr` | `just pr` |

### What Changed

1. **Better cross-platform support** - Works identically on Windows, WSL, and Linux
2. **Cleaner syntax** - No `.PHONY` declarations needed
3. **Better parameter handling** - `just branch feat/x` vs `make branch NAME=feat/x`

### CI/CD Impact

**None!** CI workflows use `uv run` commands directly and don't depend on make or just.

---

## IDE Setup

### VS Code

Recommended extensions:
- Python (Microsoft)
- Ruff
- Just (skellock.just)

### PyCharm

1. Mark `soloquest/` as "Sources Root"
2. Configure pytest as the test runner
3. Install ruff plugin

---

## Next Steps

- Read the [Contributing Guide](../../CONTRIBUTING.md)
- Review the [Testing Guide](testing.md)
- Check [Project Status](project-status.md) for current development state
- Browse [Architecture Decision Records](../adr/) for design context

---

## Getting Help

- **Questions:** Open a [GitHub Discussion](https://github.com/yourusername/soloquest/discussions)
- **Bugs:** Open a [GitHub Issue](https://github.com/yourusername/soloquest/issues)
- **Chat:** Join the [Ironsworn Discord](https://discord.gg/ironsworn)
