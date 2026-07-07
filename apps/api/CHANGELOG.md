# Changelog

## [1.3.0](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.2.8...replimap-api-v1.3.0) (2026-07-07)


### Features

* **api:** add GET /v1/checkout/session/:id/license post-payment lookup ([ffdb8b4](https://github.com/RepliMap/replimap-mono/commit/ffdb8b475bbbec401b17a720b820cb3782f87533))
* **api:** add getLicenseByUserEmailLatest helper ([1f4134e](https://github.com/RepliMap/replimap-mono/commit/1f4134ebea41473bcbdb56218377be525f7e96ba))
* **api:** add POST /v1/license/provision-community for free-tier auto-signup ([c7d71e5](https://github.com/RepliMap/replimap-mono/commit/c7d71e5d3e1a83e5338b5951670f2153367b77e6))
* **api:** add RATE_LIMIT_DISABLED env flag for local dev/e2e ([7fbff44](https://github.com/RepliMap/replimap-mono/commit/7fbff449a531e2b7c7b0d735c241b9bd56c664ed))
* **api:** extend handleCreateCheckout to support lifetime billing ([704ded8](https://github.com/RepliMap/replimap-mono/commit/704ded807d0335efb58252f134ccd93181e6d924))
* **api:** sign /v1/license/validate license_blob per Blob Format Contract v1 ([cd58f29](https://github.com/RepliMap/replimap-mono/commit/cd58f29819c91cb41d4bdb0e6861e6fb44bfb883))
* **billing:** switch to live Stripe price IDs, allow www + apex CORS, ([b39d4ac](https://github.com/RepliMap/replimap-mono/commit/b39d4ac62f131257677cd30f01f68422ef809abd))
* **payments:** harden Stripe webhook flow, add license CSPRNG, and require auth on community provisioning ([a570276](https://github.com/RepliMap/replimap-mono/commit/a5702768272a4c9d565056827c3b8dc55fe3e9cc))


### Bug Fixes

* **api:** add migration to bootstrap Drizzle schema on local D1 ([aa29216](https://github.com/RepliMap/replimap-mono/commit/aa29216bd7410de1edb72df95a23d286563e2db0))
* **api:** guard checkout-license route so it doesn't swallow all GET requests ([6aa25dc](https://github.com/RepliMap/replimap-mono/commit/6aa25dc329fbdc8269fefeb13aa4b29e291b4d43))
* **api:** self-heal subscription.created when user not yet in DB ([df74f99](https://github.com/RepliMap/replimap-mono/commit/df74f99c851e18ec90183a274c245b108586ff25))
* **dashboard:** populate device list, per-plan limits, grace days, expiry (followups [#6](https://github.com/RepliMap/replimap-mono/issues/6)/[#7](https://github.com/RepliMap/replimap-mono/issues/7)) ([2e4b6d0](https://github.com/RepliMap/replimap-mono/commit/2e4b6d02abce4829ff0686775b18d95878db733d))
* **web:** add X-Internal-Auth header to provision-community request ([8f83d6f](https://github.com/RepliMap/replimap-mono/commit/8f83d6f9d04b64f3feb9f6950d51b12f672247c8))
* **webhook:** backfill billing period from subscription items, retry ([2134d8b](https://github.com/RepliMap/replimap-mono/commit/2134d8b65e7d236a114605d0c71093f156013612))
* **webhook:** resolve customer email via customer_details fallback, refuse to guess plan on unresolvable lifetime payments ([3164b1b](https://github.com/RepliMap/replimap-mono/commit/3164b1bbafa674dd3fed161b5bae64dae160be53))
* **webhook:** resolve invoice subscription id via parent.subscription_details on API &gt;=2025-03-31 ([7640f4a](https://github.com/RepliMap/replimap-mono/commit/7640f4a39491cfa599086b53f42cc74774fed11f))
* **webhook:** resolve refunded charges to licenses via payment_intent, always create customers on lifetime checkout ([06e8111](https://github.com/RepliMap/replimap-mono/commit/06e81116b62509706c21007dcb69036efb2b496c))
* **web:** move license fetch/provision to client-side (Cloudflare Bot Fight Mode blocks Vercel SSR requests) ([e6bd1c9](https://github.com/RepliMap/replimap-mono/commit/e6bd1c9f820b58ff4cae61631bfd13c88bb9d9cb))


### Documentation

* mark followups [#6](https://github.com/RepliMap/replimap-mono/issues/6)/[#7](https://github.com/RepliMap/replimap-mono/issues/7) fixed; add [#8](https://github.com/RepliMap/replimap-mono/issues/8) (license key as URL query param — ([2e4b6d0](https://github.com/RepliMap/replimap-mono/commit/2e4b6d02abce4829ff0686775b18d95878db733d))

## [1.2.8](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.2.7...replimap-api-v1.2.8) (2026-01-23)

## [1.2.7](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.2.6...replimap-api-v1.2.7) (2026-01-22)

## [1.2.6](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.2.5...replimap-api-v1.2.6) (2026-01-22)

## [1.2.5](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.2.4...replimap-api-v1.2.5) (2026-01-22)

## [1.2.4](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.2.3...replimap-api-v1.2.4) (2026-01-20)

## [1.2.3](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.2.2...replimap-api-v1.2.3) (2026-01-20)

## [1.2.2](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.2.1...replimap-api-v1.2.2) (2026-01-20)

## [1.2.1](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.2.0...replimap-api-v1.2.1) (2026-01-20)


### Bug Fixes

* **api:** use PKCS8/SPKI format for Ed25519 keys ([37d90af](https://github.com/RepliMap/replimap-mono/commit/37d90af14df7daae981a888e142301df56e2c4e5))
* **api:** use PKCS8/SPKI format for Ed25519 keys ([904d9a0](https://github.com/RepliMap/replimap-mono/commit/904d9a0eecee2c382a4f2a04662d06454a967a20))

## [1.2.0](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.1.2...replimap-api-v1.2.0) (2026-01-20)


### Features

* **api:** implement backend license system for CLI Phase 3 ([4030a1b](https://github.com/RepliMap/replimap-mono/commit/4030a1bd5d5efcf5bf18aba7f0325f9d6e7d6bd2))
* **api:** implement backend/frontend license system for CLI Phase 3 ([41abb0c](https://github.com/RepliMap/replimap-mono/commit/41abb0c49f0a0765c599fe6c032de8686992d36e))


### Bug Fixes

* **api:** SQLite cannot add UNIQUE column directly ([5fb172a](https://github.com/RepliMap/replimap-mono/commit/5fb172ae63667b1a45087bb29f59dcc7a18d7ea2))

## [1.1.2](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.1.1...replimap-api-v1.1.2) (2026-01-16)


### Bug Fixes

* **api:** update billing handler to use v4.0 plan names ([18417ac](https://github.com/RepliMap/replimap-mono/commit/18417ac234c62273f2440c239a67073d8a40a0c9))


### Refactoring

* **api:** remove legacy plan names and fix test mocks ([ae411c1](https://github.com/RepliMap/replimap-mono/commit/ae411c103871656157736ea7ecf7284bc9caa160))

## [1.1.1](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.1.0...replimap-api-v1.1.1) (2026-01-16)


### Documentation

* update documentation for v4.0 pricing tiers ([d5d341a](https://github.com/RepliMap/replimap-mono/commit/d5d341a4f8293fd9579d350ade0798f5a914b4d8))
* update documentation for v4.0 pricing tiers ([44a1c8f](https://github.com/RepliMap/replimap-mono/commit/44a1c8f8281e7f7c651b9e9da919e847cfcd3f72))

## [1.1.0](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.0.3...replimap-api-v1.1.0) (2026-01-15)


### Features

* **pricing:** implement v4.0 pricing transformation ([8e59f51](https://github.com/RepliMap/replimap-mono/commit/8e59f510b7cec4ede843accaddf7c3e0d96bf1dd))
* **pricing:** implement v4.0 pricing transformation ([114b844](https://github.com/RepliMap/replimap-mono/commit/114b844b07ace38c350cc8126150eb2bd8816e56))

## [1.0.3](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.0.2...replimap-api-v1.0.3) (2026-01-15)

## [1.0.2](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.0.1...replimap-api-v1.0.2) (2026-01-15)

## [1.0.1](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.0.0...replimap-api-v1.0.1) (2026-01-15)
