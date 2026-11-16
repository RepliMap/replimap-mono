/**
 * Rate limiting for Cloudflare Workers.
 *
 * Primary backend: the Workers Rate Limiting binding (RL_* in wrangler.toml),
 * which counts per Cloudflare location and costs no KV writes. When the
 * binding is absent (unit tests, a config without it) a per-isolate in-memory
 * counter is used instead. Either way the limiter FAILS OPEN: any backend
 * error is logged once and the request is let through, so the limiter can
 * never take the API down.
 */

import type { Env } from '../types/env';
import { AppError, Errors } from './errors';
import { RATE_LIMITS } from './constants';

type Endpoint = keyof typeof RATE_LIMITS;

/** wrangler.toml binding name per endpoint (limits mirror RATE_LIMITS). */
const BINDINGS: Record<Endpoint, keyof Env> = {
  validate: 'RL_VALIDATE',
  activate: 'RL_ACTIVATE',
  deactivate: 'RL_DEACTIVATE',
  admin: 'RL_ADMIN',
  metrics: 'RL_METRICS',
  resend_email: 'RL_RESEND_EMAIL',
};

// shortcut: per-isolate fallback, not shared across isolates/locations; only
// used when the RL_* binding is missing (tests, misconfigured env).
const memoryWindows = new Map<string, { count: number; resetAt: number }>();
const MEMORY_MAX_KEYS = 10_000;

let backendErrorLogged = false;

function checkMemory(endpoint: Endpoint, key: string, now: number): number | null {
  const config = RATE_LIMITS[endpoint];
  const mapKey = `${endpoint}:${key}`;
  const state = memoryWindows.get(mapKey);
  if (!state || now > state.resetAt) {
    if (memoryWindows.size >= MEMORY_MAX_KEYS) memoryWindows.clear();
    memoryWindows.set(mapKey, { count: 1, resetAt: now + config.window * 1000 });
    return null;
  }
  state.count++;
  return state.count > config.requests ? Math.ceil((state.resetAt - now) / 1000) : null;
}

/**
 * Check and count one request for `key` against `endpoint`'s limit.
 * Throws the rate-limit AppError when exceeded; never throws anything else.
 *
 * The first argument is the Worker Env (preferred: enables the RL_* binding)
 * or a bare KVNamespace (legacy callers: in-memory fallback, KV is not used).
 */
export async function checkRateLimit(
  kvOrEnv: KVNamespace | Env,
  endpoint: Endpoint,
  clientIP: string
): Promise<void> {
  try {
    const env = isEnv(kvOrEnv) ? kvOrEnv : undefined;
    const binding = env?.[BINDINGS[endpoint]] as RateLimit | undefined;
    let retryAfter: number | null;
    if (binding && typeof binding.limit === 'function') {
      const { success } = await binding.limit({ key: `${endpoint}:${clientIP}` });
      retryAfter = success ? null : RATE_LIMITS[endpoint].window;
    } else {
      retryAfter = checkMemory(endpoint, clientIP, Date.now());
    }
    if (retryAfter !== null) throw Errors.rateLimitExceeded(retryAfter);
  } catch (error) {
    if (error instanceof AppError) throw error;
    if (!backendErrorLogged) {
      backendErrorLogged = true;
      console.error('[RateLimit] backend error, failing open:', error);
    }
  }
}

/** Test hook: reset the in-memory fallback and the log-once flag. */
export function _resetRateLimiterForTests(): void {
  memoryWindows.clear();
  backendErrorLogged = false;
}

/**
 * Get rate limit headers for response
 */
export function getRateLimitHeaders(
  endpoint: Endpoint,
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
  endpoint: Endpoint,
  clientIP: string
): Promise<Record<string, string>> {
  const env = isEnv(kvOrEnv) ? kvOrEnv : undefined;
  const config = RATE_LIMITS[endpoint];
  const now = Date.now();

  if (env?.RATE_LIMIT_DISABLED !== 'true') {
    await checkRateLimit(kvOrEnv, endpoint, clientIP);
  }

  return getRateLimitHeaders(
    endpoint,
    config.requests - 1,
    now + config.window * 1000
  );
}

function isEnv(x: KVNamespace | Env | undefined): x is Env {
  return (
    typeof x === 'object' &&
    x !== null &&
    'CACHE' in x &&
    'ENVIRONMENT' in x
  );
}
