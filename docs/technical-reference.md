# RepliMap Technical Reference

> **Looking for a quick overview?** See the [main README](../README.md) for features, pricing, and quick start.
>
> This document contains detailed technical specifications, CLI reference, and architecture documentation.

---

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

# Activate a license key (format: RM-XXXX-XXXX-XXXX-XXXX)
replimap license activate RM-XXXX-XXXX-XXXX-XXXX
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

## Trust Center (Enterprise Audit)

The Trust Center provides enterprise-grade API call auditing for compliance and security reviews. It proves that RepliMap only performs READ-ONLY operations, which is critical for enterprise procurement, especially Australian Big 4 banks.

### Quick Start

```python
from replimap.audit import TrustCenter

# Get the singleton instance
tc = TrustCenter.get_instance()

# Enable auditing on your boto3 session
tc.enable(boto3_session)

# Create an audit session for related operations
with tc.session("production_scan") as session_id:
    # All AWS API calls are now captured
    scanner.scan_all()

# Generate a compliance report
report = tc.generate_report()
print(report.compliance_statement)
# Output: "COMPLIANT: This tool performed 100% READ-ONLY operations..."
```

### CLI Usage

```bash
# Enable Trust Center auditing during scan
replimap scan --profile prod --audit

# Generate audit report
replimap audit-report --format json --output audit.json
replimap audit-report --format csv --output audit.csv
replimap audit-report --format text --output compliance.txt
```

### Features

| Feature | Description |
|---------|-------------|
| **Automatic Capture** | boto3 event hooks capture all API calls transparently |
| **Operation Classification** | Categorizes as READ/WRITE/DELETE/ADMIN |
| **Session Grouping** | Groups related API calls together |
| **Compliance Reports** | Proves 100% Read-Only operation |
| **Multi-Format Export** | JSON, CSV, human-readable text |
| **Sensitive Data Redaction** | Passwords, tokens, secrets automatically redacted |

### Export Formats

```bash
# JSON - Full report with optional detailed records
tc.export_json(report, "audit.json", include_records=True)

# CSV - Tabular format for spreadsheet analysis
tc.export_csv(sessions, "records.csv")

# Text - Human-readable compliance statement
tc.save_compliance_text(report, "compliance.txt")
```

### Compliance Statement

The Trust Center generates compliance statements for enterprise security reviews:

```
========================================================================
TRUST CENTER COMPLIANCE REPORT
========================================================================

Tool: RepliMap v1.0.0
Report ID: rpt-12345
Generated: 2025-01-15T12:00:00

------------------------------------------------------------------------
EXECUTIVE SUMMARY
------------------------------------------------------------------------

  Total Audit Sessions:  5
  Total AWS API Calls:   1,247
  Total Duration:        45.3 seconds

  Read-Only Operations:  100.0%
  Fully Read-Only:       YES

COMPLIANCE STATEMENT:
  COMPLIANT: This tool performed 100% READ-ONLY operations during
  the audit period. No AWS resources were created, modified, or
  deleted. This confirms the tool's non-invasive, agentless
  architecture.
```

## Security Auditing

RepliMap includes security auditing powered by Checkov for scanning your AWS infrastructure.

```bash
# Run security audit on scanned infrastructure
replimap audit --profile prod --region us-east-1

# Output to HTML report
replimap audit --profile prod --format html --output audit-report.html

# Output to JSON for CI/CD integration
replimap audit --profile prod --format json --output audit.json

# Exit with non-zero code on failures (for CI/CD)
replimap audit --profile prod --ci

# Scan specific VPC
replimap audit --profile prod --scope vpc:vpc-12345678
```

## Infrastructure Visualization

Generate interactive visualizations of your AWS infrastructure dependencies.

```bash
# Generate Mermaid diagram
replimap graph --profile prod --format mermaid

# Generate interactive HTML (D3.js)
replimap graph --profile prod --format html --output infra-graph.html

# Export as JSON for custom tooling
replimap graph --profile prod --format json --output graph.json

# Scope to specific VPC
replimap graph --profile prod --vpc vpc-12345678
```

### Graph Simplification

By default, graphs are simplified for readability by hiding noisy resources (SG rules, routes) and collapsing large groups of similar resources.

```bash
# Show all resources (no filtering or grouping)
replimap graph -r us-east-1 --all

# Include security group rules
replimap graph -r us-east-1 --sg-rules

# Include routes and route tables
replimap graph -r us-east-1 --routes

# Disable resource grouping (show individual nodes)
replimap graph -r us-east-1 --no-collapse

# Security-focused view (show SGs, IAM, KMS)
replimap graph -r us-east-1 --security
```

