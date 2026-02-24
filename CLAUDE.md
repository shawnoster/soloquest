# CLAUDE.md — Project Conventions for solo-cli

## Branching

- Never push directly to `main`. All work goes on feature branches.
- Branch naming: `feat/`, `fix/`, `refactor/`, `docs/`, `chore/` + short description.
- Merge to `main` via pull request. Delete branches after merge.

## Commits

- Use Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Summary under 72 chars. Body explains *why*, not *what*.

## Pull Requests

- **PR titles MUST follow Conventional Commits format** (same as commit messages)
- Examples: `feat: add character creation`, `fix: handle empty vow list`
- Body should include Summary section (bullet points) and Test plan
- Keep PR titles under 70 chars

## Code Quality

- Run `just check` (lint + tests) before pushing.
- All new features should include tests.
- Formatter: `ruff format`. Linter: `ruff check`.

## Tech Stack

- Python 3.13+, uv, hatchling
- rich, prompt-toolkit
- ruff, pytest, pytest-cov

## Dataforged Integration

- Game data (oracles, moves, assets) sourced from [dataforged](https://github.com/rsek/dataforged)
- JSON files vendored in `wyrd/data/dataforged/`
- Custom TOML files in `wyrd/data/` take priority (allow overrides)
- License: CC BY 4.0 / CC BY-NC 4.0 / MIT (see `wyrd/data/dataforged/LICENSE.md`)
- Attribution: Game content © Shawn Tomkin

## Documentation Structure

**When you need to find information:**

- **Current project state:** [docs/development/project-status.md](docs/development/project-status.md)
- **New feature ideas:** Check GitHub Issues with `enhancement` label
- **Project specifications:** [docs/specifications/poc-spec.md](docs/specifications/poc-spec.md)
- **Architecture decisions:** [docs/adr/](docs/adr/)
- **Development setup:** [docs/development/setup.md](docs/development/setup.md)
- **User documentation:** [docs/user-guide/](docs/user-guide/)
- **Historical snapshots:** [docs/archive/](docs/archive/) (dated snapshots from past milestones)

**All documentation is indexed at:** [docs/README.md](docs/README.md)

## Quick Reference

- `just` — show all available commands
- `just run` — launch the CLI
- `just check` — lint + test
- `just branch feat/name` — create feature branch
