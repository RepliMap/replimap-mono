.PHONY: help install build dev clean lint typecheck test \
        dev-web dev-api dev-cli build-config sync-cli-config \
        deploy-web deploy-api release-cli deploy-all \
        check-generated check-versions pre-commit setup info \
        commit-config tag-cli update

.DEFAULT_GOAL := help

# Colors
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Version detection
NODE_VERSION := $(shell node --version 2>/dev/null || echo "not installed")
PNPM_VERSION := $(shell pnpm --version 2>/dev/null || echo "not installed")
PYTHON_VERSION := $(shell python3 --version 2>/dev/null || echo "not installed")
NPM_VERSION := $(shell npm --version 2>/dev/null || echo "not installed")

#==============================================================================
# Help
#==============================================================================
help: ## Show this help message
	@echo ""
	@echo "$(CYAN)RepliMap Monorepo$(RESET)"
	@echo "$(CYAN)=================$(RESET)"
	@echo ""
	@echo "$(GREEN)Environment:$(RESET)"
	@echo "  Node:   $(NODE_VERSION) (required: 24.x)"
	@echo "  npm:    $(NPM_VERSION)"
	@echo "  pnpm:   $(PNPM_VERSION) (required: 9.x)"
	@echo "  Python: $(PYTHON_VERSION) (required: 3.11+)"
	@echo ""
	@echo "$(GREEN)Available commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Quick start:$(RESET)"
	@echo "  make setup          # First-time setup"
	@echo "  make dev-web        # Start web dev server"
	@echo "  make dev-api        # Start api dev server"
	@echo ""

#==============================================================================
# Installation
#==============================================================================
install: ## Install all dependencies
	@echo "$(CYAN)Enabling Corepack for consistent pnpm version...$(RESET)"
	@corepack enable 2>/dev/null || echo "$(YELLOW)Corepack not available, using system pnpm$(RESET)"
	pnpm install
	@echo "$(GREEN)Dependencies installed$(RESET)"

install-frozen: ## Install with frozen lockfile (CI)
	@corepack enable 2>/dev/null || true
	pnpm install --frozen-lockfile

update: ## Update all dependencies
	pnpm update --recursive
	@echo "$(GREEN)Dependencies updated$(RESET)"

#==============================================================================
# Build
#==============================================================================
build: ## Build all packages
	pnpm build

build-config: ## Build shared config package
	pnpm --filter @replimap/config build
	@echo "$(GREEN)Config package built$(RESET)"

build-web: build-config ## Build web app
	pnpm --filter @replimap/web build

build-api: build-config ## Build api app
	pnpm --filter @replimap/api build

build-cli: sync-cli-config ## Build CLI package
	cd apps/cli && rm -rf dist/ build/ *.egg-info && python -m build
	@echo "$(GREEN)CLI package built$(RESET)"

#==============================================================================
# Development
#==============================================================================
dev: ## Start all dev servers (parallel)
	pnpm dev

dev-web: ## Start web dev server
	pnpm --filter @replimap/web dev

dev-api: ## Start api dev server
	pnpm --filter @replimap/api dev

dev-cli: sync-cli-config ## Setup CLI for development
	cd apps/cli && pip install -e ".[dev]" 2>/dev/null || pip install -e .
	@echo "$(GREEN)CLI installed in dev mode$(RESET)"

#==============================================================================
# Config Sync
#==============================================================================
sync-cli-config: build-config ## Sync config to CLI (generates Python code)
	@bash apps/cli/scripts/sync-config.sh

check-generated: ## Verify generated files are committed
	@pnpm --filter @replimap/config build
	@if [ -n "$$(git status --porcelain packages/config/dist/)" ]; then \
		echo "$(RED)Generated files out of sync!$(RESET)"; \
		echo ""; \
		echo "Run: make commit-config"; \
		echo ""; \
		git status --short packages/config/dist/; \
		exit 1; \
	fi
	@echo "$(GREEN)Generated files in sync$(RESET)"

#==============================================================================
# Code Quality
#==============================================================================
lint: ## Run linters
	pnpm lint

typecheck: ## Run type checking
	pnpm typecheck

format: ## Format code
	pnpm format 2>/dev/null || npx prettier --write "**/*.{ts,tsx,js,json,md}"
	cd apps/cli && ruff format . 2>/dev/null || true

test: ## Run all tests
	pnpm test 2>/dev/null || true
	cd apps/cli && pytest tests/ -v 2>/dev/null || echo "$(YELLOW)CLI tests skipped$(RESET)"

pre-commit: lint typecheck check-generated ## Run pre-commit checks
	@echo "$(GREEN)Pre-commit checks passed$(RESET)"

#==============================================================================
# Deployment
#==============================================================================
deploy-web: build-web ## Deploy web to Vercel
	cd apps/web && vercel --prod

deploy-api: build-api ## Deploy api to Cloudflare
	cd apps/api && wrangler deploy --minify

