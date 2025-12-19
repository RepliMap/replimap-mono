.PHONY: help install dev test lint format check build clean publish publish-test version bump-patch bump-minor bump-major

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
	@echo "Version Management:"
	@echo "  make version      Show current version"
	@echo "  make bump-patch   Bump patch version (0.1.0 -> 0.1.1)"
	@echo "  make bump-minor   Bump minor version (0.1.0 -> 0.2.0)"
	@echo "  make bump-major   Bump major version (0.1.0 -> 1.0.0)"
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

# Version Management (using hatch)
version:
	@grep -Po '(?<=__version__ = ")[^"]*' replimap/__init__.py

bump-patch:
	@echo "Current version: $$(grep -Po '(?<=__version__ = ")[^"]*' replimap/__init__.py)"
	@python3 -c "import re; \
		f = open('replimap/__init__.py', 'r'); content = f.read(); f.close(); \
		v = re.search(r'__version__ = \"(\d+)\.(\d+)\.(\d+)\"', content); \
		new_v = f'{v.group(1)}.{v.group(2)}.{int(v.group(3))+1}'; \
		content = re.sub(r'__version__ = \"[^\"]+\"', f'__version__ = \"{new_v}\"', content); \
		f = open('replimap/__init__.py', 'w'); f.write(content); f.close(); \
		print(f'Bumped to: {new_v}')"

bump-minor:
	@echo "Current version: $$(grep -Po '(?<=__version__ = ")[^"]*' replimap/__init__.py)"
	@python3 -c "import re; \
		f = open('replimap/__init__.py', 'r'); content = f.read(); f.close(); \
		v = re.search(r'__version__ = \"(\d+)\.(\d+)\.(\d+)\"', content); \
		new_v = f'{v.group(1)}.{int(v.group(2))+1}.0'; \
		content = re.sub(r'__version__ = \"[^\"]+\"', f'__version__ = \"{new_v}\"', content); \
		f = open('replimap/__init__.py', 'w'); f.write(content); f.close(); \
		print(f'Bumped to: {new_v}')"

bump-major:
	@echo "Current version: $$(grep -Po '(?<=__version__ = ")[^"]*' replimap/__init__.py)"
	@python3 -c "import re; \
		f = open('replimap/__init__.py', 'r'); content = f.read(); f.close(); \
		v = re.search(r'__version__ = \"(\d+)\.(\d+)\.(\d+)\"', content); \
		new_v = f'{int(v.group(1))+1}.0.0'; \
		content = re.sub(r'__version__ = \"[^\"]+\"', f'__version__ = \"{new_v}\"', content); \
		f = open('replimap/__init__.py', 'w'); f.write(content); f.close(); \
		print(f'Bumped to: {new_v}')"

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
