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
- JSON files vendored in `soloquest/data/dataforged/`
- Custom TOML files in `soloquest/data/` take priority (allow overrides)
- License: CC BY 4.0 / CC BY-NC 4.0 / MIT (see `soloquest/data/dataforged/LICENSE.md`)
- Attribution: Game content © Shawn Tomkin

## Quick Reference

- `just` — show all available commands
- `just run` — launch the CLI
- `just check` — lint + test
- ADRs live in `docs/adr/`
