/**
 * E2E: /checkout/success must surface lookup auth failures explicitly.
 *
 * The license lookup is intercepted (no Stripe, no API, no webhook needed);
 * only Clerk test mode is required to get a signed-in session, because the
 * checkout routes are behind <RequireAuth>.
 *
 *   401 -> "could not verify this purchase" state (NOT the "payment received,
 *          still creating" timeout copy)
 *   404 -> keeps polling (pending state)
 *   5xx -> retried within the poll window; 502 then 200 shows the key;
 *          persistent 5xx ends in the "could not load" state
 */

import { test, expect } from '@playwright/test'
import {
  createTestUser,
  setupClerkForPage,
  CLERK_TEST_OTP,
} from './fixtures/test-user'

async function signUp(page: import('@playwright/test').Page) {
  await setupClerkForPage(page)
  const user = createTestUser()
  await page.goto('/sign-up')
  await page.getByLabel(/email/i).first().fill(user.email)
  await page.getByLabel(/password/i).first().fill(user.password)
  await page.getByRole('button', { name: /continue|sign up/i }).first().click()
  const otpInput = page
    .getByRole('textbox', { name: /verification code|code/i })
    .first()
  try {
    await otpInput.waitFor({ timeout: 10_000 })
    await otpInput.fill(CLERK_TEST_OTP)
    const verifyBtn = page.getByRole('button', { name: /continue|verify/i }).first()
    if (await verifyBtn.isVisible().catch(() => false)) await verifyBtn.click()
  } catch {
    // Auto-verified
  }
  await page.waitForURL(/\/dashboard/, { timeout: 30_000 })
}

test.describe('Checkout success page lookup errors', () => {
  test('401 from the lookup shows the verification error, not the timeout copy', async ({
    page,
  }) => {
    await signUp(page)
    let authHeader: string | undefined
    await page.route('**/v1/checkout/session/*/license', async (route) => {
      authHeader = route.request().headers()['authorization']
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'UNAUTHORIZED', message: 'nope' }),
      })
    })

    await page.goto('/checkout/success?session_id=cs_test_e2e401')

    await expect(
      page.getByText(/could not verify this purchase/i)
    ).toBeVisible()
    await expect(
      page.getByText(/taking longer than expected/i)
    ).toHaveCount(0)
    expect(authHeader).toMatch(/^Bearer .+/)
  })

  test('404 NOT_READY keeps the pending state', async ({ page }) => {
    await signUp(page)
    await page.route('**/v1/checkout/session/*/license', (route) =>
      route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'NOT_READY', message: 'wait' }),
      })
    )

    await page.goto('/checkout/success?session_id=cs_test_e2e404')

    await expect(page.getByText(/creating your license/i)).toBeVisible()
    await expect(page.getByText(/could not verify/i)).toHaveCount(0)
  })

  test('502 followed by 200 shows the key', async ({ page }) => {
    await signUp(page)
    let calls = 0
    await page.route('**/v1/checkout/session/*/license', (route) => {
      calls += 1
      if (calls === 1) {
        return route.fulfill({
          status: 502,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'INTERNAL_ERROR', message: 'stripe' }),
        })
      }
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          license_key: 'RM-E2E0-AAAA-BBBB-CCCC',
          plan: 'pro',
          status: 'active',
          plan_type: 'monthly',
        }),
      })
    })

    await page.goto('/checkout/success?session_id=cs_test_e2e502')

    await expect(page.locator('code').filter({ hasText: /^RM-E2E0/ }).first()).toBeVisible({
      timeout: 15_000,
    })
    await expect(page.getByText(/couldn't load your license key/i)).toHaveCount(0)
    expect(calls).toBeGreaterThanOrEqual(2)
  })

  test('persistent 502 ends in the "could not load" state, not the timeout copy', async ({
    page,
  }) => {
    test.setTimeout(90_000)
    await signUp(page)
    await page.route('**/v1/checkout/session/*/license', (route) =>
      route.fulfill({
        status: 502,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'INTERNAL_ERROR', message: 'stripe' }),
      })
    )

    await page.goto('/checkout/success?session_id=cs_test_e2e502b')

    await expect(page.getByText(/couldn't load your license key/i)).toBeVisible({
      timeout: 40_000,
    })
    await expect(page.getByText(/taking longer than expected/i)).toHaveCount(0)
  })
})
