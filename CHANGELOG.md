# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.4.3...replimap-mono-v1.5.0) (2026-04-19)


### Features

* **api:** add GET /v1/checkout/session/:id/license post-payment lookup ([ffdb8b4](https://github.com/RepliMap/replimap-mono/commit/ffdb8b475bbbec401b17a720b820cb3782f87533))
* **api:** add getLicenseByUserEmailLatest helper ([1f4134e](https://github.com/RepliMap/replimap-mono/commit/1f4134ebea41473bcbdb56218377be525f7e96ba))
* **api:** add POST /v1/license/provision-community for free-tier auto-signup ([c7d71e5](https://github.com/RepliMap/replimap-mono/commit/c7d71e5d3e1a83e5338b5951670f2153367b77e6))
* **api:** add RATE_LIMIT_DISABLED env flag for local dev/e2e ([7fbff44](https://github.com/RepliMap/replimap-mono/commit/7fbff449a531e2b7c7b0d735c241b9bd56c664ed))
* **api:** extend handleCreateCheckout to support lifetime billing ([704ded8](https://github.com/RepliMap/replimap-mono/commit/704ded807d0335efb58252f134ccd93181e6d924))
* **web:** add cta-links helper with checkoutHref/freeSignupHref ([a276fbf](https://github.com/RepliMap/replimap-mono/commit/a276fbf96c743466ce30be196e721ac45fdb2064))
* **web:** add getCheckoutLicense + provisionCommunityLicense api clients ([3e18dba](https://github.com/RepliMap/replimap-mono/commit/3e18dba37a51adb7f91f3b222dffa3b4802233f7))
* **web:** poll and display license key on /checkout/success page ([06ba075](https://github.com/RepliMap/replimap-mono/commit/06ba075cc399642fbfcb4cabfbe403a5595354a7))
* **web:** route header + bottom CTAs to sign-up instead of Tally ([aee075c](https://github.com/RepliMap/replimap-mono/commit/aee075c9b05f3de057c64422e76dee6d6a1eb402))
* **web:** route hero 'Get Started Free' to Clerk sign-up ([d8226e6](https://github.com/RepliMap/replimap-mono/commit/d8226e6c9c82d6378b329e01f93a9cf1e8b582b0))
* **web:** route pricing CTAs to checkout + support lifetime in /checkout ([556db81](https://github.com/RepliMap/replimap-mono/commit/556db819e6f81b45e6b134b0852174cf489d32d7))


### Bug Fixes

* **api:** add migration to bootstrap Drizzle schema on local D1 ([aa29216](https://github.com/RepliMap/replimap-mono/commit/aa29216bd7410de1edb72df95a23d286563e2db0))
* **api:** guard checkout-license route so it doesn't swallow all GET requests ([6aa25dc](https://github.com/RepliMap/replimap-mono/commit/6aa25dc329fbdc8269fefeb13aa4b29e291b4d43))
* **api:** self-heal subscription.created when user not yet in DB ([df74f99](https://github.com/RepliMap/replimap-mono/commit/df74f99c851e18ec90183a274c245b108586ff25))
* **web:** link Clerk user to license via email, auto-provision community ([30d088f](https://github.com/RepliMap/replimap-mono/commit/30d088f068391b828f949371e3686beba23d3caa))
* **web:** pass license_key as query param to /v1/me/license ([1051aaa](https://github.com/RepliMap/replimap-mono/commit/1051aaa860838207fc156ca596eb72c7069cd144))


### Documentation

* add commercial flow testing guide ([a1db780](https://github.com/RepliMap/replimap-mono/commit/a1db780a52331396e1bac88c4b8ece21348c1068))
* add production rollback playbook + follow-ups tracker ([cb38f0e](https://github.com/RepliMap/replimap-mono/commit/cb38f0eb97e0bec90f51b239aff2593bf9a79f5f))
* document commercial flow e2e harness and update README ([7ad9b2e](https://github.com/RepliMap/replimap-mono/commit/7ad9b2e10be8232fbfd5cb7f509a9dc0ea652300))

## [1.4.3](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.4.2...replimap-mono-v1.4.3) (2026-01-23)


### Bug Fixes

* remove broken footer links and redirect to GitHub ([ae36c39](https://github.com/RepliMap/replimap-mono/commit/ae36c3942f6959da6ec6cfd636e969d328a2f41f))
* remove broken footer links and redirect to GitHub ([336c4af](https://github.com/RepliMap/replimap-mono/commit/336c4af69a1be60d3355fcf0635b3db49ba402a8))
* update Changelog link to CHANGELOG.md ([7f468ac](https://github.com/RepliMap/replimap-mono/commit/7f468ac7b6a5a84af0aa8d065e58605f1d005bb6))

## [1.4.2](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.4.1...replimap-mono-v1.4.2) (2026-01-22)


### Bug Fixes

* add Firefox compatibility for CSS colors, scrollbar, and backdrop-filter ([d04ff5c](https://github.com/RepliMap/replimap-mono/commit/d04ff5c462cebbc675cd09b2cdf6c8de51cbde08))
* add Firefox compatibility for CSS colors, scrollbar, and backdrop-filter ([49249f7](https://github.com/RepliMap/replimap-mono/commit/49249f78b6dcfc68ba277b2a67915e0a03e643ee))

## [1.4.1](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.4.0...replimap-mono-v1.4.1) (2026-01-22)


### Bug Fixes

* correct FUNDING.yml pricing link and remove enterprise ([b23a6cb](https://github.com/RepliMap/replimap-mono/commit/b23a6cba964076de510cc9d10a1feb3630f6fff2))
* correct FUNDING.yml pricing link and remove enterprise ([c6b9176](https://github.com/RepliMap/replimap-mono/commit/c6b9176791fde8328fe880cdf9a512d302fd8477))

## [1.4.0](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.3.2...replimap-mono-v1.4.0) (2026-01-22)


### Features

* **web:** update GitHub links to use public community repo ([a6072a6](https://github.com/RepliMap/replimap-mono/commit/a6072a6982e55c8757457c217da2181ce9c62d68))
* **web:** update GitHub links to use public community repo ([c1e2d86](https://github.com/RepliMap/replimap-mono/commit/c1e2d860721cfa7b055d8c1edb5082e35161e40c))

## [1.3.2](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.3.1...replimap-mono-v1.3.2) (2026-01-20)


### Bug Fixes

* **web:** bypass Clerk middleware for sitemap.xml and robots.txt ([02eb8fc](https://github.com/RepliMap/replimap-mono/commit/02eb8fcf2a706ee50306383217b3d943d04d2098))
* **web:** bypass Clerk middleware for sitemap.xml and robots.txt ([1c0dc38](https://github.com/RepliMap/replimap-mono/commit/1c0dc38d4e20118410bf6ee23295e5a482b57d0e))

## [1.3.1](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.3.0...replimap-mono-v1.3.1) (2026-01-20)


### Bug Fixes

* **web:** resolve sitemap and middleware issues for Vercel deployment ([8b53d25](https://github.com/RepliMap/replimap-mono/commit/8b53d25384064f2b1059632e765ccb6006fcee8e))
* **web:** resolve sitemap and middleware issues for Vercel deployment ([e22d8d6](https://github.com/RepliMap/replimap-mono/commit/e22d8d6f9611cc7170da52ade87f651c4d4cea4d))

## [1.3.0](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.2.1...replimap-mono-v1.3.0) (2026-01-20)


### Features

* **web:** fix critical SEO issues and add AI-friendly infrastructure ([72f0c2b](https://github.com/RepliMap/replimap-mono/commit/72f0c2b385ec7be74853a829e3f237aada3de81c))
* **web:** fix critical SEO issues and add AI-friendly infrastructure ([cc61b9e](https://github.com/RepliMap/replimap-mono/commit/cc61b9e521130b21a447ac10880170ccf7a432d2))
* **web:** implement SEO improvements with SSOT pricing and dynamic OG images ([2afbe41](https://github.com/RepliMap/replimap-mono/commit/2afbe41ad9c9ba38df14b505fc3c52ee78f49278))


### Bug Fixes

* **web:** remove docs opengraph-image incompatible with catch-all route ([033dab9](https://github.com/RepliMap/replimap-mono/commit/033dab901ddfd8a6b6be1461149e5054e47f4fcc))

## [1.2.1](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.2.0...replimap-mono-v1.2.1) (2026-01-20)


### Bug Fixes

* **api:** use PKCS8/SPKI format for Ed25519 keys ([37d90af](https://github.com/RepliMap/replimap-mono/commit/37d90af14df7daae981a888e142301df56e2c4e5))
* **api:** use PKCS8/SPKI format for Ed25519 keys ([904d9a0](https://github.com/RepliMap/replimap-mono/commit/904d9a0eecee2c382a4f2a04662d06454a967a20))

## [1.2.0](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.1.2...replimap-mono-v1.2.0) (2026-01-20)


### Features

* **api:** implement backend license system for CLI Phase 3 ([4030a1b](https://github.com/RepliMap/replimap-mono/commit/4030a1bd5d5efcf5bf18aba7f0325f9d6e7d6bd2))
* **api:** implement backend/frontend license system for CLI Phase 3 ([41abb0c](https://github.com/RepliMap/replimap-mono/commit/41abb0c49f0a0765c599fe6c032de8686992d36e))
* **web:** implement license dashboard for CLI Phase 3 ([bfb822a](https://github.com/RepliMap/replimap-mono/commit/bfb822a9e20edc73fb9641467925282f567d2c2e))


### Bug Fixes

* **api:** SQLite cannot add UNIQUE column directly ([5fb172a](https://github.com/RepliMap/replimap-mono/commit/5fb172ae63667b1a45087bb29f59dcc7a18d7ea2))

## [1.1.2](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.1.1...replimap-mono-v1.1.2) (2026-01-16)


### Bug Fixes

* **api:** update billing handler to use v4.0 plan names ([18417ac](https://github.com/RepliMap/replimap-mono/commit/18417ac234c62273f2440c239a67073d8a40a0c9))


### Refactoring

* **api:** remove legacy plan names and fix test mocks ([ae411c1](https://github.com/RepliMap/replimap-mono/commit/ae411c103871656157736ea7ecf7284bc9caa160))

## [1.1.1](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.1.0...replimap-mono-v1.1.1) (2026-01-16)


### Documentation

* update documentation for v4.0 pricing tiers ([d5d341a](https://github.com/RepliMap/replimap-mono/commit/d5d341a4f8293fd9579d350ade0798f5a914b4d8))
* update documentation for v4.0 pricing tiers ([44a1c8f](https://github.com/RepliMap/replimap-mono/commit/44a1c8f8281e7f7c651b9e9da919e847cfcd3f72))

## [1.1.0](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.0.2...replimap-mono-v1.1.0) (2026-01-15)


### Features

* **pricing:** implement v4.0 pricing transformation ([8e59f51](https://github.com/RepliMap/replimap-mono/commit/8e59f510b7cec4ede843accaddf7c3e0d96bf1dd))
* **pricing:** implement v4.0 pricing transformation ([114b844](https://github.com/RepliMap/replimap-mono/commit/114b844b07ace38c350cc8126150eb2bd8816e56))

## [1.0.2](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.0.1...replimap-mono-v1.0.2) (2026-01-15)


### Bug Fixes

* **ci:** remove redundant Vercel deploy workflow ([bfcdcf4](https://github.com/RepliMap/replimap-mono/commit/bfcdcf4115c28b725661e3b7bfbff0fa1db18b9d))
* **ci:** remove redundant Vercel deploy workflow ([ff0d312](https://github.com/RepliMap/replimap-mono/commit/ff0d3124f7e676e94d0300db54af479e883af2d6))

## [1.0.1](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.0.0...replimap-mono-v1.0.1) (2026-01-15)


### Bug Fixes

* **ci:** remove duplicate pnpm version specification ([791c0f3](https://github.com/RepliMap/replimap-mono/commit/791c0f3a926ad36f6c34d0a0bf747194a9a20cca))
* **ci:** remove duplicate pnpm version specification ([cfa7b36](https://github.com/RepliMap/replimap-mono/commit/cfa7b361a8e20f258abb27c1c4ef27d84c707645))

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