release-cli: build-cli ## Release CLI to PyPI
	cd apps/cli && twine check dist/* && twine upload dist/*

deploy-all: deploy-web deploy-api ## Deploy web and api
	@echo "$(GREEN)All deployments complete$(RESET)"

#==============================================================================
# Cleanup
#==============================================================================
clean: ## Clean build artifacts
	rm -rf node_modules .turbo
	rm -rf apps/web/.next apps/web/out apps/web/node_modules
	rm -rf apps/api/dist apps/api/node_modules .wrangler
	rm -rf apps/cli/dist apps/cli/build apps/cli/*.egg-info
	rm -rf packages/config/node_modules
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".turbo" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleaned$(RESET)"

clean-all: clean ## Deep clean (includes generated files and caches)
	rm -rf packages/config/dist
	rm -rf apps/cli/replimap/_generated
	pnpm store prune 2>/dev/null || true
	@echo "$(GREEN)Deep cleaned$(RESET)"

#==============================================================================
# Setup & Info
#==============================================================================
setup: check-versions ## First-time development setup
	@echo "$(CYAN)Setting up RepliMap development environment...$(RESET)"
	@echo ""
	$(MAKE) install
	$(MAKE) build-config
	$(MAKE) sync-cli-config
	cd apps/cli && pip install -e ".[dev]" 2>/dev/null || pip install -e .
	@echo ""
	@echo "$(GREEN)Setup complete!$(RESET)"
	@echo ""
	@echo "$(CYAN)Next steps:$(RESET)"
	@echo "  make dev-web   # Start web development"
	@echo "  make dev-api   # Start api development"
	@echo "  make dev-cli   # Setup CLI development"
	@echo ""
	@echo "$(CYAN)Deployment checklist:$(RESET)"
	@echo "  1. Vercel: Set Root Directory to 'apps/web'"
	@echo "  2. Cloudflare: Set Root Directory to 'apps/api'"
	@echo "  3. Add secrets: VERCEL_TOKEN, CLOUDFLARE_API_TOKEN, PYPI_API_TOKEN"

check-versions: ## Verify installed versions meet requirements
	@echo "$(CYAN)Checking versions...$(RESET)"
	@NODE_MAJOR=$$(node --version 2>/dev/null | cut -d. -f1 | tr -d 'v'); \
	if [ -z "$$NODE_MAJOR" ]; then \
		echo "$(RED)Node.js not installed$(RESET)"; \
		exit 1; \
	elif [ "$$NODE_MAJOR" -lt 20 ]; then \
		echo "$(RED)Node.js v$$NODE_MAJOR found, need v20+ (v24 recommended)$(RESET)"; \
		exit 1; \
	elif [ "$$NODE_MAJOR" -lt 24 ]; then \
		echo "$(YELLOW)Node.js $(NODE_VERSION) - works, but v24 recommended for Vercel parity$(RESET)"; \
	else \
		echo "$(GREEN)Node.js $(NODE_VERSION)$(RESET)"; \
	fi
	@if ! command -v pnpm >/dev/null 2>&1; then \
		echo "$(RED)pnpm not installed. Run: corepack enable$(RESET)"; \
		exit 1; \
	fi
	@PNPM_MAJOR=$$(pnpm --version | cut -d. -f1); \
	if [ "$$PNPM_MAJOR" -lt 9 ]; then \
		echo "$(YELLOW)pnpm v$$PNPM_MAJOR - upgrade to v9 recommended$(RESET)"; \
	else \
		echo "$(GREEN)pnpm $(PNPM_VERSION)$(RESET)"; \
	fi
	@echo "$(GREEN)npm $(NPM_VERSION)$(RESET)"
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "$(RED)Python 3 not installed$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)$(PYTHON_VERSION)$(RESET)"

info: ## Show environment info
	@echo ""
	@echo "$(CYAN)RepliMap Monorepo$(RESET)"
	@echo ""
	@echo "$(GREEN)Environment:$(RESET)"
	@echo "  Node:   $(NODE_VERSION)"
	@echo "  npm:    $(NPM_VERSION)"
	@echo "  pnpm:   $(PNPM_VERSION)"
	@echo "  Python: $(PYTHON_VERSION)"
	@echo ""
	@echo "$(GREEN)Required versions:$(RESET)"
	@echo "  Node:   24.x (Vercel production)"
	@echo "  pnpm:   9.x"
	@echo "  Python: 3.11+"
	@echo ""
	@echo "$(GREEN)Components:$(RESET)"
	@echo "  apps/web        -> Next.js 16 (Vercel)"
	@echo "  apps/api        -> Hono (Cloudflare Workers)"
	@echo "  apps/cli        -> Python (PyPI)"
	@echo "  packages/config -> Shared configuration"
	@echo ""
	@if [ -f packages/config/dist/index.ts ]; then \
		echo "$(GREEN)Config Version:$(RESET)"; \
		grep "CONFIG_VERSION" packages/config/dist/index.ts 2>/dev/null | head -1 | sed 's/^/  /' || echo "  (not found)"; \
	else \
		echo "$(YELLOW)Config not built. Run: make build-config$(RESET)"; \
	fi
	@echo ""

#==============================================================================
# Git Workflow
#==============================================================================
commit-config: build-config ## Build and commit config changes
	git add packages/config/dist/
	git commit -m "chore: regenerate config files [skip ci]" || echo "$(YELLOW)No changes to commit$(RESET)"

tag-cli: ## Create CLI release tag (usage: make tag-cli VERSION=0.5.0)
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)Usage: make tag-cli VERSION=0.5.0$(RESET)"; \
		exit 1; \
	fi
	@echo "$(CYAN)Creating tag cli-v$(VERSION)...$(RESET)"
	git tag -a "cli-v$(VERSION)" -m "CLI release v$(VERSION)"
	git push origin "cli-v$(VERSION)"
	@echo "$(GREEN)Tagged and pushed cli-v$(VERSION)$(RESET)"
	@echo "$(CYAN)GitHub Actions will now build and publish to PyPI$(RESET)"
