# AGENTS.md — Agent Coding Guidelines for soloquest

This file provides guidance for AI agents working in this repository.

---

## Build, Lint, and Test Commands

### Running the CLI
```bash
just run          # Launch the CLI
just install      # Install package with uv sync
just dev          # Install with dev dependencies
```

### Running Tests
```bash
just test         # Run all tests with coverage
pytest                           # Run all tests
pytest tests/test_character.py   # Run specific test file
pytest tests/test_character.py::TestCharacter::test_adjust_track_up  # Run specific test
pytest -k "test_name"            # Run tests matching pattern
pytest -v                        # Verbose output
pytest --cov=soloquest --cov-report=term-missing  # With coverage
```

### Linting and Formatting
```bash
just check       # Run lint + tests
just lint        # Run ruff check
just format      # Auto-format with ruff
```

### Other Commands
```bash
just clean       # Remove build artifacts and caches
just branch NAME # Create new feature branch
just pr          # Create pull request
```

---

## Code Style Guidelines

### General Principles
- Python 3.13+ required
- Use `from __future__ import annotations` for all files
- Line length: 100 characters (configured in pyproject.toml)
- No inline comments unless explicitly required (docstrings are encouraged)

### Imports
- Use `TYPE_CHECKING` guard for imports only needed for type hints
- Group imports: stdlib → third-party → first-party (local)
- Use `isort` conventions (configured in ruff)

### Type Hints
- Use Python 3.13+ native union syntax: `str | None` instead of `Optional[str]`
- Use `dict`, `list`, `set` instead of typing module equivalents
- Return types required for public functions
- Use `StrEnum` for string-based enums (e.g., `class DiceMode(StrEnum):`)

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `Character`, `GameState`)
- **Functions/methods**: `snake_case` (e.g., `handle_move`, `_parse_move_args`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MOMENTUM_MAX_BASE`, `TRACK_MAX`)
- **Private functions**: prefix with `_` (e.g., `_display_no_match_error`)
- **Files**: `snake_case.py`

### Data Classes
- Use `@dataclass` for simple data models
- Use `field(default_factory=...)` for mutable defaults
- Provide `to_dict()` and `from_dict()` methods for serialization

### Error Handling
- Use exceptions for exceptional cases, not for control flow
- Return `None` for "not found" or "cancelled" cases where appropriate
- Display user-friendly errors via `display.error()`, `display.warn()`, `display.info()`
- Catch `KeyboardInterrupt` and `EOFError` for CLI cancellable operations

### Pattern Matching
- Use `match/case` for type-based and enum-based dispatch

### Rich UI Patterns
- Use `display.console.print()` for output
- Use `Confirm.ask()` and `Prompt.ask()` for user input
- Use `Panel`, `Table`, `Markdown` for formatted output
- Use style markup: `[bold]`, `[dim]`, `[cyan]`, etc.

### Section Comments
- Use section comments to organize code blocks: `# ── Dice mode ─────────────────`

---

## Testing Conventions

### Test Organization
- Place tests in `tests/` directory mirroring source structure
- Name test files: `test_<module>.py`
- Use class-based organization: `class Test<Component>:`
- Use `setup_method` for per-test setup

### Test Style
- Use descriptive test names: `test_adjust_track_clamps_at_5`
- Use `pytest` assertions
- Test both positive and edge cases

---

## Git Conventions

### Branch Naming
- `feat/` — new features
- `fix/` — bug fixes
- `refactor/` — code refactoring
- `docs/` — documentation
- `chore/` — maintenance tasks

### Commit Messages
- Use Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Summary under 72 characters

---

## Project Structure

```
soloquest/
├── soloquest/           # Main package
│   ├── commands/        # CLI command handlers
│   ├── engine/          # Game logic (dice, moves, oracles)
│   ├── models/          # Data models (Character, Vow, Asset)
│   ├── state/           # Save/load logic
│   ├── ui/              # Display utilities
│   └── data/            # Game data (JSON, TOML)
├── tests/               # Test suite
├── pyproject.toml       # Project configuration
└── justfile             # Development commands
```

---

## Additional Notes
- Game data sourced from [dataforged](https://github.com/rsek/dataforged)
- Use `rich` for CLI output, `prompt-toolkit` for interactive prompts
