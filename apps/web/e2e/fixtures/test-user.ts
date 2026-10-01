/**
 * Clerk-aware test fixtures.
 *
 * Uses @clerk/testing to bypass Clerk bot protection in Playwright runs
 * (requires CLERK_SECRET_KEY + NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY in env).
 *
 * For email verification bypass, Clerk recognises the literal substring
 * `+clerk_test` in the local-part and uses a fixed OTP (`424242`) instead
 * of sending a real email — see https://clerk.com/docs/testing/test-emails
 */

import { randomUUID } from 'node:crypto'
import { setupClerkTestingToken } from '@clerk/testing/playwright'
import type { Page } from '@playwright/test'

export interface TestUser {
  email: string
  password: string
  uuid: string
}

/**
 * Clerk's fixed OTP code for `+clerk_test` email addresses.
 */
export const CLERK_TEST_OTP = '424242'

/**
 * Generate a unique test user whose email bypasses Clerk's OTP flow.
 * `+clerk_test` in the local-part tells Clerk not to deliver a real email;
 * the OTP is always 424242 in that case.
 */
export function createTestUser(): TestUser {
  const uuid = randomUUID().replace(/-/g, '').slice(0, 10)
  return {
    uuid,
    email: `e2e+clerk_test+${uuid}@replimap-test.dev`,
    password: `E2e-Test-${uuid}!`,
  }
}

/**
 * Attach Clerk's testing token to a Page so sign-up / sign-in requests
 * bypass bot-protection rate limits. Call this before any navigation
 * into `/sign-up` or `/sign-in`.
 */
export async function setupClerkForPage(page: Page): Promise<void> {
  await setupClerkTestingToken({ page })
}
