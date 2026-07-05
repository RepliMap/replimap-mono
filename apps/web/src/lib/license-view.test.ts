import { describe, it, expect } from 'vitest';
import type { LicenseDetails, MachineInfo } from '@/types/license';
import {
  activeDeviceCount,
  expiresAt,
  graceDays,
  machinesToFingerprints,
} from './license-view';

/** A license exactly as GET /v1/me/license returns it (real contract). */
function apiLicense(overrides: Partial<LicenseDetails> = {}): LicenseDetails {
  return {
    license_key: 'RM-5LTH-ATZ4-J2YC-YWNS',
    plan: 'pro',
    status: 'active',
    features: {
      resources_per_scan: -1,
      scans_per_month: -1,
      aws_accounts: 3,
      machines: 2,
      export_formats: ['json'],
      offline_grace_days: 7,
    },
    usage: {
      scans_this_month: 0,
      machines_active: 1,
      machines_limit: 2,
      aws_accounts_active: 0,
      aws_accounts_limit: 3,
    },
    subscription: {
      current_period_start: '2026-07-04T14:36:49.000Z',
      current_period_end: '2026-08-04T14:36:49.000Z',
      has_payment_method: true,
    },
    created_at: '2026-07-04T14:36:53.664Z',
    ...overrides,
  } as LicenseDetails;
}

describe('graceDays — server-issued entitlement, never derived client-side', () => {
  it('reads features.offline_grace_days', () => {
    expect(graceDays(apiLicense())).toBe(7);
  });

  it('fails closed to 0 when features is absent (older cached response)', () => {
    expect(graceDays(apiLicense({ features: undefined }))).toBe(0);
  });
});

describe('activeDeviceCount — server-authoritative usage.machines_active', () => {
  it('reads usage.machines_active', () => {
    expect(activeDeviceCount(apiLicense())).toBe(1);
  });

  it('falls back to 0 when usage is absent', () => {
    expect(activeDeviceCount(apiLicense({ usage: undefined }))).toBe(0);
  });
});

describe('expiresAt — status-dependent display (decision 3)', () => {
  it('active license → null (renders "Never")', () => {
    expect(expiresAt(apiLicense({ status: 'active' }))).toBeNull();
  });

  it('canceled license → paid-through date from subscription.current_period_end', () => {
    expect(expiresAt(apiLicense({ status: 'canceled' }))).toBe(
      '2026-08-04T14:36:49.000Z'
    );
  });

  it('past_due license → paid-through date', () => {
    expect(expiresAt(apiLicense({ status: 'past_due' }))).toBe(
      '2026-08-04T14:36:49.000Z'
    );
  });

  it('canceled with no period end recorded → null', () => {
    expect(
      expiresAt(
        apiLicense({
          status: 'canceled',
          subscription: {
            current_period_start: null,
            current_period_end: null,
            has_payment_method: false,
          },
        })
      )
    ).toBeNull();
  });
});

describe('machinesToFingerprints — /v1/me/machines → device-list UI shape', () => {
  const machines: MachineInfo[] = [
    {
      machine_id: 'a'.repeat(32),
      machine_id_truncated: 'aaaaaaaa...aaaa',
      machine_name: 'dev-laptop',
      is_active: true,
      first_seen_at: '2026-07-01T00:00:00.000Z',
      last_seen_at: '2026-07-04T00:00:00.000Z',
      fingerprint_type: 'machine',
      ci_provider: null,
      ci_repo: null,
      container_type: null,
    },
    {
      machine_id: 'b'.repeat(32),
      machine_id_truncated: 'bbbbbbbb...bbbb',
      machine_name: null,
      is_active: true,
      first_seen_at: '2026-07-01T00:00:00.000Z',
      last_seen_at: '2026-07-03T00:00:00.000Z',
      fingerprint_type: 'ci',
      ci_provider: 'github',
      ci_repo: 'org/repo',
      container_type: null,
    },
    {
      machine_id: 'c'.repeat(32),
      machine_id_truncated: 'cccccccc...cccc',
      machine_name: 'old-box',
      is_active: false, // deactivated — must not show in the device list
      first_seen_at: '2026-06-01T00:00:00.000Z',
      last_seen_at: '2026-06-02T00:00:00.000Z',
      fingerprint_type: 'machine',
      ci_provider: null,
      ci_repo: null,
      container_type: null,
    },
  ];

  it('maps active machines to the Fingerprint UI shape (full id preserved for deactivate)', () => {
    const result = machinesToFingerprints(machines);
    expect(result).toHaveLength(2);
    expect(result[0]).toMatchObject({
      fingerprint: 'a'.repeat(32),
      type: 'machine',
      last_seen: '2026-07-04T00:00:00.000Z',
    });
    expect(result[1]).toMatchObject({
      fingerprint: 'b'.repeat(32),
      type: 'ci',
      ci_provider: 'github',
      ci_repo: 'org/repo',
    });
  });

  it('coerces unknown fingerprint types to "machine" for the badge', () => {
    const odd = [
      { ...machines[0], fingerprint_type: 'developer_workstation' },
    ];
    expect(machinesToFingerprints(odd)[0].type).toBe('machine');
  });

  it('returns [] for undefined input', () => {
    expect(machinesToFingerprints(undefined)).toEqual([]);
  });
});
