/**
 * KV-based rate limiting for Cloudflare Workers
 */

import type { Env } from '../types/env';
import { Errors } from './errors';
import { RATE_LIMITS } from './constants';

interface RateLimitState {
  count: number;
  resetAt: number; // timestamp
}

/**
 * Check and update rate limit for a given key
 * Throws AppError if rate limit exceeded
 */
export async function checkRateLimit(
  kv: KVNamespace,
  endpoint: keyof typeof RATE_LIMITS,
  clientIP: string
): Promise<void> {
  const config = RATE_LIMITS[endpoint];
  const key = `ratelimit:${endpoint}:${clientIP}`;

  // Get current state
  const stateJson = await kv.get(key);
  const now = Date.now();

  let state: RateLimitState;

  if (stateJson) {
    state = JSON.parse(stateJson);

    // Check if window has expired
    if (now > state.resetAt) {
      // Start new window
      state = {
        count: 1,
        resetAt: now + config.window * 1000,
      };
    } else {
      // Increment count
      state.count++;

      // Check if exceeded
      if (state.count > config.requests) {
        const retryAfter = Math.ceil((state.resetAt - now) / 1000);
        throw Errors.rateLimitExceeded(retryAfter);
      }
    }
  } else {
    // First request in window
    state = {
      count: 1,
      resetAt: now + config.window * 1000,
    };
  }

  // Update state in KV (non-blocking, fire-and-forget)
  // TTL is window + buffer to auto-cleanup
  await kv.put(key, JSON.stringify(state), {
    expirationTtl: config.window + 60,
  });
}

/**
 * Get rate limit headers for response
 */
export function getRateLimitHeaders(
  endpoint: keyof typeof RATE_LIMITS,
  remaining: number,
  resetAt: number
): Record<string, string> {
  const config = RATE_LIMITS[endpoint];
  return {
    'X-RateLimit-Limit': String(config.requests),
    'X-RateLimit-Remaining': String(Math.max(0, remaining)),
    'X-RateLimit-Reset': String(Math.ceil(resetAt / 1000)),
  };
}

/**
 * Rate limiter middleware - returns headers to add to response
 *
 * Accepts either a plain KVNamespace (legacy) or the full Env (preferred).
 * When Env is passed and `RATE_LIMIT_DISABLED === 'true'`, the check is
 * skipped entirely — used by local dev and e2e harnesses so back-to-back
 * test runs don't trip production thresholds. NEVER set in production.
 */
export async function rateLimit(
  kvOrEnv: KVNamespace | Env,
  endpoint: keyof typeof RATE_LIMITS,
  clientIP: string
): Promise<Record<string, string>> {
  const env = isEnv(kvOrEnv) ? kvOrEnv : undefined;
  const kv: KVNamespace = env ? env.CACHE : (kvOrEnv as KVNamespace);

  const config = RATE_LIMITS[endpoint];
  const now = Date.now();

  if (env?.RATE_LIMIT_DISABLED === 'true') {
    return getRateLimitHeaders(
      endpoint,
      config.requests - 1,
      now + config.window * 1000
    );
  }

  await checkRateLimit(kv, endpoint, clientIP);

  return getRateLimitHeaders(
    endpoint,
    config.requests - 1,
    now + config.window * 1000
  );
}

function isEnv(x: KVNamespace | Env): x is Env {
  return (
    typeof x === 'object' &&
    x !== null &&
    'CACHE' in x &&
    'ENVIRONMENT' in x
  );
}
