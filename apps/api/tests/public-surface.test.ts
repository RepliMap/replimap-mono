/**
 * What the public, unauthenticated surface reveals: `/` and `/health`, plus
 * the prod worker's exposure in wrangler.toml.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import worker from '../src/index';
import type { Env } from '../src/types/env';

const env = { ENVIRONMENT: 'production', API_VERSION: 'v1', CORS_ORIGIN: '*' } as Env;

async function get(path: string): Promise<Record<string, unknown>> {
  const res = await worker.fetch(new Request(`https://api.test${path}`), env);
  expect(res.status).toBe(200);
  return (await res.json()) as Record<string, unknown>;
}

describe('public surface', () => {
  it('GET / returns only the service name and API version', async () => {
    expect(await get('/')).toEqual({ name: 'RepliMap License API', version: 'v1' });
  });

  it('GET /health does not carry the stale pricing_data_date', async () => {
    const body = await get('/health');
    expect(body.status).toBe('ok');
    expect(body).not.toHaveProperty('pricing_data_date');
  });

  it('the prod environment disables workers.dev (served on its custom domain)', () => {
    const toml = readFileSync(join(__dirname, '..', 'wrangler.toml'), 'utf8');
    const prod = toml.slice(toml.indexOf('[env.prod]'));
    const prodHeader = prod.slice(0, prod.indexOf('[env.prod.vars]'));
    expect(prodHeader).toMatch(/^workers_dev = false$/m);
    expect(prod).toMatch(/pattern = "api\.replimap\.com"\s*\ncustom_domain = true/);
    // dev keeps its defaults
    expect(toml.slice(0, toml.indexOf('[env.prod]'))).not.toMatch(/^workers_dev/m);
  });
});
