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
- `NEXT_PUBLIC_API_URL`: API endpoint URL
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: Clerk authentication key
- Other Next.js environment variables as needed

### API (apps/api)
- Configured in `wrangler.toml` `[vars]` section
- Secrets set via `wrangler secret put`
