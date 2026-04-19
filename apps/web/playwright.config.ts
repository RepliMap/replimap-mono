import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config for RepliMap web e2e tests.
 *
 * By default, `pnpm e2e` boots `next dev` via webServer. For tests that
 * also need the API + Stripe webhooks, use scripts/e2e-commercial-flow.sh
 * which spawns wrangler dev + stripe listen alongside.
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3000',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
