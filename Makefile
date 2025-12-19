.PHONY: help install dev test lint format check build clean publish publish-test

# Default target
help:
	@echo "RepliMap Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install dependencies"
	@echo "  make dev          Install with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test         Run tests"
	@echo "  make test-cov     Run tests with coverage"
	@echo "  make lint         Run linter (ruff check)"
	@echo "  make format       Format code (ruff format)"
	@echo "  make check        Run all checks (format + lint + test)"
	@echo ""
	@echo "Build & Publish:"
	@echo "  make build        Build package"
	@echo "  make clean        Clean build artifacts"
	@echo "  make publish      Publish to PyPI (requires PYPI_TOKEN)"
	@echo "  make publish-test Publish to TestPyPI (requires TEST_PYPI_TOKEN)"
	@echo ""
	@echo "Environment variables:"
	@echo "  PYPI_TOKEN        PyPI API token for publishing"
	@echo "  TEST_PYPI_TOKEN   TestPyPI API token for test publishing"

# Setup
install:
	uv sync --no-dev

dev:
	uv sync

# Development
test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ -v --cov=replimap --cov-report=term --cov-report=html

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

check: format-check lint test
	@echo "All checks passed!"

# Build & Publish
build: clean
	uv build

clean:
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

publish: build
ifndef PYPI_TOKEN
	$(error PYPI_TOKEN is not set. Export it with: export PYPI_TOKEN=pypi-xxx)
endif
	uv publish --token $(PYPI_TOKEN)

publish-test: build
ifndef TEST_PYPI_TOKEN
	$(error TEST_PYPI_TOKEN is not set. Export it with: export TEST_PYPI_TOKEN=pypi-xxx)
endif
	uv publish --publish-url https://test.pypi.org/legacy/ --token $(TEST_PYPI_TOKEN)
