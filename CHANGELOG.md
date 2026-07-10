# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.5.0...replimap-mono-v1.6.0) (2026-07-10)


### Features

* **api:** push [Stripe][MANUAL_REVIEW] to an ops-alert webhook (B-3) ([a66ea8e](https://github.com/RepliMap/replimap-mono/commit/a66ea8e2ff012134407fdb781d9880ebf5e39ac6))


### Bug Fixes

* **api:** backdate license blob nbf by 300s to tolerate client clock skew ([fa105b8](https://github.com/RepliMap/replimap-mono/commit/fa105b8e077caf440e765e787ad3f9803a306095))
* **api:** exclude free-tier plans from Path B post-checkout license lookup ([6ef4d4f](https://github.com/RepliMap/replimap-mono/commit/6ef4d4f466ededfc9dbf5fae320d60cea3044684))
* **web:** align marketing copy with shipped product and ratified positioning ([8d61856](https://github.com/RepliMap/replimap-mono/commit/8d6185677190d0f4b76ab59eaa178ad886e3d178))
* **web:** full-site accuracy pass — docs verified against CLI v0.4.11 ([56bd074](https://github.com/RepliMap/replimap-mono/commit/56bd0740349be1d97494f75db089dac86d555cb1))


### Documentation

* B-3 shipped (ops-alert webhook, needs receiver secret) + B-4 resolved in CLI repo ([f93d0df](https://github.com/RepliMap/replimap-mono/commit/f93d0dfbbe161d42f1e882d04a5b4c67758d90e5))
* checklist §1.1-§1.5 updated with 2026-07-09 verification evidence ([6610d60](https://github.com/RepliMap/replimap-mono/commit/6610d606ea478183138feb2a0f5e45ab6c68482d))
* close A-2/A-3 residuals — live-verified via Vercel prod env credentials ([81d8931](https://github.com/RepliMap/replimap-mono/commit/81d89311f90d810f026e4b1d941cc200d928b9dd))
* payment prod-hardening TODO from 2026-07-09 code inventory ([511faf2](https://github.com/RepliMap/replimap-mono/commit/511faf233608c98e27f47d5790bcf6bae80aea5f))
* record 2026-07-09 execution — A组 complete, B-1/B-2/B-5 done, deployed ([38726e1](https://github.com/RepliMap/replimap-mono/commit/38726e1e95eaee6bed15a8ffbc561549aa84f042))
* runbook state update — signing live on dev+prod; nbf leeway follow-ups ([e581a22](https://github.com/RepliMap/replimap-mono/commit/e581a22a4da2770615a70bf8d3cb314a6965fd13))

## [1.5.0](https://github.com/RepliMap/replimap-mono/compare/replimap-mono-v1.4.3...replimap-mono-v1.5.0) (2026-07-07)


### Features

* **api:** add GET /v1/checkout/session/:id/license post-payment lookup ([ffdb8b4](https://github.com/RepliMap/replimap-mono/commit/ffdb8b475bbbec401b17a720b820cb3782f87533))
* **api:** add getLicenseByUserEmailLatest helper ([1f4134e](https://github.com/RepliMap/replimap-mono/commit/1f4134ebea41473bcbdb56218377be525f7e96ba))
* **api:** add POST /v1/license/provision-community for free-tier auto-signup ([c7d71e5](https://github.com/RepliMap/replimap-mono/commit/c7d71e5d3e1a83e5338b5951670f2153367b77e6))
* **api:** add RATE_LIMIT_DISABLED env flag for local dev/e2e ([7fbff44](https://github.com/RepliMap/replimap-mono/commit/7fbff449a531e2b7c7b0d735c241b9bd56c664ed))
* **api:** extend handleCreateCheckout to support lifetime billing ([704ded8](https://github.com/RepliMap/replimap-mono/commit/704ded807d0335efb58252f134ccd93181e6d924))
* **api:** sign /v1/license/validate license_blob per Blob Format Contract v1 ([cd58f29](https://github.com/RepliMap/replimap-mono/commit/cd58f29819c91cb41d4bdb0e6861e6fb44bfb883))
* **billing:** switch to live Stripe price IDs, allow www + apex CORS, ([b39d4ac](https://github.com/RepliMap/replimap-mono/commit/b39d4ac62f131257677cd30f01f68422ef809abd))
* **payments:** harden Stripe webhook flow, add license CSPRNG, and require auth on community provisioning ([a570276](https://github.com/RepliMap/replimap-mono/commit/a5702768272a4c9d565056827c3b8dc55fe3e9cc))
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
* **dashboard:** populate device list, per-plan limits, grace days, expiry (followups [#6](https://github.com/RepliMap/replimap-mono/issues/6)/[#7](https://github.com/RepliMap/replimap-mono/issues/7)) ([2e4b6d0](https://github.com/RepliMap/replimap-mono/commit/2e4b6d02abce4829ff0686775b18d95878db733d))
* **web:** add X-Internal-Auth header to provision-community request ([8f83d6f](https://github.com/RepliMap/replimap-mono/commit/8f83d6f9d04b64f3feb9f6950d51b12f672247c8))
* **web:** force-dynamic on /checkout to fix SSG prerender of Clerk hooks ([8c846b5](https://github.com/RepliMap/replimap-mono/commit/8c846b56b79260f98243eeaebae2828663b3a531))
* **web:** guard license.fingerprints access against undefined ([7b829cd](https://github.com/RepliMap/replimap-mono/commit/7b829cdbd65cb09be00bc9ac0f5a7e20cbf09d4c))
* **webhook:** backfill billing period from subscription items, retry ([2134d8b](https://github.com/RepliMap/replimap-mono/commit/2134d8b65e7d236a114605d0c71093f156013612))
* **webhook:** resolve customer email via customer_details fallback, refuse to guess plan on unresolvable lifetime payments ([3164b1b](https://github.com/RepliMap/replimap-mono/commit/3164b1bbafa674dd3fed161b5bae64dae160be53))
* **webhook:** resolve invoice subscription id via parent.subscription_details on API &gt;=2025-03-31 ([7640f4a](https://github.com/RepliMap/replimap-mono/commit/7640f4a39491cfa599086b53f42cc74774fed11f))
* **webhook:** resolve refunded charges to licenses via payment_intent, always create customers on lifetime checkout ([06e8111](https://github.com/RepliMap/replimap-mono/commit/06e81116b62509706c21007dcb69036efb2b496c))
* **web:** link Clerk user to license via email, auto-provision community ([30d088f](https://github.com/RepliMap/replimap-mono/commit/30d088f068391b828f949371e3686beba23d3caa))
* **web:** move license fetch/provision to client-side (Cloudflare Bot Fight Mode blocks Vercel SSR requests) ([e6bd1c9](https://github.com/RepliMap/replimap-mono/commit/e6bd1c9f820b58ff4cae61631bfd13c88bb9d9cb))
* **web:** pass license_key as query param to /v1/me/license ([1051aaa](https://github.com/RepliMap/replimap-mono/commit/1051aaa860838207fc156ca596eb72c7069cd144))


### Documentation

* add commercial flow testing guide ([a1db780](https://github.com/RepliMap/replimap-mono/commit/a1db780a52331396e1bac88c4b8ece21348c1068))
* add production deployment checklist ([3eb9a03](https://github.com/RepliMap/replimap-mono/commit/3eb9a03485422645bd8e1ab3d717a35d067ff2cd))
* add production rollback playbook + follow-ups tracker ([cb38f0e](https://github.com/RepliMap/replimap-mono/commit/cb38f0eb97e0bec90f51b239aff2593bf9a79f5f))
* add repo CLAUDE.md (ops landmines + doc index), sync status across docs ([5a44b75](https://github.com/RepliMap/replimap-mono/commit/5a44b75f1d0c0c494df2ea27fe5954a7ae6580ee))
* complete A6 e2e dev validation log (items 9 + cleanup, D1 restored to baseline) ([b89cf98](https://github.com/RepliMap/replimap-mono/commit/b89cf989444836ca43938d84ed076891709c62cb))
* correct §1.3 — prod D1 needs ledger alignment, not migration apply ([a145d42](https://github.com/RepliMap/replimap-mono/commit/a145d42f82555c697c8dc5d59248b0252e7c3fb9))
* deploy runbook for Ed25519 license-blob signing go-live (Phase 4) ([611f106](https://github.com/RepliMap/replimap-mono/commit/611f106f02038507a0270cc27d2f5cbe110e0a74))
* document commercial flow e2e harness and update README ([7ad9b2e](https://github.com/RepliMap/replimap-mono/commit/7ad9b2e10be8232fbfd5cb7f509a9dc0ea652300))
* mark §5 rollout complete (prod deployed f62bd94c) ([cbdc51d](https://github.com/RepliMap/replimap-mono/commit/cbdc51db956ac55c58f7df09133d203331e86233))
* mark checklist §1.5 (post-deploy smoke test) done, link live e2e evidence ([61fb196](https://github.com/RepliMap/replimap-mono/commit/61fb1965b3c2042d306165e91590edc565b7a5a7))
* mark followups [#6](https://github.com/RepliMap/replimap-mono/issues/6)/[#7](https://github.com/RepliMap/replimap-mono/issues/7) deployed to prod (API 90bfc4ca), CI green ([04b86eb](https://github.com/RepliMap/replimap-mono/commit/04b86ebf34de4a89c9866af5f24a26b450a45779))
* mark followups [#6](https://github.com/RepliMap/replimap-mono/issues/6)/[#7](https://github.com/RepliMap/replimap-mono/issues/7) fixed; add [#8](https://github.com/RepliMap/replimap-mono/issues/8) (license key as URL query param — ([2e4b6d0](https://github.com/RepliMap/replimap-mono/commit/2e4b6d02abce4829ff0686775b18d95878db733d))
* record first live production end-to-end smoke test (payment + refund/cancel) ([0a098f4](https://github.com/RepliMap/replimap-mono/commit/0a098f4029d13f47e6e4eecba4db6be3bffa5b3c))

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
