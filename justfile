# soloquest - Cross-platform task runner for local development
# CI/CD workflows use `uv run` commands directly (no just required)

# Show all available commands
default:
    @just --list

# Install the package
install:
    uv sync

# Install with dev dependencies
dev:
    uv sync --group dev

# Run the CLI
run:
    uv run soloquest

# Run tests with coverage
test:
    uv run python -m pytest

# Lint with ruff
lint:
    uv run ruff check soloquest tests

# Auto-format code with ruff
format:
    uv run ruff format soloquest tests
    uv run ruff check --fix soloquest tests

# Run lint + tests
check: lint test

# Remove build artifacts and caches
clean:
    -rm -rf __pycache__ .pytest_cache htmlcov dist build
    -rm -f .coverage
    -find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Create and switch to new feature branch (e.g., just branch feat/my-feature)
branch NAME:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Creating branch: {{NAME}}"
    git checkout -b {{NAME}}
    echo "✅ Switched to new branch: {{NAME}}"

# Create pull request for current branch
pr:
    #!/usr/bin/env bash
    set -euo pipefail
    current=$(git branch --show-current)
    if [ "$current" = "main" ]; then
        echo "❌ Error: You're on main branch"
        echo "Create a feature branch first: just branch feat/description"
        exit 1
    fi
    echo "Creating PR for branch: $current"
    gh pr create --base main
