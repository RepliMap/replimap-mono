import type { Fingerprint, LicenseDetails } from '@/types/license';

/**
 * View helpers that tolerate the real shape of `GET /v1/me/license`.
 *
 * That endpoint returns `features` / `usage` / `subscription` and does NOT
 * include a `fingerprints` array (the device list comes from a separate
 * endpoint, `GET /v1/me/machines`). So `license.fingerprints` is `undefined`
 * at runtime, and the previous `license.fingerprints.length` crashed with
 * "Cannot read properties of undefined (reading 'length')".
 */
export function licenseFingerprints(
  license: Pick<LicenseDetails, 'fingerprints'>
): Fingerprint[] {
  return license.fingerprints ?? [];
}

export function activeDeviceCount(
  license: Pick<LicenseDetails, 'fingerprints'>
): number {
  return licenseFingerprints(license).length;
}
