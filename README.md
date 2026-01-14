# RepliMap Monorepo

Cloud Infrastructure Visualization & Compliance Platform

## Structure

```
replimap-mono/
├── apps/
│   ├── web/         # Next.js frontend (Vercel)
│   ├── api/         # Hono API (Cloudflare Workers)
│   └── cli/         # Python CLI (PyPI)
├── packages/
│   └── config/      # Shared configuration (JSON → TS/Python)
└── .github/
    └── workflows/   # CI/CD pipelines
```

## Prerequisites

- Node.js 20+ (see `.nvmrc`)
- pnpm 9+
- Python 3.11+ (for CLI development)

## Getting Started

```bash
# Install dependencies
pnpm install

# Build all packages
pnpm build

# Build config package only
pnpm config:build
```

## packages/config

Shared configuration that generates TypeScript and Python code from JSON source files.

### Source Files

- `src/plans.json` - Pricing plans configuration
- `src/frameworks.json` - Compliance frameworks
- `src/resources.json` - Supported AWS resources
- `src/schema.json` - JSON Schema definitions

### Generated Files

The `dist/` directory contains auto-generated code (committed to git):

- `dist/index.ts` - TypeScript exports with full type safety
- `dist/config.py` - Python dataclasses

### Usage

**TypeScript:**
```typescript
import { PLANS, COMPLIANCE_FRAMEWORKS, isPlanName } from '@replimap/config';

const proPlan = PLANS.pro;
console.log(`Pro plan: $${proPlan.price_monthly / 100}/month`);
```

**Python:**
```python
from packages.config.dist import config

pro_plan = config.PLANS["pro"]
print(f"Pro plan: ${pro_plan.price_monthly / 100}/month")
```

### Updating Configuration

1. Edit JSON files in `packages/config/src/`
2. Run `pnpm config:build`
3. Commit the changes (including generated `dist/` files)

The CI pipeline will verify generated files are up to date.

## Configuration Loading (CLI)

The CLI uses a 4-layer configuration system:

| Priority | Source | Description |
|----------|--------|-------------|
| 1 | ENV | Environment variables (`REPLIMAP_*`) |
| 2 | Drop-in | User config files (`~/.config/replimap/*.json`) |
| 3 | Cache | Cached remote config (`~/.cache/replimap/`) |
| 4 | Bundled | Default bundled config |

See `apps/cli/replimap/config/loader.py.template` for implementation details.

## CI/CD

### CI Pipeline (`.github/workflows/ci.yml`)

- Config generation check (ensures dist files are committed)
- TypeScript type checking
- Python config validation
- Linting

### Deploy Pipeline (`.github/workflows/deploy.yml`)

Uses path-based filtering for conditional deployments:

| Component | Trigger Paths | Deploy Target |
|-----------|---------------|---------------|
| Web | `apps/web/**`, `packages/config/dist/**` | Vercel |
| API | `apps/api/**`, `packages/config/dist/**` | Cloudflare Workers |
| CLI | `apps/cli/**`, `packages/config/dist/**` | PyPI |

## Development

```bash
# Run development servers (when apps are migrated)
pnpm dev

# Type check all packages
pnpm typecheck

# Lint all packages
pnpm lint

# Clean build artifacts
pnpm clean
```

## License

Proprietary - All rights reserved
