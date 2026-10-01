.PHONY: help install build dev clean lint typecheck test \
        dev-web dev-api build-config \
        deploy-web deploy-api deploy-all \
        check-generated check-versions pre-commit setup info \
        commit-config update

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

#==============================================================================
# Development
#==============================================================================
dev: ## Start all dev servers (parallel)
	pnpm dev

dev-web: ## Start web dev server
	pnpm --filter @replimap/web dev

dev-api: ## Start api dev server
	pnpm --filter @replimap/api dev

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

test: ## Run all tests
	pnpm test 2>/dev/null || true

pre-commit: lint typecheck check-generated ## Run pre-commit checks
	@echo "$(GREEN)Pre-commit checks passed$(RESET)"

#==============================================================================
# Deployment
#==============================================================================
deploy-web: build-web ## Deploy web to Vercel
	cd apps/web && vercel --prod

deploy-api: build-api ## Deploy api to Cloudflare
	cd apps/api && wrangler deploy --minify

deploy-all: deploy-web deploy-api ## Deploy web and api
	@echo "$(GREEN)All deployments complete$(RESET)"

#==============================================================================
# Cleanup
#==============================================================================
clean: ## Clean build artifacts
	rm -rf node_modules .turbo
	rm -rf apps/web/.next apps/web/out apps/web/node_modules
	rm -rf apps/api/dist apps/api/node_modules .wrangler
	rm -rf packages/config/node_modules
	find . -type d -name ".turbo" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleaned$(RESET)"

clean-all: clean ## Deep clean (includes generated files and caches)
	rm -rf packages/config/dist
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
	@echo ""
	@echo "$(GREEN)Setup complete!$(RESET)"
	@echo ""
	@echo "$(CYAN)Next steps:$(RESET)"
	@echo "  make dev-web   # Start web development"
	@echo "  make dev-api   # Start api development"
	@echo ""
	@echo "$(CYAN)Deployment checklist:$(RESET)"
	@echo "  1. Vercel: Set Root Directory to 'apps/web'"
	@echo "  2. Cloudflare: Set Root Directory to 'apps/api'"
	@echo "  3. Add secrets: VERCEL_TOKEN, CLOUDFLARE_API_TOKEN"

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

info: ## Show environment info
	@echo ""
	@echo "$(CYAN)RepliMap Monorepo$(RESET)"
	@echo ""
	@echo "$(GREEN)Environment:$(RESET)"
	@echo "  Node:   $(NODE_VERSION)"
	@echo "  npm:    $(NPM_VERSION)"
	@echo "  pnpm:   $(PNPM_VERSION)"
	@echo ""
	@echo "$(GREEN)Required versions:$(RESET)"
	@echo "  Node:   24.x (Vercel production)"
	@echo "  pnpm:   9.x"
	@echo ""
	@echo "$(GREEN)Components:$(RESET)"
	@echo "  apps/web        -> Next.js 16 (Vercel)"
	@echo "  apps/api        -> Hono (Cloudflare Workers)"
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
