# Contributing to Development

See the main [CONTRIBUTING.md](../../CONTRIBUTING.md) in the root directory for complete contribution guidelines.

This page provides additional context for developers.

---

## Quick Links

- **[Main Contributing Guide](../../CONTRIBUTING.md)** - Complete guidelines
- **[Setup Guide](setup.md)** - Development environment setup
- **[Testing Guide](testing.md)** - Manual testing procedures
- **[Project Status](project-status.md)** - Current development state

---

## Development Commands

### Using Just (Recommended)

```bash
just            # Show all available commands
just run        # Launch the CLI
just test       # Run tests with coverage
just check      # Lint + tests
just format     # Format code
```

### Using Make

```bash
make            # Show help
make run        # Launch the CLI
make test       # Run tests
make check      # Lint + tests
make format     # Format code
```

---

## Project Structure

```
wyrd/
├── main.py             # Entry point
├── loop.py             # REPL game loop
├── commands/           # Command handlers
│   ├── move.py
│   ├── oracle.py
│   ├── vow.py
│   └── ...
├── engine/             # Game mechanics
│   ├── dice.py
│   ├── moves.py
│   ├── oracles.py
│   └── momentum.py
├── models/             # Data models
│   ├── character.py
│   ├── vow.py
│   └── session.py
├── journal/            # Export system
│   └── exporter.py
├── data/               # Game data
│   ├── dataforged/     # Vendored dataforged JSON
│   └── ...
├── state/              # Persistence
│   └── save.py
└── ui/                 # Display helpers
    └── display.py
```

---

## Working with Dataforged

Game content (moves, oracles, assets) comes from the [dataforged](https://github.com/rsek/dataforged) package:

- JSON files in `wyrd/data/dataforged/`
- Loaded at runtime by `dataforged_loader.py`
- 200+ oracle tables, 90+ assets, 56 moves

**License:** CC BY 4.0 / CC BY-NC 4.0 / MIT (see `wyrd/data/dataforged/LICENSE.md`)

---

## Adding New Features

### Adding a New Command

1. Create command handler in `wyrd/commands/`
2. Register in command registry
3. Add tests in `tests/`
4. Update help text
5. Document in user guide

### Adding a New Move

Moves come from dataforged. To customize:

1. Check if move exists in dataforged JSON
2. If not, add custom TOML in `wyrd/data/`
3. Update move loader to handle custom moves

### Adding a New Oracle Table

Oracle tables come from dataforged. To customize:

1. Check dataforged JSON first
2. For custom tables, add TOML in `wyrd/data/`
3. Update oracle loader

---

## Common Development Tasks

### Running Tests for a Specific Module

```bash
pytest tests/test_moves.py
pytest tests/test_character.py -v
```

### Debugging a Test

```bash
pytest tests/test_moves.py::test_strong_hit -vv
```

### Checking Coverage

```bash
pytest --cov=wyrd --cov-report=html
# Open htmlcov/index.html in browser
```

### Running Manual Playtest

See [testing.md](testing.md) for complete manual testing guide.

---

## Tips for Contributors

### Keep PRs Focused

- One feature or fix per PR
- Easier to review, easier to merge
- Can be deployed independently

### Write Tests First

- TDD helps clarify requirements
- Catches edge cases early
- Makes refactoring safer

### Follow Existing Patterns

- Look at similar existing code
- Match the style and structure
- Ask if unsure!

### Update Documentation

- User-facing changes → update user guides
- Architecture changes → create ADR
- New features → update README

---

## Questions?

- Check [Project Status](project-status.md) for current state
- Look at [ADRs](../adr/) for design context
- Ask in GitHub Discussions
- Open an issue for bugs
