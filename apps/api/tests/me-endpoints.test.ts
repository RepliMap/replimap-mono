/**
 * Contract + owner-scoping tests for the /v1/me/* self-service endpoints,
 * against real handlers and a real (Miniflare D1) database.
 *
 * Contract half (followups #6/#7): /v1/me/license must expose
 * features.offline_grace_days (authoritative per-plan value, fail-closed 0 for
 * unknown plans), and /v1/me/machines must expose the full machine_id plus the
 * fingerprint metadata columns migration 010 added — the dashboard device list
 * and its Remove button are dead without them.
 *
 * Scoping half (security regression guard): these endpoints are authorized by
 * license-key possession. Widening the machines payload with full machine ids
 * must NOT widen the query scope — a key must only ever see/deactivate its own
 * license's machines. These tests pin that boundary.
 */

import {
  describe,
  it,
  expect,
  beforeAll,
  afterAll,
  beforeEach,
  afterEach,
  vi,
} from 'vitest';
import { handleGetOwnLicense, handleGetOwnMachines } from '../src/handlers/user';
import { handleDeactivateLicense } from '../src/handlers/deactivate-license';
import { MAX_MACHINE_CHANGES_PER_MONTH } from '../src/lib/constants';
import { createRealD1, realEnv, type RealD1 } from './real-d1';
import type { Env } from '../src/types/env';

const KEY_PRO = 'RM-AAAA-AAAA-AAAA-AAAA';
const KEY_TEAM = 'RM-BBBB-BBBB-BBBB-BBBB';
const KEY_COMMUNITY = 'RM-CCCC-CCCC-CCCC-CCCC';
const KEY_UNKNOWN_PLAN = 'RM-DDDD-DDDD-DDDD-DDDD';

const MACHINE_PRO = 'a'.repeat(32);
const MACHINE_TEAM = 'b'.repeat(32);

let d1: RealD1;
let env: Env;

/**
 * In-memory KV: the user/deactivate handlers pass env.CACHE straight into the
 * rate limiter (bypassing the RATE_LIMIT_DISABLED env check), so tests need a
 * working KV rather than realEnv's undefined placeholder.
 */
function memoryKV(): Env['CACHE'] {
  const store = new Map<string, string>();
  return {
    get: async (key: string) => store.get(key) ?? null,
    put: async (key: string, value: string) => {
      store.set(key, value);
    },
    delete: async (key: string) => {
      store.delete(key);
    },
  } as unknown as Env['CACHE'];
}

beforeAll(async () => {
  d1 = await createRealD1();
  env = realEnv(d1.DB, { CACHE: memoryKV() });
}, 30_000);

afterAll(async () => {
  await d1.dispose();
});

beforeEach(async () => {
  await d1.reset();
  vi.spyOn(console, 'log').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});

  await env.DB.prepare(
    `INSERT INTO user (id, email, name) VALUES
      ('u_pro', 'pro@example.com', ''),
      ('u_team', 'team@example.com', ''),
      ('u_comm', 'comm@example.com', ''),
      ('u_unk', 'unk@example.com', '')`
  ).run();
  await env.DB.prepare(
    `INSERT INTO licenses (id, user_id, license_key, plan, plan_type, status) VALUES
      ('lic_pro', 'u_pro', '${KEY_PRO}', 'pro', 'monthly', 'active'),
      ('lic_team', 'u_team', '${KEY_TEAM}', 'team', 'monthly', 'active'),
      ('lic_comm', 'u_comm', '${KEY_COMMUNITY}', 'community', 'free', 'active'),
      ('lic_unk', 'u_unk', '${KEY_UNKNOWN_PLAN}', 'legacy_solo', 'monthly', 'active')`
  ).run();
  await env.DB.prepare(
    `INSERT INTO license_machines
      (id, license_id, machine_id, machine_name, is_active, fingerprint_type, ci_provider, ci_repo) VALUES
      ('m_pro', 'lic_pro', '${MACHINE_PRO}', 'dev-laptop', 1, 'machine', NULL, NULL),
      ('m_team', 'lic_team', '${MACHINE_TEAM}', NULL, 1, 'ci', 'github', 'org/repo')`
  ).run();
});

afterEach(() => {
  vi.restoreAllMocks();
});

function licenseRequest(key: string): Request {
  return new Request(
    `https://api.test/v1/me/license?license_key=${encodeURIComponent(key)}`
  );
}

function machinesRequest(key: string): Request {
  return new Request(
    `https://api.test/v1/me/machines?license_key=${encodeURIComponent(key)}`
  );
}

function deactivateRequest(key: string, machineId: string): Request {
  return new Request('https://api.test/v1/license/deactivate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ license_key: key, machine_id: machineId }),
  });
}

async function machineActive(id: string): Promise<boolean> {
  const row = await env.DB.prepare(
    `SELECT is_active FROM license_machines WHERE id = ?`
  )
    .bind(id)
    .first<{ is_active: number }>();
  return row?.is_active === 1;
}

