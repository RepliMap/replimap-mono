/**
 * E2E: lifetime plans are no longer sold (2026-11).
 *
 * Covers:
 *   - The pricing section offers only Monthly / Annual (no Lifetime, no "Early Bird").
 *   - An old /checkout?plan=pro&billing=lifetime link shows the normal Pro
 *     checkout on monthly billing, not an error page.
 *   - The API refuses billing_period=lifetime with a 400.
 *
 * Existing lifetime licenses are unaffected; they are covered by the API
 * webhook/license tests, not here.
 */

import { test, expect } from '@playwright/test'
import {
  createTestUser,
  setupClerkForPage,
  CLERK_TEST_OTP,
} from './fixtures/test-user'

test.describe('Lifetime plans removed', () => {
  test('pricing section has no lifetime option', async ({ page }) => {
    await page.goto('/#pricing')
    const pricing = page.locator('#pricing')
    await expect(pricing.getByRole('button', { name: /^monthly$/i })).toBeVisible()
    await expect(pricing.getByRole('button', { name: /annual/i })).toBeVisible()
    await expect(pricing.getByRole('button', { name: /lifetime/i })).toHaveCount(0)
    await expect(pricing.getByText(/early bird/i)).toHaveCount(0)
  })

  test('old lifetime checkout link falls back to monthly; API refuses lifetime', async ({
    page,
    request,
  }) => {
    test.setTimeout(120_000)
    await setupClerkForPage(page)
    const user = createTestUser()
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8787'
    const appUrl = process.env.E2E_BASE_URL ?? 'http://localhost:3100'

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

    await page.goto('/checkout?plan=pro&billing=lifetime')
    await expect(page.getByRole('heading', { name: /subscribe to replimap pro/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /continue to payment.*\/mo/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /lifetime/i })).toHaveCount(0)
    await expect(page.getByText(/one-time/i)).toHaveCount(0)

    const token = await page.evaluate(
      async () =>
        (
          window as unknown as {
            Clerk?: { session?: { getToken: () => Promise<string | null> } }
          }
        ).Clerk?.session?.getToken() ?? null
    )
    expect(token).toBeTruthy()

    const refused = await request.post(`${apiUrl}/v1/checkout/session`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        plan: 'pro',
        billing_period: 'lifetime',
        success_url: `${appUrl}/checkout/success`,
        cancel_url: `${appUrl}/checkout`,
      },
    })
    expect(refused.status()).toBe(400)
    expect(await refused.text()).toContain('Lifetime plans are no longer sold')
  })
})
