import { beforeEach } from 'vitest';
import { _resetRateLimiterForTests } from '../src/lib/rate-limiter';
import { _resetJwksCacheForTests } from '../src/lib/clerk';

// Module-scoped state (in-memory rate-limit fallback, Clerk JWKS cache):
// start every test clean, as each test env used to get a fresh mock KV and
// every Clerk harness mints its own key under the same kid.
beforeEach(() => {
  _resetRateLimiterForTests();
  _resetJwksCacheForTests();
});
