# RepliMap Backend API

License validation and usage tracking API for RepliMap.

## Overview

This backend provides:
- **License Validation API** - Validate license keys, check feature access
- **Usage Sync API** - Track quota usage, aggregate metrics
- **Admin API** - License management, usage reports

## Architecture

```
replimap-backend/
├── api/                    # API endpoints (FastAPI)
│   ├── licenses.py         # License validation endpoints
│   ├── usage.py            # Usage tracking endpoints
│   └── admin.py            # Admin management endpoints
├── services/               # Business logic
│   ├── license_service.py  # License validation, generation
│   └── usage_service.py    # Usage aggregation, quotas
├── database/               # Database layer
│   ├── models.py           # SQLAlchemy models
│   └── migrations/         # Alembic migrations
├── config/                 # Configuration
│   └── settings.py         # Environment-based settings
└── tests/                  # API tests
```

## Deployment Options

### Option 1: Supabase (Recommended for MVP)
- Use Supabase PostgreSQL for database
- Deploy API as Supabase Edge Functions or external service
- Built-in Row Level Security

### Option 2: AWS Lambda + API Gateway
- Serverless deployment
- Good for production scale
- Use RDS PostgreSQL or DynamoDB

### Option 3: Docker + Any Cloud
- Self-contained deployment
- Deploy to ECS, Cloud Run, Fly.io, etc.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Set environment variables
export DATABASE_URL="postgresql://..."
export JWT_SECRET="your-secret-key"
export STRIPE_SECRET_KEY="sk_..."  # For payment integration

# Run migrations
alembic upgrade head

# Start development server
uvicorn api.main:app --reload
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JWT_SECRET` | Secret for JWT signing | Yes |
| `STRIPE_SECRET_KEY` | Stripe API key for payments | No |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | No |
| `CORS_ORIGINS` | Allowed CORS origins | No |

## API Endpoints

### License Validation

```
POST /api/v1/licenses/validate
{
  "license_key": "RP-XXXX-XXXX-XXXX-XXXX",
  "machine_id": "abc123",
  "product_version": "1.0.0"
}

Response:
{
  "valid": true,
  "plan": "team",
  "features": ["async_scanning", "unlimited_resources", ...],
  "expires_at": "2025-12-31T23:59:59Z",
  "max_activations": 5,
  "current_activations": 2
}
```

### Usage Sync

```
POST /api/v1/usage/sync
{
  "license_key": "RP-XXXX-XXXX-XXXX-XXXX",
  "machine_id": "abc123",
  "usage": {
    "scans_count": 15,
    "resources_scanned": 1250,
    "terraform_generations": 8
  },
  "period": "2025-01"
}

Response:
{
  "synced": true,
  "quotas": {
    "scans_remaining": 85,
    "resources_remaining": null  // unlimited
  }
}
```

## Database Schema

See `database/models.py` for full schema. Key tables:
- `licenses` - License records with plan, features, expiry
- `activations` - Machine activations per license
- `usage_records` - Usage tracking per license/period
- `customers` - Customer information (for admin)
