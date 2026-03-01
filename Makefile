# Works on Ubuntu/Linux natively and Windows via Git Bash or WSL.
# Install make: Ubuntu: sudo apt install make | Windows: included in Git Bash, or winget install GnuWin32.Make

.DEFAULT_GOAL := help

.PHONY: help install install-hooks dev run test lint format check clean branch pr

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help            Show this help message"
	@echo "  install         Install the package"
	@echo "  install-hooks   Configure git to use tracked hooks in .githooks/"
	@echo "  dev             Install with dev dependencies"
	@echo "  run             Run the CLI"
	@echo "  test            Run tests with coverage"
	@echo "  lint            Lint with ruff"
	@echo "  format          Auto-format code with ruff"
	@echo "  check           Run lint + tests"
	@echo "  clean           Remove build artifacts and caches"
	@echo "  branch NAME=x   Create and switch to new feature branch"
	@echo "  pr              Create pull request for current branch"

install: install-hooks ## Install the package
	uv sync

install-hooks: ## Configure git to use tracked hooks in .githooks/
	git config core.hooksPath .githooks
	@echo "✅ Git hooks configured (.githooks/)"

dev: ## Install with dev dependencies
	uv sync --group dev

run: ## Run the CLI
	uv run wyrd

test: ## Run tests with coverage
	uv run python -m pytest

lint: ## Lint with ruff
	uv run ruff check wyrd tests

format: ## Auto-format code with ruff
	uv run ruff format wyrd tests
	uv run ruff check --fix wyrd tests

check: lint test ## Run lint + tests

clean: ## Remove build artifacts and caches (works on Ubuntu and Windows)
	uv run python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['__pycache__', '.pytest_cache', 'htmlcov', 'dist', 'build'] + [str(p) for p in pathlib.Path('.').rglob('__pycache__')]]; pathlib.Path('.coverage').unlink(missing_ok=True)"

branch: ## Create and switch to new feature branch (e.g., make branch NAME=fix/something)
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is required"; \
		echo "Usage: make branch NAME=feat/description"; \
		echo ""; \
		echo "Prefixes: feat/, fix/, refactor/, docs/, chore/"; \
		exit 1; \
	fi
	@echo "Creating branch: $(NAME)"
	@git checkout -b $(NAME)
	@echo "Switched to new branch: $(NAME)"

pr: ## Create pull request for current branch
	@current=$$(git branch --show-current); \
	if [ "$$current" = "main" ]; then \
		echo "Error: You're on main branch"; \
		echo "Create a feature branch first: make branch NAME=feat/description"; \
		exit 1; \
	fi
	@echo "Creating PR for branch: $$(git branch --show-current)"
	@gh pr create --base main
