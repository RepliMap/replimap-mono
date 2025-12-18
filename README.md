# RepliMap

**AWS Environment Replication Tool**

Point at your Production AWS environment and generate a cost-optimized, safe Staging environment in minutes.

## Overview

RepliMap scans your AWS resources, builds a dependency graph, and generates Terraform code to replicate your environment with intelligent transformations:

- **Instance Downsizing**: Automatically reduces EC2/RDS instance sizes for cost savings
- **Environment Renaming**: Transforms names from `prod` to `staging`
- **Sensitive Data Sanitization**: Removes secrets, passwords, and hardcoded credentials
- **Dependency Awareness**: Understands VPC → Subnet → EC2 relationships

## Architecture

RepliMap uses a **graph-based engine**:

1. **Ingestion**: AWS resources become nodes in a NetworkX directed graph
2. **Edges**: Dependencies (EC2 → Security Group → VPC) are tracked
3. **Transformation**: Graph traversal modifies properties
4. **Generation**: Jinja2 templates render Terraform HCL

## Installation

```bash
# Clone the repository
git clone https://github.com/replimap/replimap.git
cd replimap

# Install with pip
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Scan Your Environment

```bash
# Scan with default profile
replimap scan --region us-east-1

# Scan with specific profile and save graph
replimap scan --profile prod --region us-west-2 --output graph.json
```

### Generate Terraform Code

```bash
# Preview what will be generated (dry-run)
replimap clone --profile prod --region us-west-2 --mode dry-run

# Generate Terraform files
replimap clone --profile prod --region us-west-2 --output-dir ./staging-terraform --mode generate
```

### Load a Saved Graph

```bash
replimap load graph.json
```

## Supported Resources

| Resource Type | Scan | Transform | Generate |
|--------------|------|-----------|----------|
| VPC | ✅ | ✅ | ✅ |
| Subnets | ✅ | ✅ | ✅ |
| Security Groups | ✅ | ✅ | ✅ |
| EC2 Instances | ✅ | ✅ | ✅ |
| S3 Buckets | ✅ | ✅ | ✅ |
| RDS Instances | ✅ | ✅ | ✅ |
| DB Subnet Groups | ✅ | ✅ | ✅ |

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
  --output-dir, -o PATH    Output directory for Terraform files [default: ./terraform]
  --mode, -m TEXT          Mode: 'dry-run' or 'generate' [default: dry-run]
  --downsize/--no-downsize Enable instance downsizing [default: downsize]
  --rename-pattern TEXT    Renaming pattern, e.g., 'prod:stage'

# Load command
replimap load GRAPH_FILE
```

## Project Structure

```
replimap/
├── replimap/
│   ├── __init__.py
│   ├── main.py              # Typer CLI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── graph_engine.py  # NetworkX graph wrapper
│   │   └── models.py        # ResourceNode dataclass
│   ├── scanners/
│   │   ├── __init__.py
│   │   ├── base.py          # Scanner base class
│   │   ├── vpc_scanner.py   # VPC/Subnet/SG scanner
│   │   ├── ec2_scanner.py   # EC2 scanner
│   │   ├── s3_scanner.py    # S3 scanner
│   │   └── rds_scanner.py   # RDS scanner
│   ├── transformers/
│   │   ├── __init__.py
│   │   └── base.py          # Transformer pipeline
│   └── renderers/
│       ├── __init__.py
│       └── terraform.py     # Terraform HCL renderer
├── templates/               # Jinja2 templates for TF generation
├── tests/                   # pytest test suite
├── pyproject.toml
└── README.md
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy replimap

# Linting
ruff check replimap
```

## How It Works

### The Dependency Graph

RepliMap builds a directed graph where:
- **Nodes** are AWS resources (VPCs, Subnets, EC2 instances, etc.)
- **Edges** represent dependencies (EC2 *depends on* Subnet, Subnet *belongs to* VPC)

This enables:
- **Topological sorting** for correct Terraform ordering
- **Impact analysis** (what depends on this VPC?)
- **Transformation isolation** (modify only network resources)

### Transformations

Before generating Terraform, RepliMap applies transformations:

1. **Sanitization**: Remove passwords, secrets, ARNs with account IDs
2. **Downsizing**: Map `m5.xlarge` → `t3.medium` for cost savings
3. **Renaming**: Replace `prod` → `staging` in names and tags
4. **Network Remapping**: Update subnet/SG references for new VPC

### Generated Output

RepliMap produces organized Terraform files:
- `vpc.tf` - VPCs and Subnets
- `security_groups.tf` - Security Groups with rules
- `ec2.tf` - EC2 Instances
- `rds.tf` - RDS Instances and DB Subnet Groups
- `s3.tf` - S3 Buckets
- `variables.tf` - Configurable variables
- `outputs.tf` - Useful outputs

## License

MIT License
