# RepliMap

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

```bash
# Install from PyPI
pip install replimap

# Or with uv
uv pip install replimap
```

## Quick Start

```bash
# Scan your production environment (Free tier: 5 resources, 3 scans/month)
replimap scan --profile prod --region us-east-1

# Preview what will be generated
replimap clone --profile prod --region us-west-2 --mode dry-run

# Generate Terraform files
replimap clone --profile prod --region us-west-2 --output-dir ./staging-tf --mode generate

# Check your license status
replimap license status
```

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
```

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
