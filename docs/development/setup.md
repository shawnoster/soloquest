# Development Setup Guide

Complete guide to setting up your development environment for wyrd.

---

## Prerequisites

- **Python 3.13+** - Check with `python --version` or `python3 --version`
- **uv** - Python package installer ([installation guide](https://github.com/astral-sh/uv))
- **git** - Version control
- **make** - Task runner (see [Installing Make](#installing-make) below)

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/wyrd.git
cd wyrd

# Install dependencies
uv sync

# Run the CLI
uv run wyrd

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

## Installing Make

### Ubuntu / Linux

`make` is typically pre-installed. If not:

```bash
sudo apt install make
```

Verify:
```bash
make --version
```

### Windows

On Windows, run `make` through one of these options:

**Option 1: Git Bash (Recommended)**
Git Bash is included with [Git for Windows](https://git-scm.com/download/win) and includes `make`. Open "Git Bash" from the Start menu and all `make` commands work identically to Linux.

**Option 2: WSL (Windows Subsystem for Linux)**
Install WSL and Ubuntu, then follow the Ubuntu instructions above.

**Option 3: Standalone make**
```powershell
# winget
winget install GnuWin32.Make

# or Chocolatey
choco install make

# or Scoop
scoop install make
```

Verify:
```bash
make --version
```

---

## Development Workflow

### 1. Set Up Your Environment

```bash
# Clone and enter the repository
git clone https://github.com/yourusername/wyrd.git
cd wyrd

# Install dependencies (including dev dependencies)
uv sync

# Install git hooks (runs format, lint, and tests before each commit)
make install-hooks

# Verify everything works
make check
```

### 2. Create a Feature Branch

```bash
# Using make
make branch NAME=feat/my-feature

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
# Run all checks (lint + tests)
make check

# Or individually
make lint      # Check for issues
make format    # Auto-format code
make test      # Run tests with coverage
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

| Command | Description |
|---------|-------------|
| `make` | Show all commands |
| `make install` | Install dependencies |
| `make dev` | Install with dev dependencies |
| `make run` | Run the CLI |
| `make test` | Run tests with coverage |
| `make lint` | Check code with ruff |
| `make format` | Auto-format code |
| `make check` | Lint + tests |
| `make clean` | Remove build artifacts |
| `make branch NAME=<name>` | Create a new feature branch |
| `make pr` | Create a pull request (requires gh CLI) |

### Direct uv Commands

You can also run commands directly with `uv`:

```bash
# Run the CLI
uv run wyrd
uv run python -m wyrd.main

# Run tests
uv run pytest
uv run pytest --cov=wyrd --cov-report=html

# Linting and formatting
uv run ruff check .
uv run ruff format .
```

---

## Testing

### Running Tests

```bash
# All tests
make test

# Specific test file
uv run pytest tests/test_moves.py

# Specific test
uv run pytest tests/test_moves.py::test_strong_hit

# With verbose output
uv run pytest -v

# With coverage report
uv run pytest --cov=wyrd --cov-report=html
# Open htmlcov/index.html in browser
```

### Manual Testing

For interactive features and UI testing, see [testing.md](testing.md) for the complete manual testing guide.

---

## Code Quality

### Linting

We use `ruff` for linting:

```bash
make lint
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
make format
# or
uv run ruff format .
```

### Type Checking

Type hints are encouraged but not enforced. If you want to check types:

```bash
uv run mypy wyrd
```

---

## Project Structure

```
wyrd/
├── wyrd/          # Main package
│   ├── commands/       # Command handlers
│   ├── engine/         # Game mechanics
│   ├── models/         # Data models
│   ├── state/          # Persistence
│   ├── journal/        # Export system
│   ├── ui/             # Display helpers
│   └── data/           # Game content
├── tests/              # Test suite
├── docs/               # Documentation
├── Makefile            # Task runner (Ubuntu and Windows)
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

### `make: command not found`

On Ubuntu: `sudo apt install make`

On Windows: Use Git Bash (bundled with Git for Windows) or install make via `winget install GnuWin32.Make`.

### Import errors when running tests

Make sure you've installed dependencies:
```bash
uv sync
```

### `ModuleNotFoundError: No module named 'wyrd'`

Run commands with `uv run`:
```bash
uv run pytest
uv run wyrd
```

### Tests fail with "dataforged not found"

The dataforged JSON files should be in `wyrd/data/dataforged/`. If missing:
```bash
git status  # Check if files are tracked
git submodule update --init  # If it's a submodule
```

---

## IDE Setup

### VS Code

Recommended extensions:
- Python (Microsoft)
- Ruff

### PyCharm

1. Mark `wyrd/` as "Sources Root"
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

- **Questions:** Open a [GitHub Discussion](https://github.com/yourusername/wyrd/discussions)
- **Bugs:** Open a [GitHub Issue](https://github.com/yourusername/wyrd/issues)
- **Chat:** Join the [Ironsworn Discord](https://discord.gg/ironsworn)