// ============================================================================
// /v1/me/license — features.offline_grace_days (followups #7)
// ============================================================================

describe('GET /v1/me/license — offline_grace_days contract', () => {
  async function graceDaysFor(key: string): Promise<unknown> {
    const res = await handleGetOwnLicense(licenseRequest(key), env, '1.2.3.4');
    expect(res.status).toBe(200);
    const body = (await res.json()) as {
      features: { offline_grace_days?: number };
    };
    return body.features.offline_grace_days;
  }

  it('returns the authoritative per-plan value for pro (7)', async () => {
    expect(await graceDaysFor(KEY_PRO)).toBe(7);
  });

  it('returns 14 for team', async () => {
    expect(await graceDaysFor(KEY_TEAM)).toBe(14);
  });

  it('returns 0 for community (must be online)', async () => {
    expect(await graceDaysFor(KEY_COMMUNITY)).toBe(0);
  });

  it('fails closed to 0 for an unknown plan value', async () => {
    expect(await graceDaysFor(KEY_UNKNOWN_PLAN)).toBe(0);
  });
});

// ============================================================================
// /v1/me/machines — full machine_id + fingerprint metadata (followups #6)
// ============================================================================

interface MachinesBody {
  machines: Array<{
    machine_id?: string;
    machine_id_truncated: string;
    machine_name: string | null;
    is_active: boolean;
    fingerprint_type?: string;
    ci_provider?: string | null;
    ci_repo?: string | null;
    container_type?: string | null;
  }>;
  active_count: number;
  limit: number;
  changes_this_month: number;
  changes_limit: number;
}

describe('GET /v1/me/machines — device payload contract', () => {
  async function machinesFor(key: string): Promise<MachinesBody> {
    const res = await handleGetOwnMachines(machinesRequest(key), env, '1.2.3.4');
    expect(res.status).toBe(200);
    return (await res.json()) as MachinesBody;
  }

  it('includes the full machine_id (required by the deactivate flow)', async () => {
    const body = await machinesFor(KEY_PRO);
    expect(body.machines).toHaveLength(1);
    expect(body.machines[0].machine_id).toBe(MACHINE_PRO);
  });

  it('includes fingerprint metadata for machine-type devices', async () => {
    const body = await machinesFor(KEY_PRO);
    expect(body.machines[0].fingerprint_type).toBe('machine');
    expect(body.machines[0].machine_name).toBe('dev-laptop');
  });

  it('includes CI metadata for ci-type devices', async () => {
    const body = await machinesFor(KEY_TEAM);
    expect(body.machines[0].fingerprint_type).toBe('ci');
    expect(body.machines[0].ci_provider).toBe('github');
    expect(body.machines[0].ci_repo).toBe('org/repo');
  });

  it('limit is the per-plan machine cap (pro=2, team=10)', async () => {
    expect((await machinesFor(KEY_PRO)).limit).toBe(2);
    expect((await machinesFor(KEY_TEAM)).limit).toBe(10);
  });

  it('changes_limit reflects MAX_MACHINE_CHANGES_PER_MONTH', async () => {
    expect((await machinesFor(KEY_PRO)).changes_limit).toBe(
      MAX_MACHINE_CHANGES_PER_MONTH
    );
  });
});

// ============================================================================
// Owner scoping — the boundary that must NOT loosen with this change
// ============================================================================

describe('owner scoping (license-key possession model)', () => {
  it('a key only ever sees its own machines', async () => {
    const res = await handleGetOwnMachines(
      machinesRequest(KEY_PRO),
      env,
      '1.2.3.4'
    );
    const body = (await res.json()) as MachinesBody;
    expect(body.machines).toHaveLength(1);
    const serialized = JSON.stringify(body);
    expect(serialized).not.toContain(MACHINE_TEAM);
    expect(serialized).not.toContain(MACHINE_TEAM.slice(0, 12));
  });

  it('an unknown key gets 404, not an empty scan', async () => {
    const res = await handleGetOwnMachines(
      machinesRequest('RM-ZZZZ-ZZZZ-ZZZZ-ZZZZ'),
      env,
      '1.2.3.4'
    );
    expect(res.status).toBe(404);
  });

  it("deactivate with key A + license B's machine_id must NOT touch B's machine", async () => {
    const res = await handleDeactivateLicense(
      deactivateRequest(KEY_PRO, MACHINE_TEAM),
      env,
      '1.2.3.4'
    );
    expect(res.status).toBe(200); // endpoint doesn't leak existence...
    expect(await machineActive('m_team')).toBe(true); // ...and B stays active
    expect(await machineActive('m_pro')).toBe(true); // A's own machine untouched too
  });

  it('deactivate with the owning key does deactivate (positive control)', async () => {
    const res = await handleDeactivateLicense(
      deactivateRequest(KEY_PRO, MACHINE_PRO),
      env,
      '1.2.3.4'
    );
    expect(res.status).toBe(200);
    expect(await machineActive('m_pro')).toBe(false);
    expect(await machineActive('m_team')).toBe(true);
  });
});
