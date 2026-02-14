.DEFAULT_GOAL := help

.PHONY: help install dev run test lint format check clean

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

install: ## Install the package
	uv sync

dev: ## Install with dev dependencies
	uv sync --group dev

run: ## Run the CLI
	uv run starforged

test: ## Run tests with coverage
	uv run pytest

lint: ## Lint with ruff
	uv run ruff check starforged tests

format: ## Auto-format code with ruff
	uv run ruff format starforged tests
	uv run ruff check --fix starforged tests

check: lint test ## Run lint + tests

clean: ## Remove build artifacts and caches
	if exist __pycache__ rd /s /q __pycache__
	if exist .pytest_cache rd /s /q .pytest_cache
	if exist .coverage del .coverage
	if exist htmlcov rd /s /q htmlcov
	if exist dist rd /s /q dist
	if exist build rd /s /q build
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
