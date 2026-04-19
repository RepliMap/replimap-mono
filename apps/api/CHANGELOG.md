# Changelog

## [1.3.0](https://github.com/RepliMap/replimap-mono/compare/replimap-api-v1.2.8...replimap-api-v1.3.0) (2026-04-19)


### Features

* **api:** add GET /v1/checkout/session/:id/license post-payment lookup ([ffdb8b4](https://github.com/RepliMap/replimap-mono/commit/ffdb8b475bbbec401b17a720b820cb3782f87533))
* **api:** add getLicenseByUserEmailLatest helper ([1f4134e](https://github.com/RepliMap/replimap-mono/commit/1f4134ebea41473bcbdb56218377be525f7e96ba))
* **api:** add POST /v1/license/provision-community for free-tier auto-signup ([c7d71e5](https://github.com/RepliMap/replimap-mono/commit/c7d71e5d3e1a83e5338b5951670f2153367b77e6))
* **api:** add RATE_LIMIT_DISABLED env flag for local dev/e2e ([7fbff44](https://github.com/RepliMap/replimap-mono/commit/7fbff449a531e2b7c7b0d735c241b9bd56c664ed))
* **api:** extend handleCreateCheckout to support lifetime billing ([704ded8](https://github.com/RepliMap/replimap-mono/commit/704ded807d0335efb58252f134ccd93181e6d924))


### Bug Fixes

* **api:** add migration to bootstrap Drizzle schema on local D1 ([aa29216](https://github.com/RepliMap/replimap-mono/commit/aa29216bd7410de1edb72df95a23d286563e2db0))
* **api:** guard checkout-license route so it doesn't swallow all GET requests ([6aa25dc](https://github.com/RepliMap/replimap-mono/commit/6aa25dc329fbdc8269fefeb13aa4b29e291b4d43))
* **api:** self-heal subscription.created when user not yet in DB ([df74f99](https://github.com/RepliMap/replimap-mono/commit/df74f99c851e18ec90183a274c245b108586ff25))

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
