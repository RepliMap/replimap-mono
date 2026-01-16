/**
 * Test Helpers and Mocks for RepliMap Backend Tests
 */

import type { Env } from '../src/types';

// ============================================================================
// Mock D1 Database
// ============================================================================

interface MockResult {
  success: boolean;
  results: unknown[];
  meta?: Record<string, unknown>;
}

interface MockPreparedStatement {
  bind: (...args: unknown[]) => MockPreparedStatement;
  first: <T = unknown>() => Promise<T | null>;
  all: <T = unknown>() => Promise<{ results: T[]; success: boolean }>;
  run: () => Promise<MockResult>;
  raw: <T = unknown[]>() => Promise<T[]>;
}

export function createMockDB(data: Record<string, unknown[]> = {}): D1Database {
  const mockPrepare = (query: string): MockPreparedStatement => {
    let boundParams: unknown[] = [];

    const statement: MockPreparedStatement = {
      bind: (...args: unknown[]) => {
        boundParams = args;
        return statement;
      },
      first: async <T = unknown>() => {
        // Simulate basic query behavior
        const table = extractTableName(query);
        if (table && data[table]?.length) {
          return data[table][0] as T;
        }
        return null;
      },
      all: async <T = unknown>() => {
        const table = extractTableName(query);
        return {
          results: (data[table] ?? []) as T[],
          success: true,
        };
      },
      run: async () => ({
        success: true,
        results: [],
        meta: { changes: 1 },
      }),
      raw: async <T = unknown[]>() => {
        // raw() returns results as arrays instead of objects
        const table = extractTableName(query);
        const results = data[table] ?? [];
        // Convert objects to arrays of values
        return results.map((row) => {
          if (typeof row === 'object' && row !== null) {
            return Object.values(row) as T;
          }
          return [row] as T;
        });
      },
    };

    return statement;
  };

  return {
    prepare: mockPrepare,
    exec: async () => ({ count: 0, duration: 0 }),
    batch: async () => [],
    dump: async () => new ArrayBuffer(0),
  } as unknown as D1Database;
}

function extractTableName(query: string): string | null {
  const fromMatch = query.match(/FROM\s+(\w+)/i);
  const intoMatch = query.match(/INTO\s+(\w+)/i);
  const updateMatch = query.match(/UPDATE\s+(\w+)/i);
  return fromMatch?.[1] ?? intoMatch?.[1] ?? updateMatch?.[1] ?? null;
}

// ============================================================================
// Mock KV Namespace (for rate limiting)
// ============================================================================

export function createMockKV(): KVNamespace {
  const store = new Map<string, { value: string; expiration?: number }>();

  return {
    get: async (key: string) => {
      const item = store.get(key);
      if (item && item.expiration && Date.now() > item.expiration) {
        store.delete(key);
        return null;
      }
      return item?.value ?? null;
    },
    put: async (key: string, value: string, options?: { expirationTtl?: number }) => {
      const expiration = options?.expirationTtl
        ? Date.now() + options.expirationTtl * 1000
        : undefined;
      store.set(key, { value, expiration });
    },
    delete: async (key: string) => {
      store.delete(key);
    },
    list: async () => ({ keys: [], list_complete: true, cursor: '' }),
    getWithMetadata: async () => ({ value: null, metadata: null }),
  } as unknown as KVNamespace;
}

// ============================================================================
// Mock Environment
// ============================================================================

export function createMockEnv(overrides: Partial<Env> = {}): Env {
  return {
    DB: createMockDB(),
    CACHE: createMockKV(),
    ENVIRONMENT: 'test',
    STRIPE_SECRET_KEY: 'sk_test_mock',
    STRIPE_WEBHOOK_SECRET: 'whsec_test_mock',
    ADMIN_API_KEY: 'test-admin-key',
    CORS_ORIGIN: '*',
    API_VERSION: 'v1',
    ...overrides,
  };
}

// ============================================================================
// Request Helpers
// ============================================================================

export function createRequest(
  method: string,
  path: string,
  body?: unknown,
  headers: Record<string, string> = {}
): Request {
  const url = `https://api.replimap.com${path}`;
  const init: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'CF-Connecting-IP': '1.2.3.4',
      ...headers,
    },
  };

  if (body) {
    init.body = JSON.stringify(body);
  }

  return new Request(url, init);
}

// ============================================================================
// Test Data Generators
// ============================================================================

export function generateLicenseKey(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  const segment = () =>
    Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  return `RM-${segment()}-${segment()}-${segment()}-${segment()}`;
}

export function generateMachineId(): string {
  return Array.from({ length: 32 }, () =>
    Math.floor(Math.random() * 16).toString(16)
  ).join('');
}

export function generateAwsAccountId(): string {
  return Array.from({ length: 12 }, () => Math.floor(Math.random() * 10)).join('');
}

// ============================================================================
// Mock License Data
// ============================================================================

export const mockLicense = {
  id: 'lic_test_123',
  license_key: 'RM-TEST-1234-5678-ABCD',
  user_id: 'user_test_123',
  plan: 'pro',
  plan_type: 'monthly',
  status: 'active',
  current_period_start: new Date().toISOString(),
  current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
  stripe_subscription_id: 'sub_test_123',
  stripe_session_id: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  canceled_at: null,
  revoked_at: null,
  revoked_reason: null,
};

/** Mock lifetime license for testing one-time purchases */
export const mockLifetimeLicense = {
  id: 'lic_lifetime_123',
  license_key: 'RM-LIFE-1234-5678-ABCD',
  user_id: 'user_test_123',
  plan: 'pro',
  plan_type: 'lifetime',
  status: 'active',
  current_period_start: new Date().toISOString(),
  current_period_end: '2099-12-31T23:59:59.000Z',
  stripe_subscription_id: null,
  stripe_session_id: 'cs_lifetime_123',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  canceled_at: null,
  revoked_at: null,
  revoked_reason: null,
};

/** Mock revoked lifetime license (after refund) */
export const mockRevokedLicense = {
  id: 'lic_revoked_123',
  license_key: 'RM-REVK-1234-5678-ABCD',
  user_id: 'user_test_123',
  plan: 'pro',
  plan_type: 'lifetime',
  status: 'revoked',
  current_period_start: new Date().toISOString(),
  current_period_end: '2099-12-31T23:59:59.000Z',
  stripe_subscription_id: null,
  stripe_session_id: 'cs_revoked_123',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  canceled_at: null,
  revoked_at: new Date().toISOString(),
  revoked_reason: 'Refunded: charge_ch_test_123',
};

export const mockUser = {
  id: 'user_test_123',
  email: 'test@example.com',
  stripe_customer_id: 'cus_test_123',
  created_at: new Date().toISOString(),
};

export const mockMachine = {
  id: 'machine_test_123',
  license_id: 'lic_test_123',
  machine_id: 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6',
  machine_name: 'Test Machine',
  is_active: 1,
  first_seen_at: new Date().toISOString(),
  last_seen_at: new Date().toISOString(),
};

// ============================================================================
// Response Helpers
// ============================================================================

export async function parseResponse<T>(response: Response): Promise<T> {
  return response.json() as Promise<T>;
}

export function expectStatus(response: Response, status: number): void {
  if (response.status !== status) {
    throw new Error(`Expected status ${status}, got ${response.status}`);
  }
}
