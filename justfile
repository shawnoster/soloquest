# wyrd - Cross-platform task runner for local development
# CI/CD workflows use `uv run` commands directly (no just required)

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

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
    uv run wyrd

# Run tests with coverage
test:
    uv run python -m pytest

# Lint with ruff
lint:
    uv run ruff check wyrd tests

# Auto-format code with ruff
format:
    uv run ruff format wyrd tests
    uv run ruff check --fix wyrd tests

# Run lint + tests
check: lint test

# Remove build artifacts and caches
clean:
    -@if (Test-Path __pycache__) { Remove-Item -Recurse -Force __pycache__ }
    -@if (Test-Path .pytest_cache) { Remove-Item -Recurse -Force .pytest_cache }
    -@if (Test-Path htmlcov) { Remove-Item -Recurse -Force htmlcov }
    -@if (Test-Path dist) { Remove-Item -Recurse -Force dist }
    -@if (Test-Path build) { Remove-Item -Recurse -Force build }
    -@if (Test-Path .coverage) { Remove-Item -Force .coverage }
    -@Get-ChildItem -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

# Create and switch to new feature branch (e.g., just branch feat/my-feature)
branch NAME:
    @Write-Host "Creating branch: {{NAME}}"
    @git checkout -b {{NAME}}
    @Write-Host "✅ Switched to new branch: {{NAME}}"

# Create pull request for current branch
pr:
    @$current = (git branch --show-current); if ($current -eq "main") { Write-Host "❌ Error: You're on main branch"; Write-Host "Create a feature branch first: just branch feat/description"; exit 1 }; Write-Host "Creating PR for branch: $current"; gh pr create --base main
