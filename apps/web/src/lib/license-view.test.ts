import { describe, it, expect } from 'vitest';
import type { LicenseDetails } from '@/types/license';
import { activeDeviceCount, licenseFingerprints } from './license-view';

/**
 * A license exactly as GET /v1/me/license returns it: note there is NO
 * `fingerprints` field (nor `offline_grace_days`) — those are not part of that
 * endpoint's payload. This is the shape that reaches LicenseCard for the real
 * (now canceled) license and triggered the crash.
 */
function apiLicenseWithoutFingerprints(): LicenseDetails {
  return {
    license_key: 'RM-5LTH-ATZ4-J2YC-YWNS',
    plan: 'pro',
    status: 'canceled',
    expires_at: null,
    // fingerprints + offline_grace_days intentionally absent (as from the API)
  } as unknown as LicenseDetails;
}

describe('license-view: /v1/me/license responses omit the fingerprints array', () => {
  it('activeDeviceCount returns 0 instead of crashing when fingerprints is absent', () => {
    // Reproduces "Cannot read properties of undefined (reading 'length')":
    // the pre-fix implementation did `license.fingerprints.length`.
    expect(activeDeviceCount(apiLicenseWithoutFingerprints())).toBe(0);
  });

  it('licenseFingerprints returns [] when the field is absent', () => {
    expect(licenseFingerprints(apiLicenseWithoutFingerprints())).toEqual([]);
  });

  it('licenseFingerprints passes through a populated array', () => {
    const license = {
      fingerprints: [
        {
          fingerprint: 'a'.repeat(32),
          type: 'machine',
          last_seen: '2026-07-04T00:00:00.000Z',
        },
      ],
    } as unknown as LicenseDetails;
    expect(licenseFingerprints(license)).toHaveLength(1);
    expect(activeDeviceCount(license)).toBe(1);
  });
});
