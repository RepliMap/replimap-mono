# Changelog

All notable changes to RepliMap will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Core Engine Deep Dive** - Security, resilience, and performance improvements
  - **Security-Critical Sanitization Middleware** (`replimap/core/sanitizer.py`)
    - Sanitizes sensitive data BEFORE cache/graph storage (SEC-001 fix)
    - HIGH_RISK_FIELDS: EC2 UserData, Lambda Environment.Variables always redacted
    - MEDIUM_RISK_FIELDS: PolicyDocument, Scripts scanned for secrets
    - SAFE_FIELDS: IDs, status, timestamps skipped for performance
    - Pattern detection: AWS access keys, connection strings, bearer tokens
  - **Coordinated Retry Logic** (`replimap/core/retry.py`)
    - `with_retry` decorator for sync functions with exponential backoff
    - `async_retry` decorator for async functions
    - FATAL_ERRORS set for immediate failure (no retry on AccessDenied, etc.)
    - Configurable via environment: REPLIMAP_MAX_RETRIES, REPLIMAP_RETRY_DELAY
  - **AWS Client Configuration** (`replimap/core/aws_config.py`)
    - BOTO_CONFIG with `max_attempts=1` to prevent retry storms (BUG-001 fix)
    - Connect/read timeouts to prevent hanging on network issues
  - **Circuit Breaker Pattern** (`replimap/core/circuit_breaker.py`)
    - CLOSED/OPEN/HALF_OPEN states for resilient AWS service calls
    - CircuitBreakerRegistry for per-region/service isolation
    - Automatic recovery after configurable timeout
  - **Phantom Nodes for Partial Scans** (`replimap/core/graph_engine.py`)
    - Creates placeholder nodes for missing dependencies (ARCH-004 fix)
    - `is_phantom` and `phantom_reason` fields on ResourceNode
    - Replaced during graph merge when real resource discovered
  - **Tarjan's SCC Algorithm** for cycle detection
    - `find_strongly_connected_components()` for dependency analysis
    - `get_safe_dependency_order()` handles cycles gracefully
    - Useful for security group circular dependencies
  - **Graph Merge for Map-Reduce** pattern
    - `GraphEngine.merge()` combines worker results lock-free
    - Phantom nodes replaced by real nodes during merge
  - **Memory Optimization**
    - `@dataclass(slots=True)` on ResourceNode (~40% memory reduction)
    - `sys.intern()` for region strings
  - **40 new tests** covering all core engine improvements
- **Graph Visualization Optimization** - Major improvements to infrastructure visualization
  - **Link Classification**: Toggle between traffic flow and dependency views
  - **Summary Links**: Cross-VPC connection summaries for overview mode
  - **Cost Overlay**: Heat map showing resource costs by tier (low/medium/high/critical)
  - **Blast Radius Analysis**: Server-side impact calculation for resource changes
  - **Tool Modes**: Select/Trace/Blast/Cost modes for click disambiguation
  - **Drift Visualization**: Highlight resources drifted from Terraform state
  - **Orphan Detection**: Find unused resources with cost savings estimates
  - **Smart Aggregation**: Only aggregate similar resources (>80% homogeneity check)
  - **D3 fx/fy Pinning**: Preserve Python-calculated layout positions in D3
  - **Edge Routing**: Curved paths for cross-VPC links
  - **Level of Detail**: Hide labels when zoomed out for performance
  - **Breadcrumbs**: Navigation history with ESC key to go back
- **Blast Radius Analyzer** (Pro+ feature) - Impact analysis for resource changes
  - `replimap blast RESOURCE_ID` command to analyze deletion/modification impact
  - Dependency graph visualization showing what will be affected
  - Impact scoring by resource type (CRITICAL/HIGH/MEDIUM/LOW)
  - Safe deletion order recommendations
  - Multiple output formats: console, tree, table, HTML (D3.js), JSON
  - VPC scoping with `--vpc` option
  - Configurable depth with `--depth` option
