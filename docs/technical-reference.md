# RepliMap Technical Reference

> **Looking for a quick overview?** See the [main README](../README.md) for features, pricing, and quick start.
>
> This document contains detailed technical specifications, CLI reference, and architecture documentation.

---

[![Python versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://github.com/RepliMap/replimap)
[![Tests](https://github.com/RepliMap/replimap/actions/workflows/test.yml/badge.svg)](https://github.com/RepliMap/replimap/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)

**AWS Infrastructure Intelligence Engine**

> Reverse-engineer AWS infrastructure into Terraform. Visualize dependencies, audit security, estimate costs.

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
replimap scan --profile prod --trust-center

# Check Trust Center status
replimap trust-center status

# Generate compliance report
replimap trust-center report
replimap trust-center report -f json -o audit.json
replimap trust-center report -f csv -o api-calls.csv
replimap trust-center report -f text -o compliance.txt

# Include detailed API call records in JSON
replimap trust-center report -f json -o audit.json --include-records

# Clear all audit sessions
replimap trust-center clear
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

### HTML Report Features

The HTML drift report includes an interactive workbench with:

- **Accordion Layout** - Resources grouped by type with expandable sections
- **Multi-dimensional Filtering** - Search by ID, name, TF address; filter by status and classification
- **Drift Classification** - "Action Required" (semantic) vs "Cosmetic" (tag-only) changes
- **Remediation Commands** - Copy-to-clipboard terraform commands for each drift

### Remediation Commands

The report generates appropriate terraform commands for each drift type:

| Drift Type | Command | Description |
|------------|---------|-------------|
| **MODIFIED** | `terraform apply -target=<resource>` | Revert AWS to match Terraform |
| **ADDED** | `terraform import <resource> <id>` | Import unmanaged resource to state |
| **REMOVED** | `terraform apply -target=<resource>` | Recreate deleted resource |

Resource IDs are automatically sanitized for valid Terraform names:
- Special characters (`/`, `-`, `.`, `:`, etc.) → underscores
- Leading digits → prefixed with `r_` (e.g., `123-bucket` → `r_123_bucket`)
- Shell special characters in IDs are properly quoted

### Offline Drift Detection (Advanced)

Detect drift using cached RepliMap scans without requiring AWS connection. This is the "offline terraform plan" - faster and works in air-gapped environments.

```bash
# Offline drift detection using cached scan
replimap drift-offline offline -p prod -s ./terraform.tfstate

# Output SARIF for GitHub Security integration
replimap drift-offline offline -p prod -s ./terraform.tfstate --sarif

# CI/CD mode with severity filtering
replimap drift-offline offline -p prod -s ./terraform.tfstate \
  --fail-on-drift --severity high

# Use custom ignore rules
replimap drift-offline offline -p prod -s ./terraform.tfstate \
  --ignore .replimapignore

# Compare two scans over time
replimap drift-offline compare-scans -p prod \
  --current ./scan-today.json --previous ./scan-yesterday.json
```

#### Drift Types

| Type | Description | Remediation |
|------|-------------|-------------|
| **UNMANAGED** | Resource exists in AWS but not in Terraform | `terraform import` or delete |
| **MISSING** | Resource in Terraform state was deleted from AWS | `terraform apply` or `terraform state rm` |
| **DRIFTED** | Configuration differs between AWS and Terraform | `terraform apply` or update .tf files |

#### Severity Classification

| Severity | Fields | Example |
|----------|--------|---------|
| **CRITICAL** | Security fields (ingress/egress, IAM policies, encryption) | Security group rules, KMS keys |
| **HIGH** | Infrastructure fields (instance_type, AMI, networking) | EC2 instance type, subnet IDs |
| **MEDIUM** | Configuration settings | Most resource attributes |
| **LOW** | Metadata (tags, descriptions) | Resource tags |

#### .replimapignore File

Create a `.replimapignore` file to suppress benign drifts:

```bash
# Ignore specific resource types
aws_cloudwatch_log_group

# Ignore specific fields (resource_type:field)
aws_autoscaling_group:desired_capacity
aws_ecs_service:desired_count

# Ignore specific resource IDs
i-1234567890abcdef0

# Wildcard field ignore
*:last_modified
```

Default ignore rules (always applied):
- Kubernetes-managed resources (`kubernetes.io/*`, `k8s.io/*` tags)
- AWS-managed tags (`aws:*` tags)
- Auto-scaling fields (`desired_capacity`, `desired_count`)

### SARIF Output for GitHub Security

RepliMap generates SARIF 2.1.0 output compatible with GitHub Advanced Security. Upload to GitHub's Code Scanning for drift alerts in your Security tab.

```bash
# Generate SARIF output
replimap drift-offline offline -p prod -s ./terraform.tfstate --sarif > drift.sarif

# Upload to GitHub (in GitHub Actions)
- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: drift.sarif
```

#### SARIF Features

- **Stable Fingerprinting**: SHA-256 fingerprints prevent duplicate alerts across scans
- **Rich Markdown**: Severity badges, change tables, remediation hints
- **Hybrid Locations**: Both file (terraform.tfstate) and cloud resource (ARN) locations
- **Predefined Rules**: 16 rules covering audit, drift, and analysis findings
- **CWE Mappings**: Security rules include Common Weakness Enumeration references

#### Predefined Rules

| Rule ID | Category | Description |
|---------|----------|-------------|
| DRIFT001 | Drift | Unmanaged resource detected |
| DRIFT002 | Drift | Terraform resource missing from AWS |
| DRIFT003 | Drift | Resource configuration has drifted |
| DRIFT004 | Drift | Security-critical configuration has drifted |
| AUDIT001 | Security | Resource is publicly accessible |
| AUDIT002 | Security | Resource lacks encryption |
| AUDIT003 | Security | IAM permissions are overly permissive |
| AUDIT004 | Security | Security group allows unrestricted access |
| ANALYSIS001 | Graph | Potential attack path identified |
| ANALYSIS002 | Graph | Resource has high blast radius |

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

### Resource Analyzer Mode

The `--analyze` flag provides deep dependency analysis for individual resources using specialized analyzers. This mode provides:

- **Relationship Classification**: Dependencies organized by relationship type (MANAGER, CONSUMER, DEPENDENCY, NETWORK, IDENTITY)
- **Blast Radius Scoring**: Weighted impact calculation based on resource criticality
- **IaC Detection**: Detects CloudFormation, Terraform, and other IaC management
- **Contextual Warnings**: Actionable warnings about resource dependencies

```bash
# Analyze EC2 instance dependencies
replimap deps i-abc123 -r us-east-1 --analyze

# Analyze Security Group dependencies
replimap deps sg-12345 -r us-east-1 --analyze

# Analyze IAM Role trust relationships
replimap deps my-role-name -r us-east-1 --analyze

# Analyze RDS instance dependencies
replimap deps my-db-instance -r us-east-1 --analyze

# Analyze S3 bucket dependencies (replication, notifications)
replimap deps my-bucket-name -r us-east-1 --analyze

# Analyze Lambda function dependencies
replimap deps my-function-name -r us-east-1 --analyze

# Analyze Load Balancer dependencies
replimap deps arn:aws:elasticloadbalancing:... -r us-east-1 --analyze
```

### Supported Analyzers

| Resource Type | Analyzer | Relationships Detected |
|---------------|----------|------------------------|
| EC2 Instance | `EC2Analyzer` | ASG manager, Target Groups, EBS, AMI, VPC/Subnet, Security Groups, IAM Profile, KMS keys |
| Security Group | `SecurityGroupAnalyzer` | EC2/RDS/Lambda consumers, VPC, rule references, cross-account access |
| IAM Role | `IAMRoleAnalyzer` | Trusted entities, attached policies, consumers (Lambda/EC2), KMS grants |
| RDS Instance | `RDSInstanceAnalyzer` | Read replicas, subnet groups, parameter groups, KMS encryption, monitoring role |
| Auto Scaling Group | `ASGAnalyzer` | Managed instances, launch templates, target groups, VPC/Subnets |
| S3 Bucket | `S3BucketAnalyzer` | Replication targets, Lambda/SQS/SNS notifications, KMS encryption |
| Lambda Function | `LambdaFunctionAnalyzer` | Layers, event sources (SQS/Kinesis/DynamoDB), VPC config, execution role |
| Load Balancer (ALB/NLB) | `ELBAnalyzer` | Target groups, VPC/Subnets, Security Groups (ALB), SSL certificates |
| ElastiCache Cluster | `ElastiCacheAnalyzer` | Replication groups, parameter groups, Security Groups |

### Relationship Types

| Type | Description | Example |
|------|-------------|---------|
| `MANAGER` | Controls resource lifecycle | ASG → EC2, CloudFormation → any |
| `CONSUMER` | Depends on this resource | Target Group → EC2, Lambda → S3 |
| `DEPENDENCY` | Resource depends on this | EC2 → AMI, EC2 → EBS |
| `NETWORK` | Network context | EC2 → VPC, EC2 → Security Group |
| `IDENTITY` | Permission/encryption context | EC2 → IAM Profile, RDS → KMS Key |
| `TRUST` | Trust relationship | IAM Role → AWS Account |
| `REPLICATION` | Data replication | S3 → S3 (cross-region) |

### Blast Radius Scoring

Blast radius is calculated using weighted resource criticality:

| Resource Type | Weight | Rationale |
|---------------|--------|-----------|
| Database (RDS) | 10 | Data loss risk, many dependents |
| KMS Key | 9 | Encryption dependency, cannot be recovered |
| Load Balancer | 8 | Traffic entry point, many backends |
| IAM Role | 8 | Permission boundary, many consumers |
| Compute (EC2) | 5 | Standard compute resource |

The blast radius level is determined by:
- **CRITICAL** (score 90+): Core infrastructure, high consumer count
- **HIGH** (score 60-89): Important resources with dependencies
- **MEDIUM** (score 30-59): Supporting resources
- **LOW** (score 1-29): Peripheral resources

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

### CLI Usage

```bash
# First scan - full scan, builds baseline
replimap scan --profile prod -r us-east-1

# Subsequent scans - only detect changes (fast)
replimap scan --profile prod -r us-east-1 --incremental
# Output: "Incremental scan: 3 created, 1 modified, 0 deleted, 247 unchanged"

# Force full scan even with existing state
replimap scan --profile prod -r us-east-1 --refresh-cache

# Use cache for faster repeated scans
replimap scan --profile prod -r us-east-1 --cache
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
# Generate default constraints file
replimap validate --generate-defaults

# Validate infrastructure against constraints
replimap validate -p prod -r us-east-1

# Use custom constraints file
replimap validate -p prod -r us-east-1 -c my-constraints.yaml

# Fail on high severity violations (for CI/CD)
replimap validate -p prod -r us-east-1 --fail-on high

# Export validation report
replimap validate -p prod -r us-east-1 -o report.json
replimap validate -p prod -r us-east-1 -o report.md
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

# Show reservation utilization details
replimap cost --profile prod --ri-aware --show-reservations

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

## Unused Resource Detection (P1-2)

Detect idle, underutilized, or orphaned AWS resources that may be candidates for termination to reduce costs.

### CLI Usage

```bash
# Detect all unused resources in a region
replimap unused -r us-east-1

# Only show high-confidence findings (safe to delete)
replimap unused -r us-east-1 --confidence high

# Check specific resource types only
replimap unused -r us-east-1 --types ec2,ebs,rds

# Export to JSON for automation
replimap unused -r us-east-1 -f json -o unused.json

# Export to CSV for spreadsheet analysis
replimap unused -r us-east-1 -f csv -o unused.csv

# Export Markdown report
replimap unused -r us-east-1 -f markdown -o unused.md
```

### Resource Types Detected

| Resource Type | Detection Method |
|---------------|------------------|
| EC2 Instances | Low CPU/network utilization over 14 days |
| EBS Volumes | Unattached volumes with no recent snapshots |
| RDS Instances | No database connections for extended period |
| NAT Gateways | Minimal traffic (< 1GB/month) |
| Load Balancers | No registered targets or zero traffic |
| Elastic IPs | Unassociated EIPs |
| EBS Snapshots | Orphaned snapshots with no AMI reference |

### Confidence Levels

| Level | Description | Action |
|-------|-------------|--------|
| HIGH | Very likely unused, safe to remove | Delete after verification |
| MEDIUM | Probably unused, verify before removing | Investigate usage |
| LOW | Possibly unused, investigate further | Monitor before action |

### API Usage

```python
from replimap.cost.unused_detector import (
    UnusedResourceDetector,
    ConfidenceLevel,
    UnusedReason,
)

# Create detector
detector = UnusedResourceDetector(session, region="us-east-1")

# Detect from graph
unused = detector.detect_from_graph(graph)

# Filter high-confidence findings
high_confidence = [r for r in unused if r.confidence == ConfidenceLevel.HIGH]

for resource in high_confidence:
    print(f"{resource.resource_id}: {resource.reason.description}")
    print(f"  Estimated savings: ${resource.estimated_monthly_savings}/mo")
```

## Cost Trend Analysis (P1-2)

Analyze historical AWS spending patterns using Cost Explorer to identify trends, anomalies, and forecast future costs.

### CLI Usage

```bash
# Analyze last 30 days (default)
replimap trends

# Analyze last 90 days
replimap trends --days 90

# Analyze with specific profile
replimap trends --profile production

# Export to JSON
replimap trends -f json -o trends.json

# Export to Markdown
replimap trends -f markdown -o trends.md
```

### Features

| Feature | Description |
|---------|-------------|
| **Trend Direction** | INCREASING, DECREASING, STABLE, VOLATILE |
| **Rate of Change** | $/day change rate with confidence |
| **Anomaly Detection** | Spikes, drops, unexpected services |
| **Seasonal Patterns** | Weekly/monthly cost patterns |
| **Forecasting** | 7-day and 30-day cost projections |
| **Service Breakdown** | Top services by cost |

### Output Example

```
Trend Analysis
  Direction: INCREASING
  Rate: $12.50/day
  Period change: +15.3% (+$375.00)
  Projected monthly: $4,125.00

Anomalies Detected (2)
  • 2025-01-15: spike - $892.00 (Unexpected EC2 usage)
  • 2025-01-22: drop - $45.00 (RDS instance stopped)

Top Services by Cost
  • Amazon EC2: $2,450.00
  • Amazon RDS: $890.00
  • Amazon S3: $125.00

Forecast
  Next 7 days: $875.50
  Next 30 days: $4,250.00
```

### Requirements

- AWS Cost Explorer must be enabled in your account
- IAM permissions: `ce:GetCostAndUsage`, `ce:GetCostForecast`

## Data Transfer Analysis (P1-6)

Analyze data transfer costs and identify optimization opportunities across your AWS infrastructure.

### CLI Usage

```bash
# Analyze transfer costs in a region
replimap transfer -r us-east-1

# Export detailed analysis to JSON
replimap transfer -r us-east-1 -f json -o transfer.json

# Use specific profile
replimap transfer -p production -r us-east-1
```

### Transfer Types Analyzed

| Type | Cost | Description |
|------|------|-------------|
| Cross-AZ | $0.01/GB each way | Traffic between availability zones |
| NAT Gateway | $0.045/GB + $0.045/hr | Internet access from private subnets |
| Cross-Region | $0.02-0.09/GB | Traffic between AWS regions |
| Internet Egress | $0.09/GB (first 10TB) | Traffic to the internet |
| VPC Peering | Free (same region) | Traffic between peered VPCs |

### Optimization Recommendations

The analyzer provides actionable recommendations:

- **VPC Endpoints**: Replace NAT Gateway traffic to S3/DynamoDB with free VPC endpoints
- **Same-AZ Placement**: Co-locate resources in the same AZ to avoid cross-AZ costs
- **CloudFront**: Use CDN for static content to reduce egress costs
- **PrivateLink**: Use PrivateLink for cross-VPC service access

### Output Example

```
Transfer Cost Summary
  Total paths analyzed: 47
  Estimated monthly cost: $1,245.00

Cross-AZ Traffic (12 paths)
  • EC2 → RDS: ~500 GB/mo ($10.00)
  • EC2 → ElastiCache: ~1.2 TB/mo ($24.00)

NAT Gateway Traffic (8 paths)
  • EC2 → Internet: ~2 TB/mo ($90.00)

Optimization Recommendations (3)
  ✓ Add S3 VPC Endpoint for bucket access
    Potential savings: $45.00/mo
  ✓ Move RDS read replica to same AZ as application
    Potential savings: $18.00/mo
```

## DR Readiness Assessment

Assess disaster recovery readiness for your AWS infrastructure with comprehensive analysis of RTO/RPO capabilities.

### CLI Usage

```bash
# Basic DR assessment
replimap dr assess -r us-east-1

# Specify DR region
replimap dr assess -r us-east-1 --dr-region us-west-2

# Target specific DR tier
replimap dr assess -r us-east-1 --target-tier tier_3

# Export to JSON
replimap dr assess -r us-east-1 -f json -o dr-assessment.json

# Export to HTML report
replimap dr assess -r us-east-1 -f html -o dr-report.html

# Export to Markdown
replimap dr assess -r us-east-1 -f markdown -o dr-assessment.md

# Multi-region scorecard
replimap dr scorecard
```

### DR Tiers

| Tier | Name | RTO | RPO | Description |
|------|------|-----|-----|-------------|
| 0 | No DR | N/A | N/A | Development/test environments |
| 1 | Cold Standby | 24-72h | 24h | Backup-based recovery |
| 2 | Warm Standby | 1-4h | 1h | Pilot light with scaled resources |
| 3 | Hot Standby | 15min-1h | 15min | Full replica with minimal scaling |
| 4 | Active-Active | <1min | 0 | Multi-region active-active |

### Assessment Categories

| Category | What's Analyzed |
|----------|-----------------|
| Compute | EC2 AMIs, ASG cross-region, Lambda replication |
| Database | RDS read replicas, DynamoDB global tables, Aurora Global |
| Storage | S3 cross-region replication, EBS snapshots |
| Network | Route53 health checks, Global Accelerator |
| Identity | IAM roles, cross-region access |

### Output Example

```
DR Readiness Score: 72/100

Current Tier: Warm Standby (Tier 2)
Target Tier: Hot Standby (Tier 3)

Recovery Objectives
  Estimated RTO: 45 minutes
  Estimated RPO: 30 minutes

Coverage Analysis
  Compute:   ████████░░ 80%
  Database:  █████████░ 90%
  Storage:   ██████░░░░ 60%
  Network:   █████░░░░░ 50%

Gaps Identified (3)
  ⚠ No cross-region RDS replica for primary database
    Impact: RPO would be 24+ hours for database tier
  ⚠ S3 buckets missing cross-region replication
    Impact: Data loss risk for objects created since last backup

Recommendations (4)
  ✓ Create RDS cross-region read replica
    Est. cost: $150/mo
  ✓ Enable S3 cross-region replication for critical buckets
    Est. cost: $25/mo
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

### Global Options

These options can be specified at the top level and will be inherited by all commands:

```bash
replimap [GLOBAL OPTIONS] <command> [COMMAND OPTIONS]

# Global options
  --profile, -p TEXT    AWS profile name (inherited by subcommands)
  --region, -r TEXT     AWS region (inherited by subcommands)
  --quiet, -q           Suppress verbose output
  --version, -V         Show version and exit
  --help, -h            Show help and exit
```

**Examples:**
```bash
# Profile at global level (works for all commands)
replimap -p prod scan
replimap -p prod clone --output-dir ./staging
replimap -p prod snapshot save -n "before-deploy"
replimap -p prod -r eu-west-1 graph

# Equivalent to command-level options
replimap scan --profile prod
```

### Commands

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
  --refresh, -R            Force fresh AWS scan (bypass cache)

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
  --analyze                Deep analysis mode using resource-specific analyzers
  --refresh, -R            Force fresh AWS scan (bypass cache)

# Cost estimation command (Pro+)
replimap cost [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --region, -r TEXT        AWS region [default: us-east-1]
  --vpc, -v TEXT           VPC ID to scope the scan
  --format, -f TEXT        Output format: console, table, html, json, csv [default: console]
  --output, -o PATH        Output file path
  --ri-aware               Consider Reserved Instances and Savings Plans
  --show-reservations      Show detailed reservation utilization
  --open/--no-open         Open HTML report in browser [default: open]

# Unused resource detection (Pro+)
replimap unused [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --region, -r TEXT        AWS region [default: us-east-1]
  --format, -f TEXT        Output format: console, json, csv, markdown [default: console]
  --output, -o PATH        Output file path
  --confidence, -c TEXT    Filter by confidence: high, medium, low, all [default: all]
  --types, -t TEXT         Resource types: ec2,ebs,rds,nat,elb (comma-separated)

# Cost trend analysis (Pro+)
replimap trends [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --days, -d INT           Number of days to analyze [default: 30]
  --format, -f TEXT        Output format: console, json, markdown [default: console]
  --output, -o PATH        Output file path

# Data transfer analysis (Pro+)
replimap transfer [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --region, -r TEXT        AWS region [default: us-east-1]
  --format, -f TEXT        Output format: console, json [default: console]
  --output, -o PATH        Output file path

# DR readiness assessment
replimap dr assess [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --region, -r TEXT        Primary AWS region to assess
  --dr-region TEXT         DR region to check for replicas
  --target-tier, -t TEXT   Target DR tier: tier_0-tier_4 [default: tier_2]
  --format, -f TEXT        Output format: console, json, markdown, html [default: console]
  --output, -o PATH        Output file path

replimap dr scorecard [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --output, -o PATH        Output file path

# Trust Center commands (Enterprise)
replimap trust-center report [OPTIONS]
  --format, -f TEXT        Output format: json, csv, text [default: text]
  --output, -o PATH        Output file path
  --include-records        Include detailed API call records in JSON

replimap trust-center status    # Show audit session summary
replimap trust-center clear     # Clear all audit sessions

# Topology validation
replimap validate [OPTIONS]
  --profile, -p TEXT       AWS profile name
  --region, -r TEXT        AWS region [default: us-east-1]
  --config, -c PATH        Path to constraints YAML file [default: constraints.yaml]
  --output, -o PATH        Output file path (JSON or Markdown)
  --fail-on TEXT           Fail on severity: critical, high, medium, low [default: critical]
  --generate-defaults      Generate default constraints file

# License commands
replimap license activate KEY
replimap license status
replimap license usage
replimap license deactivate [--yes]

# Credential cache management
replimap cache status      # Show cached credentials
replimap cache clear       # Clear credential cache

# Graph cache management (speeds up graph, deps, clone commands)
replimap graph-cache [OPTIONS]
  --show, -s               Show cached graph scans
  --clear, -c              Clear all cached graph scans

# Scan cache management (incremental scanning)
replimap scan-cache status                    # Show scan cache status
replimap scan-cache status -p PROFILE         # Filter by AWS profile
replimap scan-cache info -r REGION            # Show detailed cache info
replimap scan-cache info -r REGION -p PROFILE # Filter by profile
replimap scan-cache clear                     # Clear all scan cache
replimap scan-cache clear -p PROFILE          # Clear for specific profile
replimap scan-cache clear -r REGION           # Clear for specific region

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

### Graph Caching

RepliMap caches scan results to speed up subsequent commands. After running `replimap scan`, commands like `graph`, `deps`, `clone`, `audit`, and `cost` can use cached data (<1s) instead of re-scanning (90s+).

```bash
# First scan - full AWS scan (slow)
replimap scan --profile prod -r us-east-1

# Subsequent commands use cached graph (fast)
replimap graph --profile prod -r us-east-1      # Uses cache
replimap deps sg-12345 -r us-east-1             # Uses cache

# Force fresh scan (bypass cache)
replimap graph --profile prod -r us-east-1 --refresh
replimap deps sg-12345 -r us-east-1 --refresh

# Manage graph cache
replimap graph-cache --show     # List all cached scans
replimap graph-cache --clear    # Clear all cached scans
```

**Cache Location**: `~/.replimap/cache/graphs/`

**Cache TTL**: 1 hour (configurable)

| Command | Uses Cache | `--refresh` Flag |
|---------|------------|------------------|
| `scan` | Saves to cache | N/A |
| `graph` | Yes | Yes |
| `deps` | Yes | Yes |
| `clone` | Yes | Yes |
| `audit` | Yes | Yes |
| `cost` | Yes | Yes |

### Scan Cache (Incremental Scanning)

For incremental scanning workflows, RepliMap maintains a separate scan cache:

```bash
# Show scan cache status
replimap scan-cache status
replimap scan-cache status -p prod    # Filter by profile

# Show detailed info for a region
replimap scan-cache info -r us-east-1
replimap scan-cache info -r us-east-1 -p prod

# Clear scan cache
replimap scan-cache clear
replimap scan-cache clear -p prod           # Clear for profile
replimap scan-cache clear -r us-east-1      # Clear for region
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

RepliMap uses a **graph-based engine** with unified SQLite storage and an enhanced rendering pipeline:

```
┌─────────────┐    ┌──────────────────┐    ┌───────────────┐    ┌────────────────────┐
│   Scanners  │───▶│ UnifiedGraphEngine│───▶│ Transformers  │───▶│ Enhanced Renderer  │
│  (AWS API)  │    │ (SQLite Backend) │    │  (Pipeline)   │    │   (Terraform v2)   │
└─────────────┘    └──────────────────┘    └───────────────┘    └────────────────────┘
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
2. **UnifiedGraphEngine**: Build dependency graph with SQLite backend
   - `:memory:` mode for ephemeral/fast scans
   - File mode for persistent/large scans
   - NetworkX projection on-demand for complex algorithms
3. **Transformers**: Apply sanitization, downsizing, renaming
4. **Enhanced Renderer**: Generate production-ready Terraform with intelligent features

### Unified Storage System

RepliMap uses a unified SQLite-based storage layer (`replimap/core/unified_storage/`) that provides:

| Feature | Description |
|---------|-------------|
| **Single Backend** | SQLite for ALL scales (no separate in-memory vs file backends) |
| **Memory Mode** | `:memory:` for ephemeral, fast operations |
| **File Mode** | Persistent storage with WAL for concurrency |
| **FTS5 Search** | Full-text search for resource discovery |
| **Recursive CTEs** | Fast path finding and dependency traversal |
| **Snapshots** | Native SQLite `backup()` API for point-in-time captures |
| **NetworkX Projection** | On-demand graph projection for complex algorithms |
| **Scan Sessions** | Ghost Fix: track resource lifecycle with `scan_id` tagging |
| **Phantom Nodes** | Placeholder nodes for cross-account/missing dependencies |
| **zlib Compression** | 80-90% disk savings for JSON attributes |
| **Schema Migration** | Version-based schema upgrades with idempotent migrations |

```python
from replimap.core.unified_storage import UnifiedGraphEngine, Node, Edge

# Memory mode (ephemeral)
engine = UnifiedGraphEngine()

# File mode (persistent)
engine = UnifiedGraphEngine(cache_dir="~/.replimap/cache/profile")

# Add resources
engine.add_nodes([Node(id="vpc-1", type="aws_vpc")])
engine.add_edges([Edge(source_id="subnet-1", target_id="vpc-1", relation="in")])

# Graph algorithms
order = engine.safe_apply_order()  # Terraform apply order
deps = engine.get_dependencies("subnet-1", recursive=True)
critical = engine.get_most_critical_resources(top_n=10)

# Scan session management (Ghost Fix)
session = engine.start_scan(profile="prod", region="us-east-1")
engine.add_nodes([Node(id="vpc-2", type="aws_vpc")])  # Auto-tagged with scan_id
engine.end_scan(session.id)

# Cleanup stale resources from previous scans
removed = engine.cleanup_stale_resources(session.id)
```

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
│   │   ├── graph_engine.py  # Legacy NetworkX graph wrapper
│   │   ├── unified_storage/  # Unified SQLite graph storage
│   │   │   ├── __init__.py   # Package exports
│   │   │   ├── base.py       # Node, Edge, ResourceCategory, GraphBackend
│   │   │   ├── sqlite_backend.py  # SQLite backend with FTS5, CTEs
│   │   │   └── engine.py     # UnifiedGraphEngine facade
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
│   │   ├── topology_constraints.py # Topology constraints validation (P3-3)
│   │   ├── logging.py       # Structured logging with structlog
│   │   └── graph_tracer.py  # Graph processing phase tracer
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
│   ├── deps/                # Resource-specific dependency analyzers
│   │   ├── models.py        # Dependency, DependencyAnalysis, BlastRadius
│   │   ├── base_analyzer.py # ResourceDependencyAnalyzer base class
│   │   ├── blast_radius.py  # Weighted blast radius calculator
│   │   ├── reporter.py      # Analyzer output formatter
│   │   └── analyzers/       # Resource-specific analyzers
│   │       ├── ec2.py       # EC2 Instance analyzer
│   │       ├── security_group.py # Security Group analyzer
│   │       ├── iam_role.py  # IAM Role analyzer
│   │       ├── rds.py       # RDS Instance analyzer
│   │       ├── asg.py       # Auto Scaling Group analyzer
│   │       ├── s3.py        # S3 Bucket analyzer
│   │       ├── lambda_func.py # Lambda Function analyzer
│   │       ├── elb.py       # ELB/ALB analyzer
│   │       └── elasticache.py # ElastiCache analyzer
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
├── tests/                   # pytest test suite (2100+ tests)
├── .github/workflows/       # CI/CD
├── .replimap.yaml           # Project configuration (optional)
├── pyproject.toml
├── CHANGELOG.md             # Version history
└── README.md
```

## Observability

RepliMap includes built-in observability infrastructure for debugging, performance analysis, and graph processing inspection.

### Structured Logging

Structured logging with `structlog` provides consistent, machine-parseable logs.

```python
from replimap.core.logging import (
    configure_logging,
    get_logger,
    LogContext,
    Timer,
    ScanMetrics,
)

# Configure logging (call once at startup)
configure_logging(json_output=False, level="DEBUG")

# Get a logger
logger = get_logger("my_component")
logger.info("starting scan", region="us-east-1", vpc_count=5)

# Temporary context binding
with LogContext(request_id="abc123", user="admin"):
    logger.info("processing request")  # includes request_id and user

# Time operations automatically
with Timer("api_call", logger=logger):
    result = expensive_operation()
# Logs: "api_call completed" with duration_ms

# Collect scan metrics
metrics = ScanMetrics()
metrics.record_api_call("DescribeInstances", 0.045, success=True)
metrics.record_api_call("DescribeVpcs", 0.032, success=True)
metrics.record_resource("aws_instance", 15)

summary = metrics.summary()
# Returns: {total_api_calls, failed_api_calls, p95_latency_ms, resources_by_type}
```

**Features:**
- JSON output for production, human-readable for development
- Automatic sensitive data redaction (passwords, tokens, API keys)
- Context binding for request tracing
- Built-in timing utilities
- Scan metrics collection with p95 latency

### Graph Tracer

Debug graph processing by capturing snapshots at each phase.

```python
from replimap.core.graph_tracer import (
    init_tracer,
    get_tracer,
    GraphPhase,
)

# Initialize tracer (creates output directory)
tracer = init_tracer(output_dir=".replimap/traces")

# Capture snapshots at each processing phase
tracer.snapshot(GraphPhase.DISCOVERY, graph, "Initial resource discovery")
# ... process graph ...
tracer.snapshot(GraphPhase.LINKING, graph, "After edge linking")
# ... more processing ...
tracer.snapshot(GraphPhase.FINAL, graph, "Final optimized graph")

# Compare two phases
diff = tracer.diff(GraphPhase.DISCOVERY, GraphPhase.FINAL)
print(f"Nodes added: {diff.nodes_added}")
print(f"Nodes removed: {diff.nodes_removed}")
print(f"Edges added: {diff.edges_added}")

# Export for visualization
tracer.export_summary()  # Creates summary.json
# Individual phases exported as .graphml (Gephi/Cytoscape compatible)
```

**Processing Phases:**

| Phase | Description |
|-------|-------------|
| `DISCOVERY` | Initial resource scan results |
| `LINKING` | Edge creation between resources |
| `PHANTOM_RESOLUTION` | Cross-account/region reference resolution |
| `SANITIZATION` | Sensitive data removal |
| `OPTIMIZATION` | Graph simplification |
| `VARIABLE_INJECTION` | Terraform variable extraction |
| `FINAL` | Ready for rendering |

**Export Formats:**
- `.graphml` - Open in Gephi or Cytoscape for visual analysis
- `.json` - Machine-readable snapshot with metadata

## Support

- **Documentation**: [replimap.com/docs](https://replimap.com/docs)
- **Issues**: [GitHub Issues](https://github.com/RepliMap/replimap/issues)
- **Email**: [support@replimap.com](mailto:support@replimap.com)

## License

Proprietary - See [LICENSE](./LICENSE) for details.

Copyright (c) 2025 RepliMap
