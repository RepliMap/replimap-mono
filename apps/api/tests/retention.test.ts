/**
 * Retention (scheduled handler) tests against the real D1 harness.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest';
import { handleScheduled } from '../src/index';
import { handleValidateLicense } from '../src/handlers/validate-license';
import { createDb, createLicense, findOrCreateUser } from '../src/lib/db';
import { createRealD1, realEnv, memoryKV, type RealD1 } from './real-d1';
import type { Env } from '../src/types/env';

const DAY = 86_400_000;
const KEY = 'RM-RETN-TEST-0001-AAAA';

let d1: RealD1;
let env: Env;
let licenseId: string;

const controller = {} as ScheduledController;

/** Timestamp `days` ago in the JS/ISO format. */
const iso = (days: number) => new Date(Date.now() - days * DAY).toISOString();
/** Timestamp `days` ago in the SQLite datetime('now') format. */
const sqlite = (days: number) => iso(days).replace('T', ' ').slice(0, 19);
const BOTH_FORMATS = [
  ['ISO', iso],
  ['SQLite', sqlite],
] as const;

const OLD_TABLES = ['snapshots', 'remediations', 'usage_daily', 'usage_events', 'license_aws_accounts'];

beforeAll(async () => {
  d1 = await createRealD1();
}, 30_000);
afterAll(async () => {
  await d1.dispose();
});

