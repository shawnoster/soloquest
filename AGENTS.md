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

## Testing Guidelines

### When to Use Real Objects vs Mocks

#### Use Real Objects for Business Logic
**Models** (`test_character.py`, `test_session.py`, `test_vow.py`):
- Test with real dataclasses — they're lightweight and test actual behavior
- Example: Create `Character(name="Test", stats=Stats())` instances directly
- No need to mock simple data structures

**Engine** (`test_integration.py`):
- Use deterministic stubs instead of mocking game logic
- Example: `FixedDice` class that returns preset values for dice rolls
- This tests the full data flow without randomness
- Keeps tests readable and maintainable

```python
class FixedDice:
    """Returns a preset sequence of values, cycling if exhausted."""
    def __init__(self, values: list[int]):
        self._values = values
        self._idx = 0
    
    def roll(self, die: Die) -> int:
        v = self._values[self._idx % len(self._values)]
        self._idx += 1
        return v
```

#### Use Mocks for UI and External Dependencies
**Commands** (`test_move_commands.py`, `test_session_commands.py`):
- Mock `display.console`, `Prompt.ask()`, `Confirm.ask()`, etc.
- This is appropriate because we test command behavior, not rendering
- Use `@patch("soloquest.commands.module.display")` to mock display layer
- Use `MagicMock()` for state objects when testing command handlers

```python
@patch("soloquest.commands.session.display")
def test_empty_session_shows_message(self, mock_display):
    handle_log(self.state, [], set())
    mock_display.info.assert_called_once_with("No entries in this session yet.")
```

### Test File Organization

#### Mirror Source Structure
- `tests/test_character.py` → `soloquest/models/character.py`
- `tests/test_move_commands.py` → `soloquest/commands/move.py`
- `tests/engine/` → `soloquest/engine/`

#### Use Class-Based Organization
```python
class TestCharacter:
    def setup_method(self):
        self.char = Character(name="Kael", stats=Stats(edge=2, heart=1, iron=3))
    
    def test_adjust_track_clamps_at_5(self):
        self.char.health = 5
        new = self.char.adjust_track("health", 2)
        assert new == 5
```

#### Descriptive Test Names
- Format: `test_<action>_<expected_result>`
- Examples:
  - `test_adjust_track_clamps_at_5`
  - `test_empty_query_returns_no_matches`
  - `test_strong_hit_applies_momentum_bonus`

### Coverage Expectations

Different modules have different coverage expectations based on their testability:

| Module Type | Target Coverage | Notes |
|------------|----------------|-------|
| **Models** (`models/`) | 100% | Simple dataclasses, fully testable |
| **Engine** (`engine/`) | 100% | Pure logic, no I/O, fully testable |
| **Commands** (`commands/`) | 70%+ | Some UI interaction makes 100% impractical |
| **UI/Display** (`ui/`) | Lower priority | Hard to test without integration tests |

#### Why These Targets?
- **Models/Engine**: Pure business logic with no side effects — should be 100% covered
- **Commands**: Mix of logic and UI — focus on testing command logic, not rendering
- **UI/Display**: Primarily rendering code — integration tests more valuable than unit tests

### Running Tests

```bash
# Run all tests with coverage
just test

# Run specific test file
pytest tests/test_character.py

# Run specific test class or method
pytest tests/test_character.py::TestCharacter::test_adjust_track_up

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "test_momentum"
```

### Best Practices

1. **Test both success and edge cases**
   - Normal operation
   - Boundary conditions (min/max values)
   - Error conditions

2. **Keep tests independent**
   - Use `setup_method` for test-specific state
   - Don't rely on test execution order
   - Clean up after tests if needed

3. **Use parametrize for similar tests**
   ```python
   @pytest.mark.parametrize("stat_name,expected", [
       ("edge", 2),
       ("iron", 3),
       ("wits", 3),
   ])
   def test_get_stat(self, stat_name, expected):
       assert self.char.stats.get(stat_name) == expected
   ```

4. **Prefer determinism over randomness**
   - Use `FixedDice` for dice rolls
   - Use preset values for oracles
   - This makes tests reproducible

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