| Option | Description |
|--------|-------------|
| `--all, -a` | Show all resources without filtering |
| `--sg-rules` | Include security group rules |
| `--routes` | Include routes and route tables |
| `--no-collapse` | Disable resource grouping |
| `--security` | Security-focused view |

### Advanced Graph Features

The interactive HTML graph includes several advanced visualization features:

| Feature | Description |
|---------|-------------|
| **Link Classification** | Toggle between traffic flow and infrastructure dependency views |
| **Cost Overlay** | Heat map showing estimated monthly cost per resource (low/medium/high/critical) |
| **Blast Radius** | Click a resource to visualize the impact of changes or failures |
| **Orphan Detection** | Highlight unused resources with estimated cost savings |
| **Drift Visualization** | Show resources that have drifted from Terraform state |
| **Tool Modes** | Select/Trace/Blast modes for different analysis types |
| **Breadcrumbs** | Navigation history with ESC key to go back |

## Infrastructure Drift Detection

Detect drift between your Terraform state and actual AWS resources.

```bash
# Detect drift using local state file
replimap drift --profile prod --state ./terraform.tfstate

# Detect drift using remote S3 backend
replimap drift --profile prod \
  --remote-bucket my-tf-state \
  --remote-key prod/terraform.tfstate \
  --remote-region us-east-1

# Output HTML report
replimap drift --profile prod --state ./terraform.tfstate \
  --format html --output drift-report.html

# CI/CD mode (exit code reflects drift status)
replimap drift --profile prod --state ./terraform.tfstate --ci

# Scope to specific VPC
replimap drift --profile prod --state ./terraform.tfstate \
  --scope vpc:vpc-12345678
```

### Exit Codes (CI Mode)

| Code | Meaning |
|------|---------|
| 0 | No drift detected |
| 1 | Drift detected (or critical/high severity drift) |
| 2 | Error during detection |

## Dependency Explorer

Explore what resources may be affected before modifying or deleting a resource.

> **Important**: This analysis is based on AWS API metadata only. Application-level
> dependencies (hardcoded IPs, DNS, config files) are NOT detected. Always validate
> all dependencies before making infrastructure changes.

```bash
# Explore dependencies for a security group
replimap deps sg-12345 -r us-east-1

# Show dependency tree view
replimap deps vpc-abc123 -r us-east-1 --format tree

# Generate interactive HTML visualization
replimap deps i-xyz789 -r us-east-1 -f html -o deps.html

# Limit analysis depth
replimap deps vpc-12345 -r us-east-1 --depth 3

# Scope to a specific VPC
replimap deps sg-12345 -r us-east-1 --vpc vpc-abc123
```

### Output Formats

| Format | Description |
|--------|-------------|
| `console` | Rich terminal output with summary (default) |
| `tree` | Tree view of dependencies |
| `table` | Table of affected resources |
| `html` | Interactive D3.js visualization |
| `json` | Machine-readable JSON |

### Estimated Impact Levels

> Note: These are estimates based on AWS API metadata only.

| Level | Score | Description |
|-------|-------|-------------|
| CRITICAL | 90-100 | Core infrastructure (VPC, main DB) |
| HIGH | 70-89 | Production services |
| MEDIUM | 40-69 | Supporting resources |
| LOW | 1-39 | Peripheral resources |
| NONE | 0 | No downstream impact detected |
| UNKNOWN | - | Impact cannot be determined |

## Cost Estimation

Estimate monthly AWS costs for your infrastructure with optimization recommendations.

**Important**: Cost estimates are for planning purposes only. Actual costs may differ due to data transfer, API calls, reserved instances, and other factors not included in estimates.

```bash
# Estimate costs for current region
replimap cost -r us-east-1

# Estimate costs for a specific VPC
replimap cost -r us-east-1 --vpc vpc-12345

# Export to HTML report with charts
replimap cost -r us-east-1 -f html -o cost-report.html

# Export to CSV for spreadsheet analysis
replimap cost -r us-east-1 -f csv -o costs.csv

# Export to JSON for automation
replimap cost -r us-east-1 -f json -o costs.json

# Export to Markdown report
replimap cost -r us-east-1 -f markdown -o costs.md

# Skip confirmation prompt for exports
replimap cost -r us-east-1 -f html -o report.html --acknowledge
```