beforeEach(async () => {
  await d1.reset();
  for (const t of ['snapshots', 'remediations']) await d1.DB.prepare(`DELETE FROM ${t}`).run();
  env = realEnv(d1.DB, { CACHE: memoryKV() });
  const db = createDb(env.DB);
  const user = await findOrCreateUser(db, 'retention@example.com', 'cus_ret_1');
  const lic = await createLicense(db, {
    userId: user.id,
    licenseKey: KEY,
    plan: 'pro',
  } as Parameters<typeof createLicense>[1]);
  licenseId = lic.id;
  vi.spyOn(console, 'log').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

async function count(sqlText: string, ...binds: unknown[]): Promise<number> {
  const row = await d1.DB.prepare(sqlText).bind(...binds).first<{ c: number }>();
  return row?.c ?? 0;
}

async function insertMachine(id: string, active: 0 | 1, lastSeen: string) {
  await d1.DB.prepare(
    `INSERT INTO license_machines (id, license_id, machine_id, is_active, first_seen_at, last_seen_at)
     VALUES (?, ?, ?, ?, ?, ?)`
  )
    .bind(id, licenseId, id.padEnd(32, '0'), active, lastSeen, lastSeen)
    .run();
}

async function insertUsageLog(id: string, createdAt: string, action = 'validate', metadata: string | null = null) {
  await d1.DB.prepare(
    `INSERT INTO usage_logs (id, license_id, action, metadata, created_at) VALUES (?, ?, ?, ?, ?)`
  )
    .bind(id, licenseId, action, metadata, createdAt)
    .run();
}

async function insertMachineChange(id: string, changedAt: string) {
  await d1.DB.prepare(
    `INSERT INTO machine_changes (id, license_id, new_machine_id, changed_at) VALUES (?, ?, ?, ?)`
  )
    .bind(id, licenseId, 'f'.repeat(32), changedAt)
    .run();
}

async function seedOrphans() {
  const old = iso(1);
  await d1.DB.batch([
    d1.DB.prepare(
      `INSERT INTO license_aws_accounts (id, license_id, aws_account_id) VALUES ('a1', ?, '123456789012')`
    ).bind(licenseId),
    d1.DB.prepare(
      `INSERT INTO usage_events (id, license_id, event_type, created_at) VALUES ('e1', ?, 'scan', ?)`
    ).bind(licenseId, old),
    d1.DB.prepare(
      `INSERT INTO usage_daily (id, license_id, date, event_type) VALUES ('d1', ?, '2026-10-01', 'scan')`
    ).bind(licenseId),
    d1.DB.prepare(
      `INSERT INTO snapshots (id, license_id, name, region) VALUES ('s1', ?, 'snap', 'us-east-1')`
    ).bind(licenseId),
    d1.DB.prepare(
      `INSERT INTO remediations (id, license_id, region) VALUES ('r1', ?, 'us-east-1')`
    ).bind(licenseId),
  ]);
}

describe('scheduled retention handler', () => {
  it('purges every orphan table, whatever the row age', async () => {
    await seedOrphans();
    for (const t of OLD_TABLES) {
      expect(await count(`SELECT COUNT(*) AS c FROM ${t}`)).toBe(1);
    }

    await handleScheduled(controller, env);

    for (const t of OLD_TABLES) {
      expect(await count(`SELECT COUNT(*) AS c FROM ${t}`), t).toBe(0);
    }
  });

  it('never deactivates or deletes an active machine, however idle', async () => {
    await insertMachine('act400', 1, iso(400));
    await insertMachine('act400s', 1, sqlite(400));

    await handleScheduled(controller, env);

    expect(await count(`SELECT COUNT(*) AS c FROM license_machines WHERE is_active = 1`)).toBe(2);
    expect(await count(`SELECT COUNT(*) AS c FROM license_machines`)).toBe(2);
  });

  for (const [label, fmt] of BOTH_FORMATS) {
    it(`deletes inactive machines at 91 days and keeps them at 89 days (${label} timestamps)`, async () => {
      await insertMachine('inact91', 0, fmt(91));
      await insertMachine('inact89', 0, fmt(89));

      await handleScheduled(controller, env);

      const ids = (await d1.DB.prepare(`SELECT id FROM license_machines`).all<{ id: string }>()).results.map(
        (r) => r.id
      );
      expect(ids).toEqual(['inact89']);
    });

    it(`prunes usage_logs and machine_changes around the 90-day cutoff (${label} timestamps)`, async () => {
      await insertUsageLog('ul91', fmt(91));
      await insertUsageLog('ul89', fmt(89));
      await insertMachineChange('mc91', fmt(91));
      await insertMachineChange('mc89', fmt(89));

      await handleScheduled(controller, env);

      const logs = (await d1.DB.prepare(`SELECT id FROM usage_logs`).all<{ id: string }>()).results.map((r) => r.id);
      const changes = (await d1.DB.prepare(`SELECT id FROM machine_changes`).all<{ id: string }>()).results.map(
        (r) => r.id
      );
      expect(logs).toEqual(['ul89']);
      expect(changes).toEqual(['mc89']);
    });

    it(`keeps old offline-issue ledger rows while pruning other old logs (${label} timestamps)`, async () => {
      const ledger = JSON.stringify({ kind: 'offline_issue', exp: 1, note: 'n' });
      await insertUsageLog('ledger400', fmt(400), 'activate', ledger);
      await insertUsageLog('plain-activate400', fmt(400), 'activate', JSON.stringify({ cli_version: '1' }));
      await insertUsageLog('null-meta400', fmt(400), 'activate', null);
      await insertUsageLog('bad-json400', fmt(400), 'activate', 'not json');
      await insertUsageLog('validate-kind400', fmt(400), 'validate', ledger);

      await handleScheduled(controller, env);

      const logs = (await d1.DB.prepare(`SELECT id FROM usage_logs ORDER BY id`).all<{ id: string }>()).results.map(
        (r) => r.id
      );
      expect(logs).toEqual(['ledger400']);
    });

    it(`keeps idempotency keys for 7 days and processed events for 30 days (${label} timestamps)`, async () => {
      await d1.DB.batch([
        d1.DB.prepare(`INSERT INTO usage_idempotency (idempotency_key, license_id, created_at) VALUES ('i8', ?, ?)`).bind(licenseId, fmt(8)),
        d1.DB.prepare(`INSERT INTO usage_idempotency (idempotency_key, license_id, created_at) VALUES ('i6', ?, ?)`).bind(licenseId, fmt(6)),
        d1.DB.prepare(`INSERT INTO processed_events (event_id, event_type, processed_at) VALUES ('p31', 't', ?)`).bind(fmt(31)),
        d1.DB.prepare(`INSERT INTO processed_events (event_id, event_type, processed_at) VALUES ('p29', 't', ?)`).bind(fmt(29)),
      ]);

      await handleScheduled(controller, env);

      expect(await count(`SELECT COUNT(*) AS c FROM usage_idempotency WHERE idempotency_key = 'i6'`)).toBe(1);
      expect(await count(`SELECT COUNT(*) AS c FROM usage_idempotency WHERE idempotency_key = 'i8'`)).toBe(0);
      expect(await count(`SELECT COUNT(*) AS c FROM processed_events WHERE event_id = 'p29'`)).toBe(1);
      expect(await count(`SELECT COUNT(*) AS c FROM processed_events WHERE event_id = 'p31'`)).toBe(0);
    });
  }

  it('a failing step does not stop the others and fires the ops alert', async () => {
    await seedOrphans();
    await insertMachine('inact91', 0, iso(91));
    await insertUsageLog('ul91', iso(91));

    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200 });
    vi.stubGlobal('fetch', fetchMock);

    // Simulate a table missing in this environment: the statement throws.
    const realPrepare = d1.DB.prepare.bind(d1.DB);
    const failingDb = new Proxy(d1.DB, {
      get(target, prop, receiver) {
        if (prop === 'prepare') {
          return (query: string) => {
            if (query.includes('DELETE FROM usage_events')) {
              throw new Error('no such table: usage_events');
            }
            return realPrepare(query);
          };
        }
        return Reflect.get(target, prop, receiver);
      },
    }) as D1Database;
    const failingEnv = realEnv(failingDb, {
      CACHE: memoryKV(),
      OPS_ALERT_WEBHOOK: 'https://alerts.example.test/hook',
    });

    await handleScheduled(controller, failingEnv);

    // The failed step left its rows; every other step still ran.
    expect(await count(`SELECT COUNT(*) AS c FROM usage_events`)).toBe(1);
    expect(await count(`SELECT COUNT(*) AS c FROM license_aws_accounts`)).toBe(0);
    expect(await count(`SELECT COUNT(*) AS c FROM usage_daily`)).toBe(0);
    expect(await count(`SELECT COUNT(*) AS c FROM snapshots`)).toBe(0);
    expect(await count(`SELECT COUNT(*) AS c FROM remediations`)).toBe(0);
    expect(await count(`SELECT COUNT(*) AS c FROM license_machines`)).toBe(0);
    expect(await count(`SELECT COUNT(*) AS c FROM usage_logs`)).toBe(0);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const sent = JSON.parse(fetchMock.mock.calls[0][1].body as string) as { text: string };
    expect(sent.text).toContain('RETENTION_STEP_FAILED');
    expect(sent.text).toContain('usage_events');
  });

  it('does not alert when every step succeeds', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200 });
    vi.stubGlobal('fetch', fetchMock);
    const alertingEnv = realEnv(d1.DB, { CACHE: memoryKV(), OPS_ALERT_WEBHOOK: 'https://alerts.example.test/hook' });

    await handleScheduled(controller, alertingEnv);

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('leaves the current month change count alone and a long-idle machine re-validates without a new change', async () => {
    const machine = 'abcd'.repeat(8);
    await insertMachineChange('mc-now', new Date().toISOString());
    await d1.DB.prepare(
      `INSERT INTO license_machines (id, license_id, machine_id, is_active, first_seen_at, last_seen_at)
       VALUES ('idle60', ?, ?, 1, ?, ?)`
    )
      .bind(licenseId, machine, iso(60), iso(60))
      .run();
    const monthlyChanges = () =>
      count(
        `SELECT COUNT(*) AS c FROM machine_changes WHERE license_id = ? AND changed_at >= datetime('now', 'start of month')`,
        licenseId
      );
    const before = await monthlyChanges();

    await handleScheduled(controller, env);

    expect(await monthlyChanges()).toBe(before);
    expect(await count(`SELECT COUNT(*) AS c FROM machine_changes`)).toBe(1);

    const res = await handleValidateLicense(
      new Request('https://api.test/v1/license/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: KEY, machine_id: machine, cli_version: '1.0.0' }),
      }),
      env,
      '127.0.0.1'
    );
    expect(res.status).toBe(200);
    expect(await count(`SELECT COUNT(*) AS c FROM license_machines WHERE id = 'idle60' AND is_active = 1`)).toBe(1);
    expect(await count(`SELECT COUNT(*) AS c FROM machine_changes`)).toBe(1);
  });

  it('reactivating a deactivated machine writes an ISO last_seen_at, not a SQLite datetime', async () => {
    const machine = 'beef'.repeat(8);
    const old = '2026-01-01 00:00:00';
    await d1.DB.prepare(
      `INSERT INTO license_machines (id, license_id, machine_id, is_active, first_seen_at, last_seen_at)
       VALUES ('react1', ?, ?, 0, ?, ?)`
    )
      .bind(licenseId, machine, old, old)
      .run();

    const res = await handleValidateLicense(
      new Request('https://api.test/v1/license/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: KEY, machine_id: machine, cli_version: '1.0.0' }),
      }),
      env,
      '127.0.0.1'
    );
    expect(res.status).toBe(200);

    const row = await d1.DB.prepare(`SELECT is_active, last_seen_at FROM license_machines WHERE id = 'react1'`).first<{
      is_active: number;
      last_seen_at: string;
    }>();
    expect(row?.is_active).toBe(1);
    expect(row?.last_seen_at).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
  });
});
