/**
 * E2E: Pro tier checkout flow (requires stripe listen + local API).
 *
 * Covers:
 *   Sign in → /checkout?plan=pro&billing=monthly → Stripe hosted page
 *   → fill test card 4242 → /checkout/success?session_id=X
 *   → poll resolves to license key → activate API accepts the key
 *
 * Prereqs:
 *   - CLERK_TESTING_TOKEN env var
 *   - `stripe listen --forward-to localhost:8787/v1/webhooks/stripe` running
 *   - `apps/api` (wrangler dev) running on :8787
 *   - `apps/web` (next dev) running on :3000
 *
 * The harness script `scripts/e2e-commercial-flow.sh` sets all of this up.
 */

import { test, expect } from '@playwright/test'
import {
  createTestUser,
  setupClerkForPage,
  CLERK_TEST_OTP,
} from './fixtures/test-user'

test.describe('Pro checkout flow', () => {
  test.setTimeout(180_000)

  test('paying user reaches success page and receives a license key', async ({
    page,
    request,
  }) => {
    await setupClerkForPage(page)
    const user = createTestUser()
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8787'

    // 1. Sign up first so Clerk session exists for /checkout
    await page.goto('/sign-up')
    await page.getByLabel(/email/i).first().fill(user.email)
    await page.getByLabel(/password/i).first().fill(user.password)
    await page.getByRole('button', { name: /continue|sign up/i }).first().click()

    // OTP (Clerk test email → fixed 424242)
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

    // 2. Navigate to checkout
    await page.goto('/checkout?plan=pro&billing=monthly')
    await expect(page.getByRole('heading', { level: 1 })).toContainText(
      /subscribe.*pro/i
    )

    // 3. Click "Continue to Payment"
    await page
      .getByRole('button', { name: /continue to payment/i })
      .click()

    // 4. Stripe-hosted checkout page
    await page.waitForURL(/checkout\.stripe\.com/, { timeout: 30_000 })

    // Email is pre-filled by our createCheckoutSession call — skip it.
    // Card fields are accessible textboxes (no iframe wrapper needed on
    // Stripe-hosted checkout, only on Elements-embedded).
    await page
      .getByRole('textbox', { name: 'Card number' })
      .fill('4242 4242 4242 4242')
    await page.getByRole('textbox', { name: 'Expiration' }).fill('12 / 35')
    await page.getByRole('textbox', { name: 'CVC' }).fill('123')
    await page
      .getByRole('textbox', { name: 'Cardholder name' })
      .fill('E2E Test')

    // Country defaults to US; ZIP may appear after selecting US
    const zipInput = page.getByRole('textbox', { name: /zip|postal/i })
    if (await zipInput.count()) {
      await zipInput.first().fill('94103')
    }

    // Submit: Stripe-hosted page uses data-testid=hosted-payment-submit-button,
    // but fall back to the "Subscribe" button name in case the markup changes
    const submitBtn = page.getByTestId('hosted-payment-submit-button')
    if (await submitBtn.isVisible().catch(() => false)) {
      await submitBtn.click()
    } else {
      await page
        .getByRole('button', { name: /subscribe|pay|start.*subscription/i })
        .first()
        .click()
    }

    // 5. Redirect back to success page
    await page.waitForURL(/\/checkout\/success\?session_id=cs_/, {
      timeout: 60_000,
    })

    // 6. License key reveal (polling handles webhook lag)
    const licenseKey = page
      .locator('code')
      .filter({ hasText: /^RM-/ })
      .first()
    await expect(licenseKey).toBeVisible({ timeout: 30_000 })
    const keyText = (await licenseKey.textContent())?.trim()
    expect(keyText).toMatch(/^RM-[A-Z0-9-]+$/)

    // 7. Activate the license via API — end-to-end proof
    const fingerprint = 'a'.repeat(32) // valid 32-char hex
    const activateRes = await request.post(
      `${apiUrl}/v1/license/activate`,
      {
        data: {
          license_key: keyText,
          machine_fingerprint: fingerprint,
          machine_name: 'e2e-test-machine',
          fingerprint_type: 'developer_workstation',
        },
      }
    )
    expect(activateRes.status()).toBe(200)
    const activateBody = (await activateRes.json()) as {
      activated: boolean
      license_blob: string
      plan: string
    }
    expect(activateBody.activated).toBe(true)
    expect(activateBody.license_blob).toBeTruthy()
    expect(activateBody.plan).toBe('pro')
  })
})