- **Cost Estimator** (Pro+ feature) - Monthly AWS cost estimation
  - `replimap cost` command to estimate infrastructure costs
  - Resource-level cost breakdown by category (COMPUTE, DATABASE, STORAGE, NETWORK)
  - AWS pricing data for EC2, RDS, ElastiCache, EBS, NAT Gateway, ALB/NLB, Lambda
  - Regional price multipliers for accurate estimates
  - Reserved instance pricing tiers (1Y/3Y/Spot/Savings Plan)
  - Optimization recommendations with potential savings
  - Multiple output formats: console, table, HTML (Chart.js), JSON, CSV
- Graph-based selection engine for intelligent resource filtering
  - Selection modes: VPC_SCOPE, ENTRY_POINT, TAG_BASED
  - Boundary handling for network, identity, and global resources
  - Clone vs reference decision matrix
  - YAML configuration file support for complex selection scenarios
- New CLI options: `--scope`, `--entry`, `--config`
- Scan result caching with `--cache` flag for incremental scans
- **Makefile generation** for easier Terraform workflow management
  - Targets: `init`, `plan`, `apply`, `destroy`, `validate`, `fmt`, `clean`, etc.
  - Filtered planning: `plan-target`, `plan-include`, `plan-exclude`
  - JSON output: `plan-json` for automation
  - Quick validation: `quick-validate` (no tfvars needed)
  - State management: `state-list`, `state-show`, `state-mv`, `state-rm`
- **test-terraform.sh** script for automated validation
  - Phases: fmt check → init → validate → plan (optional)
  - Colored output with clear pass/fail indicators
- **tfplan.txt** human-readable plan output alongside binary tfplan
- **terraform fmt** integration - auto-formats generated files
- **terraform.tfvars.example** with smart variable detection
  - Includes AWS CLI commands for finding AMIs, certificates, etc.
  - All dynamic variables with helpful comments
- **httpx dependency** for license API validation

### Changed
- **License key format**: Updated to `RM-XXXX-XXXX-XXXX-XXXX` (RM prefix for RepliMap brand)
  - Aligns CLI with backend API format
  - Implemented real API validation via httpx
  - Added `REPLIMAP_LICENSE_API` environment variable for API URL configuration
- Legacy filter options (`--vpc`, `--types`) marked as deprecated but still supported
- RDS password variables now have default placeholder for `terraform plan` to succeed

### Fixed
- **Boundary resource handling**: VPC Peering and Transit Gateway routes are now commented out with clear instructions (prevents staging→production routing)
- **ASG Target Group ARNs**: Now searches graph by ARN and name, comments out if not found (prevents hardcoded production ARN leakage)
- **EBS Snapshot IDs**: Commented out by default for staging (creates empty volumes)
- **ElastiCache Redis 6+ version format**: Strips patch version (6.2.6 → 6.2) as required by Terraform
- **S3 bucket name length**: Skips environment suffix if name would exceed 63 characters
- **Security Group circular dependencies**: Rules referencing other SGs use separate `aws_security_group_rule` resources

## [0.1.0] - 2025-01-XX

### Added

#### Core Features
- Graph-based AWS resource scanning engine using NetworkX
- Support for VPC, Subnet, Security Group, EC2, RDS, and S3 resources
- Dependency tracking between resources (VPC → Subnet → EC2)
- Topological sorting for correct Terraform resource ordering

#### Scanners (24 Resource Types)
- VPC Scanner: Scans VPCs, Subnets, and Security Groups
- EC2 Scanner: Scans EC2 instances with AMI and security group associations
- RDS Scanner: Scans RDS instances and DB Subnet Groups
- S3 Scanner: Scans S3 bucket configurations
- Networking Scanner: Internet Gateways, NAT Gateways, Route Tables, VPC Endpoints
- Compute Scanner: Launch Templates, Auto Scaling Groups, ALB/NLB, Target Groups, Listeners
- ElastiCache Scanner: ElastiCache Clusters and Subnet Groups, DB Parameter Groups
- Storage Scanner: EBS Volumes, S3 Bucket Policies
- Messaging Scanner: SQS Queues, SNS Topics
- Async Scanner Base: Support for concurrent scanning with aiobotocore

