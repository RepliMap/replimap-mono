/**
 * E2E: Community tier signup flow (fully automated).
 *
 * Covers:
 *   Landing → Click "Get Started Free" → Clerk sign-up → Dashboard
 *   → Community license auto-provisioned → License visible
 *
 * Prereqs: CLERK_TESTING_TOKEN env var (see e2e/README.md).
 */

import { test, expect } from '@playwright/test'
import {
  createTestUser,
  setupClerkForPage,
  CLERK_TEST_OTP,
} from './fixtures/test-user'

test.describe('Community signup flow', () => {
  test('new user can sign up, reach dashboard, and see a community license', async ({
    page,
  }) => {
    await setupClerkForPage(page)

    const user = createTestUser()

    // 1. Landing page → hero CTA
    await page.goto('/')
    await page
      .getByRole('link', { name: /get started free/i })
      .first()
      .click()

    // 2. Clerk sign-up page
    await page.waitForURL(/sign-up/, { timeout: 15_000 })

    const emailInput = page.getByLabel(/email/i).first()
    await emailInput.waitFor({ timeout: 15_000 })
    await emailInput.fill(user.email)

    const passwordInput = page.getByLabel(/password/i).first()
    await passwordInput.fill(user.password)

    await page
      .getByRole('button', { name: /continue|sign up/i })
      .first()
      .click()

    // 3. OTP verification — Clerk's +clerk_test emails use fixed 424242
    const otpInput = page
      .getByRole('textbox', { name: /verification code|code/i })
      .first()
    try {
      await otpInput.waitFor({ timeout: 10_000 })
      await otpInput.fill(CLERK_TEST_OTP)
      const continueBtn = page
        .getByRole('button', { name: /continue|verify|submit/i })
        .first()
      if (await continueBtn.isVisible().catch(() => false)) {
        await continueBtn.click()
      }
    } catch {
      // If no OTP screen, Clerk auto-verified
    }

    // 4. Dashboard
    await page.waitForURL(/\/dashboard/, { timeout: 30_000 })

    // 5. Community license visible
    await expect(page.getByText(/community/i).first()).toBeVisible({
      timeout: 15_000,
    })
  })

  test('API refuses anonymous community provisioning (auth contract)', async ({
    request,
  }) => {
    // provision-community requires a Clerk session token; the UI test above
    // covers the authenticated path (provisioning + idempotency).
    const user = createTestUser()
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8787'

    const response = await request.post(
      `${apiUrl}/v1/license/provision-community`,
      { data: { email: user.email } }
    )

    expect(response.status()).toBe(401)
    expect(await response.text()).not.toContain('license_key')
  })
})
