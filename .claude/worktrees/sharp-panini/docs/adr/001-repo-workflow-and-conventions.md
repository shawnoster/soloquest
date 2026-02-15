# ADR-001: Repository Workflow and Conventions

**Status:** Accepted
**Date:** 2026-02-14

## Context

This is a personal project — a solo journaling CLI companion for Ironsworn: Starforged. As the project matures it needs consistent processes for branching, commits, code quality, and releases to keep the codebase healthy and the history readable.

## Decision

### Branching Strategy

- **`main`** is the stable, always-deployable branch. Never push directly to `main` after initial setup.
- All work happens on **feature branches** off `main`, using the naming convention:
  - `feat/<short-description>` — new features
  - `fix/<short-description>` — bug fixes
  - `refactor/<short-description>` — restructuring without behavior change
  - `docs/<short-description>` — documentation only
  - `chore/<short-description>` — tooling, CI, dependencies
- Feature branches are merged into `main` via **pull requests**.
- **PR titles MUST follow Conventional Commits format** (e.g., `feat: add session export`, `fix: handle Unicode on Windows`)
- PR body should include a **Summary** section (bullet points) and **Test plan**
- Keep PR titles under 70 chars
- Delete feature branches after merge.

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <short summary>

<optional body explaining why, not what>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`

Keep the summary under 72 characters. Use the body for context on *why* the change was made.

### Code Quality

- **Linting:** `ruff check` — must pass before merge.
- **Formatting:** `ruff format` — enforced consistently.
- **Tests:** `pytest` with coverage — must pass before merge.
- Use `make check` to run lint + tests together.
- All new features should include tests.

### Development Commands

Common tasks are managed via `Makefile`:

| Command        | Purpose                        |
|----------------|--------------------------------|
| `make`         | Show help                      |
| `make install` | Install dependencies           |
| `make dev`     | Install with dev dependencies  |
| `make run`     | Run the CLI                    |
| `make test`    | Run tests with coverage        |
| `make lint`    | Lint with ruff                 |
| `make format`  | Auto-format code               |
| `make check`   | Lint + tests                   |
| `make clean`   | Remove build artifacts         |

### Dependencies

- **Runtime:** Python 3.13+, `rich`, `prompt-toolkit`
- **Dev:** `ruff`, `pytest`, `pytest-cov`
- **Package management:** `uv`
- **Build backend:** `hatchling`

### Project Structure

```
starforged/          # Main package
  commands/          # CLI command handlers
  engine/            # Game mechanics (dice, moves, oracles)
  models/            # Data models (character, session, vow)
  state/             # Persistence (save/load)
  ui/                # Display and formatting
  journal/           # Journal export
tests/               # Test suite
docs/                # Documentation and ADRs
  adr/               # Architecture Decision Records
saves/               # Character save files (git-ignored)
sessions/            # Session data
journal/             # Exported journals
```

## Consequences

- All changes go through PRs, providing a clear history and review point.
- Conventional commits make the changelog readable and automatable.
- `make check` provides a single command to validate changes before pushing.
- ADRs document significant decisions for future reference.