#### Transformers
- Sanitization Transformer: Removes secrets, passwords, and sensitive data
- Downsize Transformer: Reduces EC2, RDS, ElastiCache, Launch Template, and ASG sizes
- Renaming Transformer: Converts prod → staging naming conventions
- Network Remapper: Updates resource references for new environment

#### Renderers
- Terraform Renderer (Free+): Generates Terraform HCL files
- CloudFormation Renderer (Solo+): Generates AWS CloudFormation YAML
- Pulumi Renderer (Pro+): Generates Pulumi Python code

#### Commercial Features
- License management system with plan tiers (Free, Solo, Pro, Team, Enterprise)
- Feature gating with `@feature_gate` and `@require_plan` decorators
- Usage tracking with monthly quotas
- Local license caching with offline grace period

#### CLI Commands
- `replimap scan`: Scan AWS resources and build dependency graph
- `replimap clone`: Generate Infrastructure-as-Code from scan
- `replimap load`: Load and display saved graphs
- `replimap license activate`: Activate a license key
- `replimap license status`: Show current license and plan
- `replimap license usage`: Display usage statistics
- `replimap license deactivate`: Remove license
- `replimap profiles`: List available AWS profiles
- `replimap cache status`: Show cached credentials
- `replimap cache clear`: Clear credential cache

#### CLI UX Improvements
- Interactive mode (`-i`) for guided setup
- AWS profile region auto-detection from `~/.aws/config`
- MFA credential caching (12-hour TTL) to avoid repeated prompts
- Short `-h` option for help on all commands

#### Performance & Reliability
- Parallel scanning with ThreadPoolExecutor (4 workers default)
- AWS rate limit handling with exponential backoff retry
- Configurable via environment variables (`REPLIMAP_MAX_WORKERS`, `REPLIMAP_MAX_RETRIES`)
- Dev mode (`REPLIMAP_DEV_MODE=1`) for local development without license limits

#### Developer Experience
- Rich console output with progress spinners and tables
- Comprehensive test suite with 331 tests
- CI/CD with GitHub Actions (Python 3.11, 3.12, 3.13, 3.14)
- ruff for formatting and linting
- mypy for type checking
- Timezone-aware datetime handling throughout

### Security
- Read-only AWS permissions only
- Local data processing (no external uploads)
- Automatic sensitive data sanitization
- Minimal IAM policy requirements

## Plan Comparison

| Feature | Free | Solo ($49) | Pro ($99) | Team ($199) | Enterprise ($499+) |
|---------|------|------------|-----------|-------------|-------------------|
| Resources/Scan | 5 | ∞ | ∞ | ∞ | ∞ |
| Scans/Month | 3 | ∞ | ∞ | ∞ | ∞ |
| AWS Accounts | 1 | 1 | 3 | 10 | ∞ |
| Terraform Output | ✅ | ✅ | ✅ | ✅ | ✅ |
| CloudFormation | ❌ | ✅ | ✅ | ✅ | ✅ |
| Pulumi | ❌ | ❌ | ✅ | ✅ | ✅ |
| Async Scanning | ❌ | ✅ | ✅ | ✅ | ✅ |
| Web Dashboard | ❌ | ❌ | ✅ | ✅ | ✅ |
| Collaboration | ❌ | ❌ | ❌ | ✅ | ✅ |
| SSO | ❌ | ❌ | ❌ | ❌ | ✅ |

---

[Unreleased]: https://github.com/replimap/replimap/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/replimap/replimap/releases/tag/v0.1.0
