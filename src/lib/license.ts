/**
 * License key generation and validation utilities
 */

import { LICENSE_KEY_PATTERN, MACHINE_ID_PATTERN, AWS_ACCOUNT_ID_PATTERN } from './constants';
import { Errors } from './errors';

// ============================================================================
// License Key Generation
// ============================================================================

/**
 * Generate a random license key
 * Format: RM-XXXX-XXXX-XXXX-XXXX
 */
export function generateLicenseKey(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  const segments: string[] = [];

  for (let i = 0; i < 4; i++) {
    let segment = '';
    for (let j = 0; j < 4; j++) {
      segment += chars[Math.floor(Math.random() * chars.length)];
    }
    segments.push(segment);
  }

  return `RM-${segments.join('-')}`;
}

/**
 * Generate a UUID v4
 */
export function generateId(): string {
  return crypto.randomUUID();
}

// ============================================================================
// Validation
// ============================================================================

/**
 * Validate license key format
 * Throws AppError if invalid
 */
export function validateLicenseKey(licenseKey: string): void {
  if (!licenseKey || typeof licenseKey !== 'string') {
    throw Errors.invalidLicenseFormat();
  }

  const normalized = licenseKey.trim().toUpperCase();
  if (!LICENSE_KEY_PATTERN.test(normalized)) {
    throw Errors.invalidLicenseFormat();
  }
}

/**
 * Normalize license key to uppercase
 */
export function normalizeLicenseKey(licenseKey: string): string {
  return licenseKey.trim().toUpperCase();
}

/**
 * Validate machine ID format
 * Throws AppError if invalid
 */
export function validateMachineId(machineId: string): void {
  if (!machineId || typeof machineId !== 'string') {
    throw Errors.invalidMachineFormat();
  }

  const normalized = machineId.trim().toLowerCase();
  if (!MACHINE_ID_PATTERN.test(normalized)) {
    throw Errors.invalidMachineFormat();
  }
}

/**
 * Normalize machine ID to lowercase
 */
export function normalizeMachineId(machineId: string): string {
  return machineId.trim().toLowerCase();
}

/**
 * Validate AWS account ID format
 */
export function validateAwsAccountId(accountId: string): boolean {
  if (!accountId || typeof accountId !== 'string') {
    return false;
  }
  return AWS_ACCOUNT_ID_PATTERN.test(accountId.trim());
}

/**
 * Truncate machine ID for display (first 8 chars + ...)
 */
export function truncateMachineId(machineId: string): string {
  if (machineId.length <= 11) return machineId;
  return `${machineId.substring(0, 8)}...`;
}

// ============================================================================
// Date/Time Helpers
// ============================================================================

/**
 * Get ISO timestamp for now
 */
export function nowISO(): string {
  return new Date().toISOString();
}

/**
 * Get ISO timestamp for cache expiry (now + hours)
 */
export function cacheUntilISO(hours: number): string {
  const date = new Date();
  date.setHours(date.getHours() + hours);
  return date.toISOString();
}

/**
 * Get ISO timestamp for start of next month (for machine change reset)
 */
export function nextMonthStartISO(): string {
  const date = new Date();
  date.setMonth(date.getMonth() + 1, 1);
  date.setHours(0, 0, 0, 0);
  return date.toISOString();
}

/**
 * Check if a date string is in the past
 */
export function isPast(dateStr: string | null): boolean {
  if (!dateStr) return false;
  return new Date(dateStr) < new Date();
}

/**
 * Check if a date string is in the future
 */
export function isFuture(dateStr: string | null): boolean {
  if (!dateStr) return false;
  return new Date(dateStr) > new Date();
}

/**
 * Format date for display
 */
export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Convert Unix timestamp to ISO string
 */
export function timestampToISO(timestamp: number): string {
  return new Date(timestamp * 1000).toISOString();
}
