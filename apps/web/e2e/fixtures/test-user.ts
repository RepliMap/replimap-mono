/**
 * Clerk-aware test fixtures.
 *
 * Uses Clerk's testing token to bypass email OTP and sign-up rate limits.
 * The token itself is read from CLERK_TESTING_TOKEN env var — see
 * e2e/README.md for setup.
 */

import { randomUUID } from 'node:crypto'
import type { Page } from '@playwright/test'

export interface TestUser {
  email: string
  password: string
  uuid: string
}

/**
 * Generate a unique test user. Email format stays under replimap-test.dev
 * so it never collides with real users in the Clerk project.
 */
export function createTestUser(): TestUser {
  const uuid = randomUUID().replace(/-/g, '').slice(0, 10)
  return {
    uuid,
    email: `e2e+${uuid}@replimap-test.dev`,
    // Strong enough to pass Clerk's default password policy
    password: `E2e-Test-${uuid}!`,
  }
}

/**
 * Attach Clerk's testing token to every page navigation so Clerk's test
 * backend accepts our automated sign-ups. Fails fast if the token isn't
 * configured — running these specs without it will hit real rate limits.
 */
export function requireClerkTestingToken(): string {
  const token = process.env.CLERK_TESTING_TOKEN
  if (!token) {
    throw new Error(
      'CLERK_TESTING_TOKEN is required for e2e tests. ' +
        'See apps/web/e2e/README.md for how to obtain one.'
    )
  }
  return token
}

/**
 * Set up the Clerk testing token for a Page. Must be called before any
 * sign-in/sign-up navigation.
 *
 * Clerk reads the token via the __clerk_testing_token query param on
 * requests to its API; we inject it by setting a cookie Clerk respects.
 */
export async function setupClerkTestingToken(page: Page): Promise<void> {
  const token = requireClerkTestingToken()
  await page.context().addCookies([
    {
      name: '__clerk_testing_token',
      value: token,
      domain: 'localhost',
      path: '/',
      httpOnly: false,
      secure: false,
    },
  ])
}
