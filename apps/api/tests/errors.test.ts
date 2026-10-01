/**
 * Tests for AppError factories in lib/errors.ts
 *
 * Regression coverage for the replimap.dev domain bug: every action/guidance
 * string that points customers somewhere must use the real, resolvable
 * replimap.com domain (replimap.dev does not resolve at all).
 */

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { Errors } from '../src/lib/errors';

function allUserFacingStrings(error: ReturnType<(typeof Errors)[keyof typeof Errors]>): string {
  return [error.message, error.action, error.guidance].filter(Boolean).join('\n');
}

describe('Errors factories - support URL domain', () => {
  it('never reference the dead replimap.dev domain', () => {
    const errors = [
      Errors.licenseNotFound(),
      Errors.licenseExpired('2026-01-01'),
      Errors.licenseCanceled('2026-01-01'),
      Errors.licensePastDue(),
      Errors.licenseRevoked(),
      Errors.machineLimitExceeded(['machine-1'], 3),
      Errors.machineChangeLimitExceeded('2026-01-01'),
      Errors.awsAccountLimitExceeded(5),
    ];

    for (const error of errors) {
      expect(allUserFacingStrings(error)).not.toContain('replimap.dev');
    }
  });

  it('licenseNotFound points to the real dashboard and pricing pages', () => {
    const error = Errors.licenseNotFound();
    expect(error.action).toContain('support@replimap.com');
    expect(error.guidance).toContain('https://replimap.com/pricing');
  });

  it('licenseExpired and licenseCanceled point to the pricing page (no /renew page exists)', () => {
    expect(Errors.licenseExpired('2026-01-01').action).toBe(
      'Renew at https://replimap.com/pricing'
    );
    expect(Errors.licenseCanceled('2026-01-01').action).toBe(
      'Resubscribe at https://replimap.com/pricing'
    );
  });

  it('licensePastDue directs to support instead of a nonexistent billing page', () => {
    const error = Errors.licensePastDue();
    expect(error.action).toBe(
      'Contact support at support@replimap.com to update your payment method'
    );
  });

  it('licenseRevoked uses the real support mailbox', () => {
    expect(Errors.licenseRevoked().action).toBe('Contact support at support@replimap.com');
  });

  it('machineLimitExceeded points to the real dashboard', () => {
    expect(Errors.machineLimitExceeded(['machine-1'], 3).action).toBe(
      'Remove a device you no longer use in the dashboard, or run `replimap license activate` again on the machine you want to use. You can also upgrade at https://www.replimap.com/pricing'
    );
  });
});

describe('CI guard: no replimap.dev references in source', () => {
  // replimap.dev does not resolve at all. This is a static source-text guard
  // (same pattern as the RATE_LIMIT_DISABLED CI check) for the files that
  // previously hardcoded the dead domain, since some of the offending
  // strings (e.g. the device-abuse action in validate-license.ts) are
  // inline literals not exposed through an exported factory.
  const guardedFiles = [
    '../src/lib/errors.ts',
    '../src/handlers/validate-license.ts',
  ];

  for (const relativePath of guardedFiles) {
    it(`${relativePath} does not reference replimap.dev`, () => {
      const source = readFileSync(join(__dirname, relativePath), 'utf-8');
      expect(source).not.toContain('replimap.dev');
    });
  }
});
