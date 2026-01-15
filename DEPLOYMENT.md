# Deployment Guide

## Prerequisites

### Required Secrets (GitHub Repository Settings -> Secrets)

| Secret | Description | Where to get |
|--------|-------------|--------------|
| `VERCEL_TOKEN` | Vercel API token | Vercel Dashboard -> Settings -> Tokens |
| `VERCEL_ORG_ID` | Vercel organization ID | Vercel Dashboard -> Settings -> General |
| `VERCEL_PROJECT_ID_WEB` | Web project ID | Vercel Dashboard -> Project -> Settings |
| `CLOUDFLARE_API_TOKEN` | CF API token | Cloudflare Dashboard -> API Tokens |
| `PYPI_API_TOKEN` | PyPI upload token | PyPI -> Account Settings -> API tokens |

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

### PyPI (apps/cli)

CLI releases are triggered by git tags:
```bash
# Create and push a release tag
make tag-cli VERSION=0.5.0
```

## PyPI OIDC Trusted Publishing Setup

OIDC (OpenID Connect) eliminates the need for long-lived API tokens. Configure once on PyPI:

### Step 1: Create Publisher on PyPI

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new "pending publisher" with:
   - **PyPI Project Name**: `replimap`
   - **Owner**: `RepliMap`
   - **Repository**: `replimap-mono`
   - **Workflow name**: `release-cli.yml`
   - **Environment name**: `pypi`

3. Repeat for TestPyPI at https://test.pypi.org/manage/account/publishing/
   - **Environment name**: `testpypi`

### Step 2: Create GitHub Environments

1. Go to Repository Settings -> Environments
2. Create environment `pypi`:
   - Add protection rule: Required reviewers (optional)
   - Add protection rule: Restrict to tags matching `cli-v*`
3. Create environment `testpypi`:
   - No special restrictions needed

### Why OIDC?

| Aspect | API Token | OIDC |
|--------|-----------|------|
| Secret Management | Manual rotation needed | No secrets to manage |
| Scope | Can be overly broad | Scoped to specific workflow |
| Audit | Limited | Full GitHub audit trail |
| Revocation | Manual | Automatic |

## Manual Deployment

```bash
# Deploy web to Vercel
make deploy-web

# Deploy api to Cloudflare
make deploy-api

# Release CLI to PyPI
make release-cli
```

## Troubleshooting

### "Cannot find module '@replimap/config'"
Run: `make build-config`

### Generated files out of sync
Run: `make commit-config`

### CLI config import fails
Run: `make sync-cli-config`

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
  - Tests CLI config loading

- **deploy-web.yml**: Deploys to Vercel when apps/web or packages/config changes

- **deploy-api.yml**: Deploys to Cloudflare when apps/api or packages/config changes

- **release-cli.yml**: Publishes to PyPI when a `cli-v*` tag is pushed

## Environment Variables

### Web (apps/web)
- `NEXT_PUBLIC_API_URL`: API endpoint URL
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: Clerk authentication key
- Other Next.js environment variables as needed

### API (apps/api)
- Configured in `wrangler.toml` `[vars]` section
- Secrets set via `wrangler secret put`

### CLI (apps/cli)
- No build-time environment variables required
- Runtime configuration via CLI flags or config files
