/**
 * Fingerprint Detection and Validation
 *
 * Supports three fingerprint types:
 * - machine: Standard machine (MAC + hostname hash)
 * - ci: CI/CD environment (provider:repo hash)
 * - container: Container environment (volume UUID or workspace ID)
 */

import type { FingerprintType } from './ed25519';

// ============================================================================
// Types
// ============================================================================

export interface MachineInfo {
  platform?: string;
  platform_version?: string;
  platform_release?: string;
  python_version?: string;
  hostname?: string;
  ci_provider?: string;
  ci_repo?: string;
  ci_run_id?: string;
  container_type?: string;
  workspace_id?: string;
}

export interface FingerprintMetadata {
  type: FingerprintType;
  ci_provider?: string;
  ci_repo?: string;
  container_type?: string;
}

// ============================================================================
// Detection
// ============================================================================

/**
 * Detect fingerprint type from machine info and explicit type.
 *
 * Priority:
 * 1. Explicit type (if provided)
 * 2. CI detection (if ci_provider present)
 * 3. Container detection (if container_type present)
 * 4. Default to machine
 */
export function detectFingerprintType(
  machineInfo?: MachineInfo,
  explicitType?: FingerprintType
): FingerprintMetadata {
  // 1. If explicitly specified, use that
  if (explicitType) {
    return buildMetadata(explicitType, machineInfo);
  }

  // 2. Detect CI environment
  if (machineInfo?.ci_provider) {
    return {
      type: 'ci',
      ci_provider: machineInfo.ci_provider,
      ci_repo: machineInfo.ci_repo,
    };
  }

  // 3. Detect container environment
  if (machineInfo?.container_type) {
    return {
      type: 'container',
      container_type: machineInfo.container_type,
    };
  }

  // 4. Default to machine type
  return { type: 'machine' };
}

function buildMetadata(
  type: FingerprintType,
  machineInfo?: MachineInfo
): FingerprintMetadata {
  switch (type) {
    case 'ci':
      return {
        type: 'ci',
        ci_provider: machineInfo?.ci_provider,
        ci_repo: machineInfo?.ci_repo,
      };
    case 'container':
      return {
        type: 'container',
        container_type: machineInfo?.container_type,
      };
    default:
      return { type: 'machine' };
  }
}

// ============================================================================
// Validation
// ============================================================================

/**
 * Validate fingerprint format (32 char lowercase hex).
 */
export function validateFingerprint(fingerprint: string): boolean {
  return /^[a-f0-9]{32}$/.test(fingerprint);
}

/**
 * Validate fingerprint type.
 */
export function isValidFingerprintType(type: string): type is FingerprintType {
  return ['machine', 'ci', 'container'].includes(type);
}

/**
 * Generate CI stable identifier.
 */
export function getCIStableIdentifier(provider: string, repo: string): string {
  return `${provider}:${repo}`;
}

// ============================================================================
// Display Helpers
// ============================================================================

/**
 * Get fingerprint type display label.
 */
export function getFingerprintTypeLabel(type: FingerprintType): string {
  const labels: Record<FingerprintType, string> = {
    machine: 'Local Machine',
    ci: 'CI/CD Pipeline',
    container: 'Container/Cloud IDE',
  };
  return labels[type] ?? 'Unknown';
}

/**
 * Get fingerprint type icon.
 */
export function getFingerprintTypeIcon(type: FingerprintType): string {
  const icons: Record<FingerprintType, string> = {
    machine: '💻',
    ci: '🔄',
    container: '📦',
  };
  return icons[type] ?? '❓';
}

/**
 * Get short display string for a fingerprint.
 * Shows first 8 and last 4 characters.
 */
export function truncateFingerprint(fingerprint: string): string {
  if (fingerprint.length < 12) {
    return fingerprint;
  }
  return `${fingerprint.slice(0, 8)}...${fingerprint.slice(-4)}`;
}
