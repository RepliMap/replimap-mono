# Deployment Guide

## Prerequisites

### Required Secrets (GitHub Repository Settings -> Secrets)

| Secret | Description | Where to get |
|--------|-------------|--------------|
| `VERCEL_TOKEN` | Vercel API token | Vercel Dashboard -> Settings -> Tokens |
| `VERCEL_ORG_ID` | Vercel organization ID | Vercel Dashboard -> Settings -> General |
| `VERCEL_PROJECT_ID_WEB` | Web project ID | Vercel Dashboard -> Project -> Settings |
| `CLOUDFLARE_API_TOKEN` | CF API token | Cloudflare Dashboard -> API Tokens |

## Platform Configuration

### Vercel (apps/web)

**CRITICAL:** In Vercel Dashboard:
1. Go to Project Settings -> General
2. Set **Root Directory** to: `apps/web`
3. Framework Preset: Next.js (auto-detected)
4. Node.js Version: 24.x

Without this setting, the relative paths in vercel.json will fail
and Vercel's build cache won't work correctly.

### Cloudflare Workers (apps/api)

**CRITICAL:** In Cloudflare Dashboard:
1. Go to Workers -> Your Worker -> Settings
2. Set **Root Directory** to: `apps/api`
3. Compatibility flags: `nodejs_compat`

Without this setting, wrangler deploy may fail to find dependencies.

## Manual Deployment

```bash
# Deploy web to Vercel
make deploy-web

# Deploy api to Cloudflare
make deploy-api
```

## Troubleshooting

### "Cannot find module '@replimap/config'"
Run: `make build-config`

### Generated files out of sync
Run: `make commit-config`

### Vercel build fails with "command not found: pnpm"
Ensure the installCommand in vercel.json includes `corepack enable`:
```json
{
  "installCommand": "cd ../.. && corepack enable && pnpm install"
}
```

### Cloudflare Workers deployment fails
1. Ensure you have the correct API token with Workers permissions
2. Check that `wrangler.toml` has the correct `main` entry point
3. Verify the worker name matches your Cloudflare configuration

## CI/CD Workflows

The monorepo includes the following GitHub Actions workflows:

- **ci.yml**: Runs on all PRs and pushes to main
  - Builds all packages
  - Runs linting and type checking
  - Verifies generated files are committed

- **deploy-web.yml**: Deploys to Vercel when apps/web or packages/config changes

- **deploy-api.yml**: Deploys to Cloudflare when apps/api or packages/config changes

## Environment Variables

### Web (apps/web)

Set in `.env.local` (never committed):

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | API endpoint URL | Yes |
| `NEXT_PUBLIC_APP_URL` | Web app URL | Yes |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key | Yes |
| `CLERK_SECRET_KEY` | Clerk server secret | Yes |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | For checkout |
| `STRIPE_SECRET_KEY` | Stripe secret key | For checkout |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | For webhooks |
| `STRIPE_PRO_MONTHLY_PRICE_ID` | Pro monthly price ID | For checkout |
| `STRIPE_PRO_ANNUAL_PRICE_ID` | Pro annual price ID | For checkout |
| `STRIPE_PRO_LIFETIME_PRICE_ID` | Pro lifetime price ID | For checkout |
| `STRIPE_TEAM_MONTHLY_PRICE_ID` | Team monthly price ID | For checkout |
| `STRIPE_TEAM_ANNUAL_PRICE_ID` | Team annual price ID | For checkout |
| `STRIPE_TEAM_LIFETIME_PRICE_ID` | Team lifetime price ID | For checkout |

### API (apps/api)

Non-secret vars in `wrangler.toml` `[vars]` section.
Secrets set via `wrangler secret put <NAME>`:

| Secret | Description | Required |
|--------|-------------|----------|
| `ADMIN_API_KEY` | Admin endpoint authentication | Yes |
| `STRIPE_SECRET_KEY` | Stripe API key | For billing |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | For billing |
| `STRIPE_PRO_LIFETIME_PRICE_ID` | Pro lifetime Stripe price | Optional |
| `STRIPE_TEAM_LIFETIME_PRICE_ID` | Team lifetime Stripe price | Optional |

### Stripe Setup

1. Create products in [Stripe Dashboard](https://dashboard.stripe.com/test/products):
   - **RepliMap Pro** — Monthly ($29), Annual ($290), Lifetime ($199)
   - **RepliMap Team** — Monthly ($99), Annual ($990), Lifetime ($499)
2. Copy price IDs into web `.env.local` and API secrets
3. Create webhook endpoint:
   - URL: `https://api.replimap.com/v1/webhooks/stripe`
   - Events: `checkout.session.completed`, `customer.subscription.updated`,
     `customer.subscription.deleted`, `invoice.payment_failed`
4. Copy webhook signing secret (`whsec_...`) into both web and API env

### Testing Stripe (Test Mode)

Use test card: `4242 4242 4242 4242`, any future expiry, any CVC.

Navigate to `/checkout?plan=pro&billing=monthly` after signing in to test the full flow.
