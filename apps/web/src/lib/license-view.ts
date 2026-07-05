import type {
  Fingerprint,
  FingerprintType,
  LicenseDetails,
  MachineInfo,
} from '@/types/license';

/**
 * View helpers over the real /v1/me/license and /v1/me/machines contracts.
 * All helpers are defensive against missing nested objects (older cached
 * responses) — display code must never crash on a partial payload.
 */

/**
 * Offline grace period in days — server-issued entitlement
 * (features.offline_grace_days). Fails closed to 0 (must be online).
 */
export function graceDays(license: LicenseDetails): number {
  return license.features?.offline_grace_days ?? 0;
}

/**
 * Active device count — server-authoritative usage.machines_active
 * (same source the API enforces limits against).
 */
export function activeDeviceCount(license: LicenseDetails): number {
  return license.usage?.machines_active ?? 0;
}

/**
 * Expiry display value (decision: status-dependent).
 * - active (incl. lifetime/community): null → render "Never".
 * - canceled / past_due: the paid-through date (subscription.current_period_end)
 *   so the user sees how long their payment still covers.
 */
export function expiresAt(license: LicenseDetails): string | null {
  if (license.status === 'canceled' || license.status === 'past_due') {
    return license.subscription?.current_period_end ?? null;
  }
  return null;
}

const FINGERPRINT_TYPES: readonly FingerprintType[] = [
  'machine',
  'ci',
  'container',
];

function coerceFingerprintType(value: string): FingerprintType {
  return (FINGERPRINT_TYPES as readonly string[]).includes(value)
    ? (value as FingerprintType)
    : 'machine';
}

/**
 * Adapt /v1/me/machines rows to the Fingerprint shape the device-list UI
 * renders. Only active devices are listed; the full machine_id is preserved
 * as `fingerprint` because the Remove flow (deactivate) requires it.
 */
export function machinesToFingerprints(
  machines: MachineInfo[] | undefined
): Fingerprint[] {
  return (machines ?? [])
    .filter((m) => m.is_active)
    .map((m) => ({
      fingerprint: m.machine_id,
      type: coerceFingerprintType(m.fingerprint_type),
      last_seen: m.last_seen_at,
      ci_provider: m.ci_provider,
      ci_repo: m.ci_repo,
      container_type: m.container_type,
    }));
}
