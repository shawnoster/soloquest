# CLAUDE.md — Project Conventions for solo-cli

## Branching

- Never push directly to `main`. All work goes on feature branches.
- Branch naming: `feat/`, `fix/`, `refactor/`, `docs/`, `chore/` + short description.
- Merge to `main` via pull request. Delete branches after merge.

## Commits

- Use Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Summary under 72 chars. Body explains *why*, not *what*.

## Code Quality

- Run `make check` (lint + tests) before pushing.
- All new features should include tests.
- Formatter: `ruff format`. Linter: `ruff check`.

## Tech Stack

- Python 3.13+, uv, hatchling
- rich, prompt-toolkit
- ruff, pytest, pytest-cov

## Quick Reference

- `make` — show all available commands
- `make run` — launch the CLI
- `make check` — lint + test
- ADRs live in `docs/adr/`
