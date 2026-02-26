# Contributing to wyrd

Thank you for your interest in contributing to wyrd! This document provides guidelines and instructions for contributing.

---

## Getting Started

1. **Read the documentation**
   - [Getting Started Guide](docs/user-guide/getting-started.md) - Understand how the tool works
   - [POC Specification](docs/specifications/poc-spec.md) - Understand the design goals
   - [ADRs](docs/adr/) - Understand architectural decisions

2. **Set up your development environment**
   - See [Development Setup Guide](docs/development/setup.md)

3. **Check existing issues**
   - Browse [open issues](https://github.com/yourusername/wyrd/issues)
   - Look for issues tagged `good first issue` or `help wanted`

---

## Development Workflow

### Branching Strategy

- **`main`** is the stable branch - never push directly to main
- Create feature branches from main using the naming convention:
  - `feat/<description>` - new features
  - `fix/<description>` - bug fixes
  - `refactor/<description>` - code restructuring
  - `docs/<description>` - documentation changes
  - `chore/<description>` - tooling, dependencies, CI

### Making Changes

1. **Create a branch:**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, readable code
   - Follow existing code style
   - Add tests for new features
   - Update documentation as needed

3. **Run quality checks:**
   ```bash
   make check
   ```

   This runs:
   - `ruff check` - linting
   - `ruff format` - formatting
   - `pytest` - tests

4. **Commit your changes:**
   - Use [Conventional Commits](https://www.conventionalcommits.org/)
   - Format: `<type>: <description>`
   - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
   - Keep summary under 72 characters

   Example:
   ```bash
   git commit -m "feat: add momentum burn confirmation prompt"
   ```

5. **Push and create a pull request:**
   ```bash
   git push -u origin feat/your-feature-name
   ```

### Pull Request Guidelines

- **PR title MUST follow Conventional Commits format**
  - Examples: `feat: add asset abilities`, `fix: handle empty vow list`
  - Keep under 70 characters

- **PR description should include:**
  - **Summary** - Bullet points of what changed
  - **Test plan** - How to verify the changes work
  - **Screenshots** (if UI changes)

- **Before submitting:**
  - [ ] Code follows project conventions (see CLAUDE.md)
  - [ ] All tests pass (`make check`)
  - [ ] New features include tests
  - [ ] Documentation is updated
  - [ ] PR title follows Conventional Commits

---

## Code Quality Standards

### Linting and Formatting

We use `ruff` for both linting and formatting:

```bash
# Check for issues
ruff check .

# Auto-format code
ruff format .

# Or use make
make check
```

### Testing

All new features should include tests:

```bash
# Run tests
pytest

# With coverage report
pytest --cov=wyrd --cov-report=html

# Or use make
make test
```

**Test coverage expectations:**
- Core engine code (moves, oracles, dice): 100%
- Models (character, vow, session): 100%
- Commands: Integration tests where practical
- UI code: Manual testing acceptable

### Code Style

- Follow existing patterns in the codebase
- Use type hints where they add clarity
- Keep functions focused and single-purpose
- Prefer explicit over clever
- Don't add comments that just repeat the code
- Comment the "why", not the "what"

---

## Testing

### Automated Tests

Run the test suite:

```bash
pytest                    # Run all tests
pytest tests/test_moves.py  # Run specific test file
pytest -k "test_vow"      # Run tests matching pattern
```

### Manual Testing

For UI changes and new features, follow the [Manual Testing Guide](docs/development/testing.md).

---

## Documentation

### When to Update Documentation

Update documentation when you:
- Add new features or commands
- Change existing behavior
- Add new configuration options
- Make architectural decisions (create an ADR)

### Documentation Structure

- **User documentation** → `docs/user-guide/`
- **Developer documentation** → `docs/development/`
- **Architecture decisions** → `docs/adr/`
- **Main README** → High-level overview, quick start

---

## Release Process

Releases are automated via GitHub Actions:

1. Commits to `main` trigger semantic-release
2. Version bump based on commit type:
   - `feat:` → minor version (0.x.0)
   - `fix:` → patch version (0.0.x)
   - `BREAKING CHANGE:` → major version (x.0.0)
3. CHANGELOG.md updated automatically
4. GitHub release created with notes

**You don't need to manually update versions or changelog.**

---

## Getting Help

- **Questions?** Open a [discussion](https://github.com/yourusername/wyrd/discussions)
- **Bug reports?** Open an [issue](https://github.com/yourusername/wyrd/issues)
- **Want to chat?** Join the [Ironsworn Discord](https://discord.gg/ironsworn) and mention wyrd

---

## Code of Conduct

Be respectful, constructive, and collaborative. This is a community project built by volunteers.

---

## License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

Thank you for contributing to wyrd! 🎲