### Output Formats

| Format | Description |
|--------|-------------|
| `console` | Rich terminal output with summary (default) |
| `table` | Full table of all resource costs |
| `html` | Interactive HTML report with Chart.js |
| `json` | Machine-readable JSON |
| `csv` | Spreadsheet-compatible CSV |
| `markdown` | Markdown report for documentation |

### Estimate Accuracy

| Confidence | Range | Description |
|------------|-------|-------------|
| HIGH | ±10% | Standard on-demand pricing |
| MEDIUM | ±20% | Some usage assumptions |
| LOW | ±40% | Many factors unknown |

### What's NOT Included

- Data transfer costs (can be 10-30% of bill)
- API request charges (S3, Lambda, API Gateway)
- Reserved Instance / Savings Plan discounts
- Spot Instance pricing
- Free tier benefits
- CloudWatch, CloudTrail fees
- Support plan costs

For accurate billing, use [AWS Cost Explorer](https://console.aws.amazon.com/cost-management/) or [AWS Pricing Calculator](https://calculator.aws/).

### Cost Categories

| Category | Resources |
|----------|-----------|
| COMPUTE | EC2, Lambda, ECS, EKS |
| DATABASE | RDS, DynamoDB, ElastiCache |
| STORAGE | S3, EBS, EFS |
| NETWORK | VPC, NAT Gateway, Load Balancer |
| SECURITY | IAM, KMS, WAF |
| MONITORING | CloudWatch, SNS, SQS |

### Optimization Recommendations

The cost estimator provides actionable recommendations:

- **Reserved Instances**: ~40% savings for steady-state workloads
- **Savings Plans**: ~35% savings with flexibility
- **gp2 to gp3 Migration**: ~20% savings with better performance
- **NAT Gateway Optimization**: Consolidation opportunities
- **Right-sizing**: Instance type recommendations

## Right-Sizer (Dev Mode)

Automatically optimize instance sizes for dev/staging environments using the Right-Sizer API.

```bash
# Generate Terraform with dev-optimized instance sizes
replimap clone --profile prod --output-dir ./staging-tf \
  --dev-mode --mode generate

# Use aggressive optimization (smaller instances, lower costs)
replimap clone --profile prod --output-dir ./staging-tf \
  --dev-mode --dev-strategy aggressive --mode generate

# Conservative (default) - balanced performance and cost
replimap clone --profile prod --output-dir ./staging-tf \
  --dev-mode --dev-strategy conservative --mode generate
```

### How It Works

1. RepliMap scans your production infrastructure
2. Generates Terraform with resource-specific variables (e.g., `aws_instance_web_instance_type`)
3. When `--dev-mode` is enabled, calls the Right-Sizer API with your resource inventory
4. Receives optimized instance size recommendations
5. Generates `right-sizer.auto.tfvars` with the recommendations

### Generated Files

| File | Description |
|------|-------------|
| `variables.tf` | Resource-specific variables with production defaults |
| `right-sizer.auto.tfvars` | Optimized values for dev/staging (auto-loaded by Terraform) |

### Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `conservative` | Moderate downsizing, maintains headroom | Staging, QA |
| `aggressive` | Maximum downsizing, lowest cost | Dev, CI/CD |

### Supported Resources

- EC2 Instances (`instance_type`)
- RDS Instances (`instance_class`)
- ElastiCache Clusters (`node_type`)
- ElastiCache Replication Groups (`node_type`)

### Requirements

- Solo plan or higher (Free tier does not include Right-Sizer)
- Network access to RepliMap API for recommendations

## Incremental Scanning

Incremental scanning uses the AWS ResourceGroupsTaggingAPI for efficient change detection, reducing scan times from minutes to sub-seconds after the initial full scan.

### How It Works

```bash
# First scan - full scan, builds baseline
replimap scan --profile prod --incremental

# Subsequent scans - only detect changes
replimap scan --profile prod --incremental
# Output: "Incremental scan: 3 created, 1 modified, 0 deleted, 247 unchanged"
```

### API Usage

```python
from replimap.scan.incremental import IncrementalScanner, ScanStateStore

# Initialize with state store
state_store = ScanStateStore(storage_dir=".replimap/state")
scanner = IncrementalScanner(boto3_session, state_store)

# Perform incremental scan
change_set = scanner.scan_incremental(region="us-east-1")

print(f"Created: {len(change_set.created)}")
print(f"Modified: {len(change_set.modified)}")
print(f"Deleted: {len(change_set.deleted)}")
print(f"Unchanged: {len(change_set.unchanged)}")
```

### Features

| Feature | Description |
|---------|-------------|
| **ResourceGroupsTaggingAPI** | Uses AWS tagging API for fast resource enumeration |
| **Content Hashing** | Fingerprints resources to detect modifications |
| **SQLite State Store** | Persistent state storage between scans |
| **Sub-Second Scans** | Incremental scans complete in milliseconds |

## Historical Snapshots

Historical snapshots provide point-in-time captures of your infrastructure with 30-day retention, enabling infrastructure change tracking and audit trails.

### Usage

```bash
# Create a snapshot
replimap snapshot create --profile prod --name "pre-deployment"

# List snapshots
replimap snapshot list --profile prod

# Compare two snapshots
replimap snapshot compare --from "2025-01-01" --to "2025-01-15"

# Export snapshot diff
replimap snapshot compare --from snapshot-abc --to snapshot-xyz --format json
```

### API Usage

```python
from replimap.scan.snapshots import SnapshotManager

manager = SnapshotManager(storage_dir=".replimap/snapshots")

# Create a snapshot
snapshot = manager.create_snapshot(
    graph=infrastructure_graph,
    name="pre-deployment",
    metadata={"environment": "production"}
)

# Compare snapshots
comparison = manager.compare(snapshot_id_1, snapshot_id_2)
print(f"Added: {len(comparison.added)}")
print(f"Removed: {len(comparison.removed)}")
print(f"Modified: {len(comparison.modified)}")
```

### Features

| Feature | Description |
|---------|-------------|
| **30-Day Retention** | Configurable retention policy with automatic cleanup |
| **Point-in-Time Capture** | Immutable snapshots for compliance |
| **Diff Comparison** | Compare any two snapshots |
| **Audit Trail** | Full history of infrastructure changes |
| **Compression** | Optional compression for storage efficiency |

## Topology Constraints

Topology constraints enable policy-based infrastructure validation, ensuring your infrastructure meets organizational security and compliance requirements.

### Configuration

Create a `constraints.yaml` file:

```yaml
topology_constraints:
  version: "1.0"
  constraints:
    # Require Environment tag on all resources
    - name: require-environment-tag
      constraint_type: require_tag
      severity: high
      required_tags:
        Environment: null  # Any value
        Owner: null

    # Require encryption on all databases
    - name: require-rds-encryption
      constraint_type: require_encryption
      severity: critical
      source_type: aws_db_instance

    # Prohibit public S3 buckets
    - name: prohibit-public-s3
      constraint_type: prohibit_public_access
      severity: critical
      source_type: aws_s3_bucket

    # Prohibit direct database access from internet
    - name: prohibit-public-rds
      constraint_type: prohibit_relationship
      severity: critical
      source_type: aws_internet_gateway
      target_type: aws_db_instance
```

### CLI Usage

```bash
# Validate infrastructure against constraints
replimap validate --config constraints.yaml --profile prod

# Generate default constraints
replimap constraints generate --output constraints.yaml

# Validate with specific severity threshold
replimap validate --config constraints.yaml --fail-on high
```

### Constraint Types

| Type | Description |
|------|-------------|
| `require_tag` | Resources must have specified tags |
| `require_encryption` | Resources must be encrypted |
| `prohibit_relationship` | Certain resource connections are forbidden |
| `prohibit_public_access` | Resources must not be publicly accessible |

### Severity Levels

| Severity | Exit Code | Description |
|----------|-----------|-------------|
| CRITICAL | 2 | Security vulnerabilities requiring immediate action |
| HIGH | 1 | Important policy violations |
| MEDIUM | 0 | Recommendations for improvement |
| LOW | 0 | Informational findings |
| INFO | 0 | Best practice suggestions |

## RI/Savings Plan Aware Pricing

The RI-aware pricing engine considers your Reserved Instances and Savings Plans when calculating costs and generating right-sizing recommendations.

### Features

- **Reservation Coverage** - Shows how much of your spend is covered by reservations
- **Waste Detection** - Identifies underutilized reservations
- **Constrained Right-Sizing** - Recommendations respect reservation commitments
- **Expiration Alerts** - Warns about reservations expiring soon

### CLI Usage

```bash
# Cost estimate with reservation awareness
replimap cost --profile prod --ri-aware

# Show reservation utilization
replimap reservations --profile prod

# Right-sizing with reservation constraints
replimap clone --profile prod --dev-mode --ri-aware
```

### API Usage

```python
from replimap.cost.ri_aware import (
    RIAwarePricingEngine,
    ReservedInstance,
    SavingsPlanCommitment,
)

# Create RI-aware pricing engine
engine = RIAwarePricingEngine(
    region="us-east-1",
    reserved_instances=[...],  # Your RIs
    savings_plans=[...],        # Your Savings Plans
)

# Check if resource has a reservation
has_ri, ri_type, ri_id = engine.has_reservation_for("m5.large")

# Get right-sizing impact (respects reservations)
impact = engine.get_right_sizing_impact(
    current_type="m5.xlarge",
    recommended_type="m5.large"
)
if not impact.get("can_proceed"):
    print("Cannot downsize: would waste reservation")
```

### Utilization Levels

| Level | Percentage | Description |
|-------|------------|-------------|
| HIGH | 80-100% | Healthy utilization |
| MEDIUM | 60-79% | Acceptable but room for improvement |
| LOW | 40-59% | Significant waste, review needed |
| CRITICAL | 0-39% | Major waste, immediate action required |

### Waste Detection

The engine identifies wasted reservations:

```python
# Analyze reservation waste
analysis = engine.analyze()

for waste in analysis.waste_items:
    print(f"{waste.reservation_id}: {waste.utilization_percentage}% utilized")
    print(f"  Monthly waste: ${waste.monthly_waste}")
    print(f"  Recommendation: {waste.recommendation}")
```

## Output Formats

| Format | Plan Required | Status |
|--------|---------------|--------|
| Terraform HCL | Free+ | ✅ Available |
| CloudFormation YAML | Pro+ | ✅ Available |
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

| Plan | Monthly | Scans/Month | AWS Accounts |
|------|---------|-------------|--------------|
| **Free** | $0 | 3 | 1 |
| **Solo** | $29 | Unlimited | 1 |
| **Pro** | $79 | Unlimited | 3 |
| **Team** | $149 | Unlimited | 10 |
| **Enterprise** | $399+ | Unlimited | Unlimited |

> **Note**: All plans have unlimited resource scanning. Gating happens at output/export time, not during scanning.

### Feature Matrix

| Feature | Free | Solo | Pro | Team | Enterprise |
|---------|------|------|-----|------|------------|
| Terraform Output | ✅ | ✅ | ✅ | ✅ | ✅ |
| CloudFormation Output | ❌ | ❌ | ✅ | ✅ | ✅ |
| Pulumi Output | ❌ | ❌ | ✅ | ✅ | ✅ |
| Async Scanning | ❌ | ✅ | ✅ | ✅ | ✅ |
| Right-Sizer (Dev Mode) | ❌ | ✅ | ✅ | ✅ | ✅ |
| Custom Templates | ❌ | ❌ | ✅ | ✅ | ✅ |
| Cost Estimation | ❌ | ❌ | ✅ | ✅ | ✅ |
| Drift Detection | ❌ | ❌ | ✅ | ✅ | ✅ |
| Dependency Explorer | ❌ | ❌ | ❌ | ✅ | ✅ |
| Web Dashboard | ❌ | ❌ | ✅ | ✅ | ✅ |
| Team Collaboration | ❌ | ❌ | ❌ | ✅ | ✅ |
| SSO Integration | ❌ | ❌ | ❌ | ❌ | ✅ |
| Audit Logs | ❌ | ❌ | ❌ | ❌ | ✅ |

## License Management

License keys use the format `RM-XXXX-XXXX-XXXX-XXXX` (RM prefix for RepliMap brand).

```bash
# Activate a license key
replimap license activate RM-XXXX-XXXX-XXXX-XXXX

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
  --dev-mode, --dev        [SOLO+] Optimize resources for dev/staging via Right-Sizer
  --dev-strategy TEXT      Right-Sizer strategy: 'conservative' or 'aggressive' [default: conservative]

# Load command
replimap load GRAPH_FILE

# Audit command (security scanning)
replimap audit [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --region, -r TEXT        AWS region [default: us-east-1]
  --scope, -s TEXT         Scope to VPC (e.g., vpc:vpc-xxx or vpc-name:Production)
  --format, -f TEXT        Output format: console, html, json [default: console]
  --output, -o PATH        Output file path
  --ci                     CI mode (exit code reflects findings)

# Graph command (visualization)
replimap graph [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --region, -r TEXT        AWS region [default: us-east-1]
  --scope, -s TEXT         Scope to VPC
  --format, -f TEXT        Output format: mermaid, html, json [default: mermaid]
  --output, -o PATH        Output file path

# Drift command (state comparison)
replimap drift [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --region, -r TEXT        AWS region [default: us-east-1]
  --state PATH             Local terraform.tfstate file path
  --remote-bucket TEXT     S3 bucket for remote state
  --remote-key TEXT        S3 key for remote state
  --remote-region TEXT     S3 bucket region
  --scope, -s TEXT         Scope to VPC
  --format, -f TEXT        Output format: console, html, json [default: console]
  --output, -o PATH        Output file path
  --ci                     CI mode (exit code reflects drift status)

# Dependency explorer command (impact analysis, Pro+)
# Note: Based on AWS API metadata only. Application-level deps not detected.
replimap deps RESOURCE_ID [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --region, -r TEXT        AWS region [default: us-east-1]
  --vpc, -v TEXT           VPC ID to scope the scan
  --depth, -d INT          Maximum depth to traverse [default: 10]
  --format, -f TEXT        Output format: console, tree, table, html, json [default: console]
  --output, -o PATH        Output file path
  --open/--no-open         Open HTML report in browser [default: open]

# Cost estimation command (Pro+)
replimap cost [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --region, -r TEXT        AWS region [default: us-east-1]
  --vpc, -v TEXT           VPC ID to scope the scan
  --format, -f TEXT        Output format: console, table, html, json, csv [default: console]
  --output, -o PATH        Output file path
  --open/--no-open         Open HTML report in browser [default: open]

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

### Project Configuration (.replimap.yaml)

RepliMap supports a YAML configuration file for advanced customization. Create `.replimap.yaml` in your project root:

```yaml
# .replimap.yaml - RepliMap Configuration
version: "1.0"

# Naming conventions for generated resources
naming:
  style: snake_case  # snake_case, kebab-case, camelCase
  prefix: ""
  suffix: ""
  max_length: 64

# Scope and boundary rules
scope:
  # Default scope for resources
  default: managed

  # Rules for determining resource scope
  rules:
    # Ignore resources matching these patterns
    - pattern: ".*-backup-.*"
      scope: ignored
      reason: "Backup resources excluded"

    # Treat shared resources as data sources
    - pattern: "shared-.*"
      scope: data_source
      reason: "Shared infrastructure"

    # Resources tagged with Environment=Production are managed
    - tag: "Environment=Production"
      scope: managed

# File organization for generated Terraform
file_routing:
  strategy: semantic  # semantic, single, by_type
  # Semantic routing places resources in logical files:
  # - network.tf: VPC, subnets, route tables, gateways
  # - compute.tf: EC2, ASG, launch templates
  # - database.tf: RDS, ElastiCache
  # - storage.tf: S3, EBS
  # - security.tf: Security groups, IAM
  # - loadbalancing.tf: ALB, NLB, target groups

# Variable extraction settings
variables:
  # Extract these as variables automatically
  extract:
    - ami_ids
    - instance_types
    - key_names
    - certificate_arns

  # Environment-specific variable files
  environments:
    - dev
    - staging
    - prod

# Import block generation (Terraform 1.5+)
imports:
  enabled: true
  generate_import_blocks: true

# Audit annotations in generated code
audit:
  enabled: true
  include_source_metadata: true
  include_scan_timestamp: true

# Module extraction for repeated patterns
modules:
  enabled: true
  min_occurrences: 2  # Extract pattern if it appears 2+ times
  output_dir: modules/
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REPLIMAP_DEV_MODE` | `false` | Enable dev mode (bypasses license limits) |
| `REPLIMAP_LICENSE_API` | `https://replimap-api...` | License validation API URL |
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

RepliMap uses a **graph-based engine** with an enhanced rendering pipeline:

```
┌─────────────┐    ┌─────────────┐    ┌───────────────┐    ┌────────────────────┐
│   Scanners  │───▶│ Graph Engine│───▶│ Transformers  │───▶│ Enhanced Renderer  │
│  (AWS API)  │    │ (NetworkX)  │    │  (Pipeline)   │    │   (Terraform v2)   │
└─────────────┘    └─────────────┘    └───────────────┘    └────────────────────┘
                                                                     │
                   ┌─────────────────────────────────────────────────┼─────────────────────────────────────────────────┐
                   │                                                 │                                                 │
                   ▼                                                 ▼                                                 ▼
          ┌───────────────┐                                 ┌───────────────┐                                 ┌───────────────┐
          │ SmartNaming   │                                 │ ScopeEngine   │                                 │ FileRouter    │
          │ Generator     │                                 │ (Boundaries)  │                                 │ (Semantic)    │
          └───────────────┘                                 └───────────────┘                                 └───────────────┘
                   │                                                 │                                                 │
                   ▼                                                 ▼                                                 ▼
          ┌───────────────┐                                 ┌───────────────┐                                 ┌───────────────┐
          │ ImportBlock   │                                 │ Variable      │                                 │ Audit         │
          │ Generator     │                                 │ Extractor     │                                 │ Annotator     │
          └───────────────┘                                 └───────────────┘                                 └───────────────┘
```

### Core Pipeline

1. **Scanners**: Query AWS APIs for VPC, EC2, RDS, S3 resources
2. **Graph Engine**: Build dependency graph with NetworkX
3. **Transformers**: Apply sanitization, downsizing, renaming
4. **Enhanced Renderer**: Generate production-ready Terraform with intelligent features

### Enhanced Renderer Components (Level 2-5)

| Component | Description |
|-----------|-------------|
| **SmartNameGenerator** | Context-aware naming with collision detection and configurable styles |
| **ScopeEngine** | Boundary recognition (managed/data_source/ignored) with rule-based classification |
| **ImportBlockGenerator** | Terraform 1.5+ import blocks for seamless state adoption |
| **RefactoringEngine** | Safe refactoring with `moved` blocks for resource renames |
| **SemanticFileRouter** | Organize resources into logical files (network.tf, compute.tf, etc.) |
| **VariableExtractor** | Auto-extract AMIs, instance types, certificates as variables |
| **AuditAnnotator** | Add source metadata and compliance annotations to generated code |
| **LocalModuleExtractor** | Detect repeated patterns and extract reusable modules |
| **PlanBasedDriftEngine** | Detect drift using `terraform plan` output parsing |
| **SchemaBootstrapper** | Auto-discover provider schemas for validation |
| **ConfigLoader** | Load and validate `.replimap.yaml` configuration |

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
│   │   ├── models.py        # ResourceNode dataclass
│   │   ├── config.py        # ConfigLoader - .replimap.yaml support
│   │   ├── scope.py         # ScopeEngine - boundary recognition
│   │   ├── bootstrap.py     # SchemaBootstrapper - provider schema discovery
│   │   ├── sanitizer.py     # Security-critical sanitization middleware
│   │   ├── retry.py         # Coordinated retry logic with backoff
│   │   ├── circuit_breaker.py # Circuit breaker for API resilience
│   │   ├── cache.py         # Credential and result caching
│   │   ├── filters.py       # Resource filtering utilities
│   │   ├── selection.py     # Graph-based selection engine
│   │   └── topology_constraints.py # Topology constraints validation (P3-3)
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
│   │   ├── terraform.py         # Terraform HCL renderer (base)
│   │   ├── terraform_v2.py      # EnhancedTerraformRenderer (recommended)
│   │   ├── name_generator.py    # SmartNameGenerator - context-aware naming
│   │   ├── import_generator.py  # ImportBlockGenerator - TF 1.5+ imports
│   │   ├── refactoring.py       # RefactoringEngine - moved blocks
│   │   ├── file_router.py       # SemanticFileRouter - logical file organization
│   │   ├── variable_extractor.py # VariableExtractor - auto-extract variables
│   │   ├── audit_annotator.py   # AuditAnnotator - source metadata
│   │   ├── cloudformation.py    # CloudFormation YAML (Solo+)
│   │   └── pulumi.py            # Pulumi Python (Pro+)
│   ├── patterns/
│   │   └── local_module.py  # LocalModuleExtractor - pattern detection
│   ├── audit/               # Security auditing & Trust Center
│   │   ├── engine.py        # Audit orchestration
│   │   ├── checkov_runner.py # Checkov integration
│   │   ├── renderer.py      # Console/HTML/JSON output
│   │   ├── soc2_mapping.py  # SOC2 compliance mapping
│   │   ├── fix_suggestions.py # Remediation suggestions
│   │   ├── remediation/     # Auto-remediation templates
│   │   ├── templates/       # Jinja2 HTML templates
│   │   ├── trust_center.py  # Trust Center singleton (P1-9)
│   │   ├── models.py        # APICallRecord, AuditSession, TrustCenterReport
│   │   ├── classifier.py    # OperationClassifier (READ/WRITE/DELETE/ADMIN)
│   │   ├── hooks.py         # boto3 event hooks for API capture
│   │   └── exporters.py     # JSON, CSV, text export utilities
│   ├── graph/               # Infrastructure visualization
│   │   ├── visualizer.py    # Graph building
│   │   ├── builder.py       # Graph construction
│   │   ├── layout.py        # Hierarchical container layout
│   │   ├── aggregation.py   # Smart VPC-based aggregation
│   │   ├── grouper.py       # Resource grouping
│   │   ├── naming.py        # Graph node naming
│   │   ├── environment.py   # Environment detection (prod/staging/dev)
│   │   ├── views.py         # View management (overview/detail)
│   │   ├── filters.py       # Graph filtering
│   │   ├── link_classification.py  # Traffic vs dependency links
│   │   ├── summary_links.py # Cross-VPC connection summaries
│   │   ├── tool_modes.py    # Select/Trace/Blast tool palette
│   │   ├── cost_overlay.py  # Cost heat map visualization
│   │   ├── blast_radius.py  # Impact analysis calculation
│   │   ├── drift.py         # Drift detection for graphs
│   │   ├── orphan_detection.py # Unused resource detection
│   │   ├── formatters/      # Mermaid, JSON, D3.js formatters
│   │   └── templates/       # D3.js HTML template
│   ├── drift/               # Drift detection
│   │   ├── engine.py        # Legacy detection engine
│   │   ├── plan_engine.py   # PlanBasedDriftEngine (recommended)
│   │   ├── state_parser.py  # Terraform state parsing
│   │   ├── comparator.py    # Resource comparison
│   │   ├── models.py        # DriftReport, ResourceDrift models
│   │   ├── reporter.py      # Report generation (console/HTML/JSON)
│   │   └── templates/       # HTML report template
│   ├── dependencies/        # Dependency exploration
│   │   ├── models.py        # ResourceNode, DependencyZone, etc.
│   │   ├── graph_builder.py # Dependency graph building
│   │   ├── impact_calculator.py # Impact score estimation
│   │   └── reporter.py      # Console/HTML/JSON output
│   ├── blast/               # Blast radius analysis
│   │   ├── models.py        # Impact models
│   │   ├── graph_builder.py # Blast graph construction
│   │   ├── impact_calculator.py # Impact scoring
│   │   └── reporter.py      # Blast radius reporting
│   ├── snapshot/            # Infrastructure snapshots
│   │   ├── models.py        # Snapshot models
│   │   ├── store.py         # Snapshot storage
│   │   ├── differ.py        # Snapshot comparison
│   │   └── reporter.py      # Snapshot reporting
│   ├── cost/                # Cost estimation
│   │   ├── models.py        # ResourceCost, CostEstimate
│   │   ├── pricing.py       # AWS pricing data
│   │   ├── pricing_engine.py # Core pricing engine with AU support
│   │   ├── estimator.py     # Cost calculation engine
│   │   ├── reporter.py      # Console/HTML/CSV output
│   │   ├── ri_aware.py      # RI/Savings Plan aware pricing (P3-4)
│   │   ├── data_transfer.py # Data transfer cost analysis
│   │   └── enterprise_pricing.py # Enterprise pricing tiers
│   ├── scan/                # Scanning utilities
│   │   ├── incremental.py   # Incremental scanner (P3-1)
│   │   └── snapshots.py     # Historical snapshots (P3-2)
│   └── licensing/
│       ├── manager.py       # License management
│       ├── models.py        # License models
│       ├── gates.py         # Feature gating
│       ├── prompts.py       # License prompts
│       └── tracker.py       # Usage tracking
├── templates/               # Jinja2 templates
├── tests/                   # pytest test suite (900+ tests)
├── .github/workflows/       # CI/CD
├── .replimap.yaml           # Project configuration (optional)
├── pyproject.toml
├── CHANGELOG.md             # Version history
└── README.md
```

## Support

- **Documentation**: [https://docs.replimap.io](https://docs.replimap.io)
- **Issues**: [GitHub Issues](https://github.com/replimap/replimap/issues)
- **Email**: support@replimap.io

## License

Proprietary - See [LICENSE](./LICENSE) for details.

Copyright (c) 2025 RepliMap
