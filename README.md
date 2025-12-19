# RepliMap

[![Python versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://github.com/RepliMap/replimap)
[![Tests](https://github.com/RepliMap/replimap/actions/workflows/test.yml/badge.svg)](https://github.com/RepliMap/replimap/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)

**AWS Infrastructure Staging Cloner**

> Point at your Production AWS and generate cost-optimized Staging Terraform in minutes.

🔒 **Read-only mode** | 📍 **All data stays local** | ⚡ **Minutes, not hours**

## Overview

RepliMap scans your AWS resources, builds a dependency graph, and generates Infrastructure-as-Code to replicate your environment with intelligent transformations:

- **Instance Downsizing**: Automatically reduces EC2/RDS instance sizes for cost savings
- **Environment Renaming**: Transforms names from `prod` to `staging`
- **Sensitive Data Sanitization**: Removes secrets, passwords, and hardcoded credentials
- **Dependency Awareness**: Understands VPC → Subnet → EC2 relationships

## Installation

### Recommended: pipx (isolated environment)

```bash
# Install pipx if you don't have it
brew install pipx && pipx ensurepath  # macOS
# or: pip install --user pipx && pipx ensurepath  # Linux

# Install RepliMap
pipx install replimap

# Verify installation
replimap --version

# Update later
pipx upgrade replimap
```

### Alternative: pip

```bash
pip install replimap
```

### Alternative: uv

```bash
uv pip install replimap
```

### Docker (no Python required)

```bash
# Pull the image
docker pull replimap/replimap:latest

# Run with AWS credentials
docker run -v ~/.aws:/root/.aws replimap/replimap scan --profile prod --region us-east-1
```

## Quick Start

### 1. Verify Installation

```bash
replimap --version
```

### 2. Scan Your AWS Environment

```bash
# Basic scan (scans all resources in region)
replimap scan --profile prod --region us-east-1

# Scan a specific VPC only
replimap scan --profile prod --scope vpc:vpc-12345678

# Scan resources by tag (e.g., Application=MyApp)
replimap scan --profile prod --entry tag:Application=MyApp

# Scan starting from an entry point (e.g., ALB)
replimap scan --profile prod --entry alb:my-app-alb

# Use cached results for faster incremental scans
replimap scan --profile prod --cache
```

### 3. Generate Infrastructure-as-Code

```bash
# Preview what will be generated
replimap clone --profile prod --mode dry-run

# Generate Terraform files
replimap clone --profile prod --output-dir ./staging-tf --mode generate

# Generate with custom transformations
replimap clone --profile prod --output-dir ./staging-tf \
  --rename-pattern "prod:staging" \
  --downsize \
  --mode generate
```

### 4. Apply to Your Staging Account

```bash
cd ./staging-tf

# Quick validation (no AWS credentials needed)
make quick-validate

# Or use the test script
./test-terraform.sh

# Full workflow with Makefile
make init                    # Initialize Terraform
make plan                    # Plan changes (outputs tfplan.txt)
make apply                   # Apply the plan

# Alternative: manual Terraform commands
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### 5. Available Makefile Targets

The generated Terraform includes a comprehensive Makefile:

```bash
make help                    # Show all targets
make plan                    # Plan and save to tfplan + tfplan.txt
make plan-target TARGET=...  # Plan specific resource
make plan-json               # Plan with JSON output
make apply                   # Apply saved plan
make destroy                 # Destroy (requires confirmation)
make state-list              # List resources in state
make clean                   # Remove generated files
```

### 6. Check License & Usage

```bash
# View license status
replimap license status

# View usage statistics
replimap license usage

# Activate a license key
replimap license activate TEAM-XXXX-XXXX-XXXX
```

## Graph-Based Selection Engine

RepliMap uses intelligent graph traversal instead of simple filtering. This ensures complete, working infrastructure clones.

### Selection Modes

```bash
# VPC Scope - Select everything in a VPC
replimap scan --profile prod --scope vpc:vpc-12345678
replimap scan --profile prod --scope vpc-name:Production*

# Entry Point - Start from a resource and follow dependencies
replimap scan --profile prod --entry alb:my-app-alb
replimap scan --profile prod --entry tag:Application=MyApp

# Tag-Based - Select by tags
replimap scan --profile prod --tag Environment=Production
```

### YAML Configuration (Advanced)

For complex selection scenarios, use a YAML config file:

```yaml
# selection.yaml
selection:
  mode: entry_point
  entry_points:
    - type: alb
      name: my-app-*
  dependency_direction: both
  max_depth: 5
  boundary_config:
    network_boundaries:
      - transit_gateway
      - vpc_peering
    identity_boundaries:
      - iam_role
  clone_mode: isolated
  exclusions:
    types:
      - cloudwatch_log_group
    patterns:
      - "*-backup-*"
```

```bash
replimap scan --profile prod --config selection.yaml
```

### Boundary Handling

RepliMap intelligently handles infrastructure boundaries:

| Boundary Type | Resources | Default Behavior |
|---------------|-----------|------------------|
| Network | Transit Gateway, VPC Peering | Create as data source |
| Identity | IAM Roles, Policies | Reference existing |
| Global | Route53, CloudFront | Create variables |

## Output Formats

| Format | Plan Required | Status |
|--------|---------------|--------|
| Terraform HCL | Free+ | ✅ Available |
| CloudFormation YAML | Solo+ | ✅ Available |
| Pulumi Python | Pro+ | ✅ Available |

## Supported Resources (24 Types)

### Core Infrastructure
| Resource Type | Scan | Transform | Generate |
|--------------|------|-----------|----------|
| VPC | ✅ | ✅ | ✅ |
| Subnets | ✅ | ✅ | ✅ |
| Security Groups | ✅ | ✅ | ✅ |
| Internet Gateway | ✅ | ✅ | ✅ |
| NAT Gateway | ✅ | ✅ | ✅ |
| Route Tables | ✅ | ✅ | ✅ |
| VPC Endpoints | ✅ | ✅ | ✅ |

### Compute
| Resource Type | Scan | Transform | Generate |
|--------------|------|-----------|----------|
| EC2 Instances | ✅ | ✅ | ✅ |
| Launch Templates | ✅ | ✅ | ✅ |
| Auto Scaling Groups | ✅ | ✅ | ✅ |
| Application Load Balancers | ✅ | ✅ | ✅ |
| Network Load Balancers | ✅ | ✅ | ✅ |
| Target Groups | ✅ | ✅ | ✅ |
| LB Listeners | ✅ | ✅ | ✅ |

### Database
| Resource Type | Scan | Transform | Generate |
|--------------|------|-----------|----------|
| RDS Instances | ✅ | ✅ | ✅ |
| DB Subnet Groups | ✅ | ✅ | ✅ |
| DB Parameter Groups | ✅ | ✅ | ✅ |
| ElastiCache Clusters | ✅ | ✅ | ✅ |
| ElastiCache Subnet Groups | ✅ | ✅ | ✅ |

### Storage & Messaging
| Resource Type | Scan | Transform | Generate |
|--------------|------|-----------|----------|
| S3 Buckets | ✅ | ✅ | ✅ |
| S3 Bucket Policies | ✅ | ✅ | ✅ |
| EBS Volumes | ✅ | ✅ | ✅ |
| SQS Queues | ✅ | ✅ | ✅ |
| SNS Topics | ✅ | ✅ | ✅ |

## Pricing

| Plan | Monthly | Resources/Scan | Scans/Month | AWS Accounts |
|------|---------|----------------|-------------|--------------|
| **Free** | $0 | 5 | 3 | 1 |
| **Solo** | $49 | Unlimited | Unlimited | 1 |
| **Pro** | $99 | Unlimited | Unlimited | 3 |
| **Team** | $199 | Unlimited | Unlimited | 10 |
| **Enterprise** | $499+ | Unlimited | Unlimited | Unlimited |

### Feature Matrix

| Feature | Free | Solo | Pro | Team | Enterprise |
|---------|------|------|-----|------|------------|
| Terraform Output | ✅ | ✅ | ✅ | ✅ | ✅ |
| CloudFormation Output | ❌ | ✅ | ✅ | ✅ | ✅ |
| Pulumi Output | ❌ | ❌ | ✅ | ✅ | ✅ |
| Async Scanning | ❌ | ✅ | ✅ | ✅ | ✅ |
| Custom Templates | ❌ | ❌ | ✅ | ✅ | ✅ |
| Web Dashboard | ❌ | ❌ | ✅ | ✅ | ✅ |
| Team Collaboration | ❌ | ❌ | ❌ | ✅ | ✅ |
| SSO Integration | ❌ | ❌ | ❌ | ❌ | ✅ |
| Audit Logs | ❌ | ❌ | ❌ | ❌ | ✅ |

## License Management

```bash
# Activate a license key
replimap license activate SOLO-XXXX-XXXX-XXXX

# Check current status
replimap license status

# View usage statistics
replimap license usage

# Deactivate license
replimap license deactivate --yes
```

## CLI Reference

```bash
# Show version
replimap --version

# Scan command
replimap scan [OPTIONS]
  --profile, -p TEXT    AWS profile name
  --region, -r TEXT     AWS region to scan [default: us-east-1]
  --output, -o PATH     Output path for graph JSON
  --verbose, -V         Enable verbose logging

# Clone command
replimap clone [OPTIONS]
  --profile, -p TEXT       AWS source profile name
  --region, -r TEXT        AWS region to scan [default: us-east-1]
  --output-dir, -o PATH    Output directory [default: ./terraform]
  --mode, -m TEXT          Mode: 'dry-run' or 'generate' [default: dry-run]
  --downsize/--no-downsize Enable instance downsizing [default: downsize]
  --rename-pattern TEXT    Renaming pattern, e.g., 'prod:stage'

# Load command
replimap load GRAPH_FILE

# License commands
replimap license activate KEY
replimap license status
replimap license usage
replimap license deactivate [--yes]

# Credential cache management
replimap cache status      # Show cached credentials
replimap cache clear       # Clear credential cache

# List AWS profiles
replimap profiles
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REPLIMAP_DEV_MODE` | `false` | Enable dev mode (bypasses license limits) |
| `REPLIMAP_MAX_WORKERS` | `4` | Max parallel scanner threads |
| `REPLIMAP_MAX_RETRIES` | `5` | Max retries for AWS rate limiting |
| `REPLIMAP_RETRY_DELAY` | `1.0` | Base delay (seconds) for retry backoff |
| `REPLIMAP_MAX_DELAY` | `30.0` | Maximum delay (seconds) between retries |

### Dev Mode

For local development and testing, enable dev mode to bypass license restrictions:

```bash
# Enable dev mode (unlimited resources, parallel scanning, all outputs)
export REPLIMAP_DEV_MODE=1

# Or inline with command
REPLIMAP_DEV_MODE=1 replimap scan --profile prod

# Values accepted: 1, true, yes (case-insensitive)
```

### AWS Credential Caching

RepliMap caches MFA-authenticated credentials for 12 hours to avoid repeated prompts:

```bash
# View cached credentials
replimap cache status

# Clear cache when switching accounts
replimap cache clear

# Disable cache for a single command
replimap scan --profile prod --no-cache
```

### Parallel Scanning

Scanners run in parallel for faster execution (requires Solo+ plan or dev mode):

- Default: 4 parallel workers
- Configure with `REPLIMAP_MAX_WORKERS` environment variable
- Free tier runs scanners sequentially

### AWS Rate Limiting

Built-in retry with exponential backoff handles AWS throttling automatically:

- Retries on: `Throttling`, `RequestLimitExceeded`, `TooManyRequestsException`, etc.
- Exponential backoff: 1s → 2s → 4s → 8s → 16s (up to 30s max)
- Configurable via environment variables

## Security

RepliMap is designed with security as a priority:

- **Read-Only**: Only requires read permissions to AWS resources
- **Local Processing**: All data processing happens on your machine
- **No Data Upload**: Your infrastructure data never leaves your environment
- **Minimal Permissions**: See [IAM_POLICY.md](./IAM_POLICY.md) for recommended policy

## Architecture

RepliMap uses a **graph-based engine**:

```
┌─────────────┐    ┌─────────────┐    ┌───────────────┐    ┌────────────┐
│   Scanners  │───▶│ Graph Engine│───▶│ Transformers  │───▶│  Renderers │
│  (AWS API)  │    │ (NetworkX)  │    │  (Pipeline)   │    │(Terraform) │
└─────────────┘    └─────────────┘    └───────────────┘    └────────────┘
```

1. **Scanners**: Query AWS APIs for VPC, EC2, RDS, S3 resources
2. **Graph Engine**: Build dependency graph with NetworkX
3. **Transformers**: Apply sanitization, downsizing, renaming
4. **Renderers**: Generate Terraform/CloudFormation/Pulumi code

## Development

```bash
# Clone repository
git clone https://github.com/replimap/replimap.git
cd replimap

# Install with uv (recommended)
uv sync --all-extras --dev

# Run tests
uv run pytest tests/ -v

# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy replimap
```

## Project Structure

```
replimap/
├── replimap/
│   ├── __init__.py
│   ├── main.py              # Typer CLI entry point
│   ├── core/
│   │   ├── graph_engine.py  # NetworkX graph wrapper
│   │   └── models.py        # ResourceNode dataclass
│   ├── scanners/
│   │   ├── base.py              # Scanner base class
│   │   ├── async_base.py        # Async scanner support
│   │   ├── vpc_scanner.py       # VPC/Subnet/SG scanner
│   │   ├── ec2_scanner.py       # EC2 scanner
│   │   ├── s3_scanner.py        # S3 scanner
│   │   ├── rds_scanner.py       # RDS scanner
│   │   ├── networking_scanner.py # IGW/NAT/Route Tables
│   │   ├── compute_scanner.py   # ALB/ASG/Launch Templates
│   │   ├── elasticache_scanner.py # ElastiCache clusters
│   │   ├── storage_scanner.py   # EBS/S3 policies
│   │   └── messaging_scanner.py # SQS/SNS
│   ├── transformers/
│   │   ├── base.py          # Transformer pipeline
│   │   ├── sanitizer.py     # Sensitive data removal
│   │   ├── downsizer.py     # Instance size reduction
│   │   ├── renamer.py       # Environment renaming
│   │   └── network_remapper.py  # Reference updates
│   ├── renderers/
│   │   ├── terraform.py     # Terraform HCL (Free+)
│   │   ├── cloudformation.py # CloudFormation (Solo+)
│   │   └── pulumi.py        # Pulumi Python (Pro+)
│   └── licensing/
│       ├── manager.py       # License management
│       ├── gates.py         # Feature gating
│       └── tracker.py       # Usage tracking
├── templates/               # Jinja2 templates
├── tests/                   # pytest test suite
├── .github/workflows/       # CI/CD
├── pyproject.toml
└── README.md
```

## Support

- **Documentation**: [https://docs.replimap.io](https://docs.replimap.io)
- **Issues**: [GitHub Issues](https://github.com/replimap/replimap/issues)
- **Email**: support@replimap.io

## License

Proprietary - See [LICENSE](./LICENSE) for details.

Copyright (c) 2025 RepliMap
