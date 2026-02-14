.DEFAULT_GOAL := help

.PHONY: help install dev run test lint format check clean branch pr

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help            Show this help message"
	@echo "  install         Install the package"
	@echo "  dev             Install with dev dependencies"
	@echo "  run             Run the CLI"
	@echo "  test            Run tests with coverage"
	@echo "  lint            Lint with ruff"
	@echo "  format          Auto-format code with ruff"
	@echo "  check           Run lint + tests"
	@echo "  clean           Remove build artifacts and caches"
	@echo "  branch NAME=x   Create and switch to new feature branch"
	@echo "  pr              Create pull request for current branch"

install: ## Install the package
	uv sync

dev: ## Install with dev dependencies
	uv sync --group dev

run: ## Run the CLI
	uv run soloquest

test: ## Run tests with coverage
	uv run pytest

lint: ## Lint with ruff
	uv run ruff check soloquest tests

format: ## Auto-format code with ruff
	uv run ruff format soloquest tests
	uv run ruff check --fix soloquest tests

check: lint test ## Run lint + tests

clean: ## Remove build artifacts and caches
	if exist __pycache__ rd /s /q __pycache__
	if exist .pytest_cache rd /s /q .pytest_cache
	if exist .coverage del .coverage
	if exist htmlcov rd /s /q htmlcov
	if exist dist rd /s /q dist
	if exist build rd /s /q build
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

branch: ## Create and switch to new feature branch (e.g., make branch NAME=fix/something)
	@if [ -z "$(NAME)" ]; then \
		echo "❌ Error: NAME is required"; \
		echo "Usage: make branch NAME=feat/description"; \
		echo ""; \
		echo "Prefixes: feat/, fix/, refactor/, docs/, chore/"; \
		exit 1; \
	fi
	@echo "Creating branch: $(NAME)"
	@git checkout -b $(NAME)
	@echo "✅ Switched to new branch: $(NAME)"

pr: ## Create pull request for current branch
	@current=$$(git branch --show-current); \
	if [ "$$current" = "main" ]; then \
		echo "❌ Error: You're on main branch"; \
		echo "Create a feature branch first: make branch NAME=feat/description"; \
		exit 1; \
	fi
	@echo "Creating PR for branch: $$(git branch --show-current)"
	@gh pr create --base main
