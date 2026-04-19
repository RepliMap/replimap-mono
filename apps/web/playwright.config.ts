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
  globalSetup: require.resolve('./e2e/global-setup.ts'),
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3100',
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
    command: 'pnpm dev --port 3100',
    url: 'http://localhost:3100',
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
    env: {
      // Override NEXT_PUBLIC_APP_URL so success_url points back to the test port
      NEXT_PUBLIC_APP_URL: 'http://localhost:3100',
    },
  },
})
