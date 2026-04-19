/**
 * E2E: Lifetime tier checkout flow (one-time payment, not subscription).
 *
 * Covers:
 *   Sign in → /checkout?plan=pro&billing=lifetime → Stripe hosted page
 *   → fill test card 4242 → /checkout/success?session_id=X
 *   → poll resolves to license key (plan_type=lifetime) → activate API
 *
 * Differs from pro-checkout:
 *   - Stripe `mode=payment` (one-time), not `mode=subscription`
 *   - License created in checkout.session.completed, not subscription.created
 *   - License has stripe_session_id populated (lookup path A)
 */

import { test, expect } from '@playwright/test'
import {
  createTestUser,
  setupClerkForPage,
  CLERK_TEST_OTP,
} from './fixtures/test-user'

test.describe('Lifetime checkout flow', () => {
  test.setTimeout(180_000)

  test('paying user reaches success page and receives a lifetime license', async ({
    page,
    request,
  }) => {
    await setupClerkForPage(page)
    const user = createTestUser()
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8787'

    // 1. Sign up
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

    // 2. Navigate to lifetime checkout
    await page.goto('/checkout?plan=pro&billing=lifetime')

    // Price should show one-time, not /mo or /yr
    await expect(page.getByText(/one-time/i).first()).toBeVisible()

    // 3. Click "Continue to Payment"
    await page.getByRole('button', { name: /continue to payment/i }).click()

    // 4. Stripe-hosted checkout page (mode=payment)
    await page.waitForURL(/checkout\.stripe\.com/, { timeout: 30_000 })

    await page.getByRole('textbox', { name: 'Card number' }).fill('4242 4242 4242 4242')
    await page.getByRole('textbox', { name: 'Expiration' }).fill('12 / 35')
    await page.getByRole('textbox', { name: 'CVC' }).fill('123')
    await page.getByRole('textbox', { name: 'Cardholder name' }).fill('E2E Lifetime')

    const zipInput = page.getByRole('textbox', { name: /zip|postal/i })
    if (await zipInput.count()) {
      await zipInput.first().fill('94103')
    }

    const submitBtn = page.getByTestId('hosted-payment-submit-button')
    if (await submitBtn.isVisible().catch(() => false)) {
      await submitBtn.click()
    } else {
      await page
        .getByRole('button', { name: /pay|complete purchase|purchase/i })
        .first()
        .click()
    }

    // 5. Success page
    await page.waitForURL(/\/checkout\/success\?session_id=cs_/, {
      timeout: 60_000,
    })

    // 6. License key reveal — must be lifetime plan_type
    const licenseKey = page
      .locator('code')
      .filter({ hasText: /^RM-/ })
      .first()
    await expect(licenseKey).toBeVisible({ timeout: 30_000 })
    const keyText = (await licenseKey.textContent())?.trim()
    expect(keyText).toMatch(/^RM-[A-Z0-9-]+$/)

    // 7. Verify the license plan_type is 'lifetime' via the API
    const url = new URL(page.url())
    const sessionId = url.searchParams.get('session_id')
    expect(sessionId).toBeTruthy()

    const lookupRes = await request.get(
      `${apiUrl}/v1/checkout/session/${sessionId}/license`
    )
    expect(lookupRes.status()).toBe(200)
    const lookup = (await lookupRes.json()) as {
      license_key: string
      plan: string
      plan_type: string
    }
    expect(lookup.license_key).toBe(keyText)
    expect(lookup.plan).toBe('pro')
    expect(lookup.plan_type).toBe('lifetime')

    // 8. Activate the lifetime license
    const fingerprint = 'b'.repeat(32)
    const activateRes = await request.post(`${apiUrl}/v1/license/activate`, {
      data: {
        license_key: keyText,
        machine_fingerprint: fingerprint,
        machine_name: 'e2e-lifetime-machine',
        fingerprint_type: 'developer_workstation',
      },
    })
    expect(activateRes.status()).toBe(200)
    const activateBody = (await activateRes.json()) as {
      activated: boolean
      plan: string
    }
    expect(activateBody.activated).toBe(true)
    expect(activateBody.plan).toBe('pro')
  })
})
