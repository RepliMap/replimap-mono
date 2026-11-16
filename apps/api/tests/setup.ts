import { beforeEach } from 'vitest';
import { _resetRateLimiterForTests } from '../src/lib/rate-limiter';

// The in-memory rate-limit fallback is module-scoped; start every test with
// empty counters (the old KV limiter got a fresh mock KV per test env).
beforeEach(() => {
  _resetRateLimiterForTests();
});
