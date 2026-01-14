# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Monorepo structure with Turborepo
- Shared configuration package with cross-language support
- GitHub Actions CI/CD pipelines
- OIDC-based PyPI publishing
- Comprehensive Makefile for development commands
- Cross-platform development support (Linux, macOS, Windows/WSL)

### Changed
- Migrated from multi-repo to monorepo architecture

## [0.5.0] - 2025-01-15

### Added
- Initial monorepo release
- Web dashboard (Next.js 16)
- API backend (Hono + Cloudflare Workers)
- CLI tool (Python 3.11+)

### Security
- Integrated CodeQL scanning
- Added Dependabot for automated updates
- Implemented OIDC Trusted Publishing for PyPI

---

[Unreleased]: https://github.com/RepliMap/replimap-mono/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/RepliMap/replimap-mono/releases/tag/v0.5.0
