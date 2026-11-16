/**
 * Rate limiter: binding-backed, KV-free, fail-open.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { rateLimit, checkRateLimit, _resetRateLimiterForTests } from '../src/lib/rate-limiter';
import { AppError } from '../src/lib/errors';
import { RATE_LIMITS } from '../src/lib/constants';
import type { Env } from '../src/types/env';

function throwingKV(): KVNamespace {
  const boom = async () => {
    throw new Error('KV put() limit exceeded for the day');
  };
  return { get: boom, put: boom, delete: boom } as unknown as KVNamespace;
}

function env(overrides: Partial<Env> = {}): Env {
  return {
    CACHE: throwingKV(),
    ENVIRONMENT: 'production',
    ...overrides,
  } as Env;
}

function binding(impl: () => Promise<{ success: boolean }>): RateLimit {
  return { limit: vi.fn(impl) } as unknown as RateLimit;
}

describe('rate limiter', () => {
  beforeEach(() => {
    _resetRateLimiterForTests();
    vi.restoreAllMocks();
  });

  it('never touches KV (exhausted KV quota cannot 500 the API)', async () => {
    const e = env();
    await expect(rateLimit(e, 'validate', '1.2.3.4')).resolves.toBeDefined();
    await expect(rateLimit(e.CACHE, 'validate', '1.2.3.4')).resolves.toBeDefined();
  });

  it('fails open when the binding throws, logging once', async () => {
    const err = vi.spyOn(console, 'error').mockImplementation(() => {});
    const e = env({ RL_VALIDATE: binding(async () => { throw new Error('binding down'); }) });
    await expect(rateLimit(e, 'validate', '1.2.3.4')).resolves.toBeDefined();
    await expect(rateLimit(e, 'validate', '1.2.3.4')).resolves.toBeDefined();
    expect(err).toHaveBeenCalledTimes(1);
  });

  it('uses the binding and maps a denial to RATE_LIMIT_EXCEEDED', async () => {
    const rl = binding(async () => ({ success: false }));
    const e = env({ RL_ADMIN: rl });
    const error = await checkRateLimit(e, 'admin', '9.9.9.9').catch((x) => x);
    expect(error).toBeInstanceOf(AppError);
    expect(error.errorCode).toBe('RATE_LIMIT_EXCEEDED');
    expect(error.statusCode).toBe(429);
    expect(rl.limit).toHaveBeenCalledWith({ key: 'admin:9.9.9.9' });
  });

  it('in-memory fallback still enforces the limit when no binding is configured', async () => {
    const e = env();
    for (let i = 0; i < RATE_LIMITS.activate.requests; i++) {
      await checkRateLimit(e, 'activate', '5.5.5.5');
    }
    const error = await checkRateLimit(e, 'activate', '5.5.5.5').catch((x) => x);
    expect(error).toBeInstanceOf(AppError);
    expect(error.errorCode).toBe('RATE_LIMIT_EXCEEDED');
    // other keys are unaffected
    await expect(checkRateLimit(e, 'activate', '6.6.6.6')).resolves.toBeUndefined();
  });

  it('RATE_LIMIT_DISABLED skips the check', async () => {
    const rl = binding(async () => ({ success: false }));
    await expect(
      rateLimit(env({ RL_VALIDATE: rl, RATE_LIMIT_DISABLED: 'true' }), 'validate', 'x')
    ).resolves.toBeDefined();
    expect(rl.limit).not.toHaveBeenCalled();
  });
});
