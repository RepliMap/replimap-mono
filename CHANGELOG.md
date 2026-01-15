# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0 (2026-01-15)


### Bug Fixes

* sync pnpm-lock.yaml with apps/api/package.json ([1b3e3ac](https://github.com/RepliMap/replimap-mono/commit/1b3e3ac72f4c67f187d0a909bc927e8c1485f955))
* sync pnpm-lock.yaml with apps/api/package.json ([75477c9](https://github.com/RepliMap/replimap-mono/commit/75477c91712ffdade636445622da800ec6ac830f))

## [Unreleased]

### Added
- Monorepo structure with Turborepo
- Shared configuration package
- GitHub Actions CI/CD pipelines
- Comprehensive Makefile for development commands
- Cross-platform development support (Linux, macOS, Windows/WSL)

### Changed
- Migrated from multi-repo to monorepo architecture
- Removed CLI from public repo (moved to private repo)

## [0.5.0] - 2025-01-15

### Added
- Initial monorepo release
- Web dashboard (Next.js 16)
- API backend (Hono + Cloudflare Workers)

### Security
- Integrated CodeQL scanning
- Added Dependabot for automated updates

---

[Unreleased]: https://github.com/RepliMap/replimap-mono/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/RepliMap/replimap-mono/releases/tag/v0.5.0
