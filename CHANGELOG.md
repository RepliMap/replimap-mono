# Changelog

All notable changes to RepliMap will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **FOMO Design for Audit CLI Output** - Rich-based output with plan-based gating
  - New `replimap/ui/` module with FOMO design functions
  - `print_audit_findings_fomo()` - Shows ALL issue titles (even for FREE users)
  - First CRITICAL finding gets 2-line remediation preview (taste of value)
  - Remaining remediation details are gated by plan tier
  - Beautiful Rich panels with severity icons and color coding
  - Upgrade prompts with v3.2 pricing ($49/$99/$199/$500)
  - Philosophy: "Gate at OUTPUT, not at SCAN" - users see full value, pay to export

- **v3.2 Pricing Matrix** - Updated feature gating implementation
  - 25+ new `PlanFeatures` fields for storage, trust center, compliance, support
  - 20+ new gate check functions in `replimap/licensing/gates.py`
  - Storage layer: local cache, snapshots, retention policies
  - Trust Center: TEAM+ feature with export and compliance verification
  - Regional compliance: APRA CPS 234, Essential Eight, RBNZ, NZISM (Enterprise)
  - Remediate beta access (Pro+)
  - Email support SLA by tier (48h Solo, 24h Pro, 12h Team, 4h Enterprise)

- **CLI Integration for P0-P3 Features** - Comprehensive CLI commands for all new features
  - `replimap scan --trust-center` - Enable API auditing during scan
  - `replimap scan --incremental` - Incremental scanning mode
  - `replimap trust-center report/status/clear` - Trust Center management
  - `replimap validate` - Topology constraints validation with YAML config
  - `replimap cost --ri-aware --show-reservations` - RI-aware pricing
  - `replimap unused` - Detect unused/underutilized resources
  - `replimap trends` - Cost trend analysis with anomaly detection
  - `replimap transfer` - Data transfer cost analysis
  - `replimap dr assess/scorecard` - DR readiness assessment

- **Unused Resource Detection CLI (P1-2)** - Find idle resources
  - Detects low CPU EC2, unattached EBS, idle RDS, unused NAT/ELB
  - Confidence levels: high/medium/low
  - Export to JSON, CSV, Markdown

- **Cost Trend Analysis CLI (P1-2)** - Spending pattern analysis
  - Uses AWS Cost Explorer for historical data
  - Trend direction, anomaly detection, forecasting
  - 7-day and 30-day cost projections

- **Data Transfer Analysis CLI (P1-6)** - Transfer cost optimization
  - Cross-AZ traffic detection
  - NAT Gateway analysis
  - VPC Endpoint optimization recommendations

- **DR Readiness Assessment CLI** - Disaster recovery analysis
  - `replimap dr assess` for single-region DR assessment
  - DR tier classification (0-4)
  - RTO/RPO estimation
  - Coverage analysis and gap identification
  - Export to JSON, Markdown, HTML

- **Trust Center Audit System (P1-9)** - Enterprise-grade API call auditing for compliance
  - `TrustCenter` singleton class for centralized audit management
  - Automatic boto3 event hooks capture all AWS API calls transparently
  - `OperationClassifier` categorizes operations as READ/WRITE/DELETE/ADMIN
  - Session-based grouping of related API calls
  - `TrustCenterReport` generation with compliance statements
  - 100% Read-Only operation verification for enterprise security reviews
  - Multi-format export: JSON, CSV, human-readable text
  - Thread-safe operations with session isolation
  - Sensitive parameter sanitization (passwords, tokens redacted)
  - Designed for Australian Big 4 bank procurement requirements

- **Incremental Scanning (P3-1)** - Efficient change detection using ResourceGroupsTaggingAPI
  - `IncrementalScanner` uses AWS tagging API for fast change detection
  - `ResourceFingerprint` model with content hashing for modification detection
  - `ScanStateStore` with SQLite persistence for scan state
  - `ChangeSet` model tracking created/modified/deleted/unchanged resources
  - Sub-second incremental scans after initial full scan
  - Configurable state storage directory

- **Historical Snapshots (P3-2)** - Point-in-time infrastructure snapshots with 30-day retention
  - `SnapshotManager` for snapshot lifecycle management
  - `ResourceSnapshot` immutable point-in-time captures
  - `SnapshotComparison` for diff between any two snapshots
  - 30-day default retention with configurable policies
  - Full audit trail of infrastructure changes
  - SQLite storage with optional compression

- **Topology Constraints (P3-3)** - Policy-based infrastructure validation
  - `TopologyConstraint` model with multiple constraint types
  - `ConstraintType` enum: REQUIRE_TAG, REQUIRE_ENCRYPTION, PROHIBIT_RELATIONSHIP, PROHIBIT_PUBLIC_ACCESS
  - `TopologyValidator` validates infrastructure against constraints
  - `ValidationResult` with severity-based violation reporting
  - YAML configuration support for enterprise policy management
  - Default constraint templates for common security policies
  - Exception handling for approved deviations

- **RI/Savings Plan Aware Pricing (P3-4)** - Reservation-aware cost analysis
  - `ReservedInstance` and `SavingsPlanCommitment` models
  - `RIAwarePricingEngine` applies reservation discounts to cost estimates
  - `RightSizingRecommendation` considers reservation constraints
  - `ReservationWaste` detection for underutilized reservations
  - `UtilizationLevel` classification (HIGH/MEDIUM/LOW/CRITICAL)
  - Right-sizing impact analysis for reservation-constrained resources
  - Expiration warnings for reservations ending soon

- **Network ACL (NACL) Support** - Complete scanning and template generation
  - `NETWORK_ACL` added to ResourceType enum
  - `NetworkingScanner._scan_network_acls()` method with ingress/egress rule processing
  - `network_acl.tf.j2` template supporting both default and custom NACLs
  - Uses `aws_default_network_acl` for VPC defaults, `aws_network_acl` for custom

- **Right-Sizer CLI Integration** - Automatic resource optimization for dev/staging
  - `replimap clone --dev-mode` flag for cost-optimized cloning
  - Generates `right-sizer.auto.tfvars` with instance size overrides
  - Calls backend API for optimization suggestions (Solo+ feature)
  - Supports EC2, RDS, ElastiCache resource types
  - Architecture-safe recommendations (no x86↔ARM issues)
  - Strategy options: `--dev-strategy conservative` (default) or `aggressive`
  - Resource batching for large infrastructures (>100 resources per API request)
- **Generator Variable Refactoring** - Terraform variables for Right-Sizer compatibility
  - `replimap/core/naming.py` - Standardized variable naming utility
  - Per-resource instance_type/instance_class/node_type variables
  - Templates updated: ec2_instance.tf.j2, rds_instance.tf.j2, elasticache_cluster.tf.j2, launch_template.tf.j2
  - TerraformRenderer generates variables.tf with Right-Sizer compatible variables

### Changed
- **v3.2 Pricing** - Updated pricing structure
  - SOLO: $49/mo ($33/mo annual - 2 months free)
  - PRO: $99/mo ($66/mo annual - 2 months free)
  - TEAM: $199/mo ($133/mo annual - 2 months free)
  - ENTERPRISE: From $500/mo (custom pricing)

### Added (previous)
- **Sovereign Engineer Protocol (Level 2-5)** - Complete Terraform renderer refactoring
  - **SmartNameGenerator** (`replimap/renderers/name_generator.py`)
    - Deterministic Base62 hash-based naming (same input = same output, always)
    - AWS length limit enforcement per resource type (32 char default)
    - NameRegistry for collision tracking and lookup
    - Replaces non-deterministic numeric suffix approach
  - **ScopeEngine** (`replimap/core/scope.py`)
    - Boundary recognition: MANAGED, READ_ONLY, SKIP scopes
    - Default VPC/SG/NACL automatically rendered as data sources (safety)
    - Escape hatches via .replimap.yaml for advanced users
    - Pattern-based skip/force-manage rules (tag:, id:, id_prefix:)
  - **ImportBlockGenerator** (`replimap/renderers/import_generator.py`)
    - Terraform 1.5+ import block generation
    - Resource-specific import ID format handling
    - Legacy import.sh script for Terraform < 1.5
    - Complex import warnings for manual intervention
  - **RefactoringEngine** (`replimap/renderers/refactoring.py`)
    - Terraform `moved` block generation for Brownfield adoption
    - StateManifest for parsing existing Terraform state
    - ResourceMapping to identify moves vs imports
    - Prevents "destroy and recreate" disasters
  - **SemanticFileRouter** (`replimap/renderers/file_router.py`)
    - Organized output: vpc.tf, security.tf, compute.tf, etc.
    - FileRoute pattern matching per resource type
    - FileStructure tracking for multi-file output
  - **VariableExtractor** (`replimap/renderers/variable_extractor.py`)
    - DRY variable extraction from resources
    - Auto-detects region, environment, VPC ID patterns
    - Generates variables.tf and terraform.tfvars
  - **AuditAnnotator** (`replimap/renderers/audit_annotator.py`)
    - Inline security annotations in generated code
    - Noise control: only CRITICAL/HIGH inline, rest in header/report
    - SecurityCheckRunner for built-in checks (SSH open to world, etc.)
    - Full audit report generation (audit-report.md)
  - **PlanBasedDriftEngine** (`replimap/drift/plan_engine.py`)
    - Replaces COMPARABLE_ATTRIBUTES with terraform plan
    - Complete and accurate drift detection
    - DriftReporter with multiple output formats (summary, details, JSON, CI)
  - **LocalModuleExtractor** (`replimap/patterns/local_module.py`)
    - Pattern detection for VPC, ALB, RDS, Lambda, etc.
    - ModuleSuggestion with resource groupings
    - ModuleGenerator for local module structure
    - Moved block generation for module migration
  - **SchemaBootstrapper** (`replimap/core/bootstrap.py`)
    - Solves the Bootstrap Paradox (need schema to generate, need init for schema)
    - VersionAwareBootstrapper respects user's provider constraints
    - EnvironmentDetector finds existing Terraform config
    - ProviderSchemaLoader for schema-driven intelligence
  - **ConfigLoader** (`replimap/core/config.py`)
    - .replimap.yaml configuration file support
    - Hierarchical config search (cwd → parent → home)
    - Deep merge with sensible defaults
    - Escape hatches for all safety defaults
  - **EnhancedTerraformRenderer** (`replimap/renderers/terraform_v2.py`)
    - Integrates all Level 2-5 components
    - Backwards compatible with original TerraformRenderer
    - Preview mode for dry-run analysis
    - 40+ tests for new functionality

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
- **Cross-Account Variable Fallback Pattern** - Templates now use variables instead of hardcoded IDs for missing dependencies
  - 14 templates updated to use `var.unmapped_*` pattern instead of source account IDs
  - Affected templates: ec2_instance, autoscaling_group, db_subnet_group, elasticache_cluster, elasticache_subnet_group, launch_template, lb, nat_gateway, network_acl, rds_instance, security_group, vpc_endpoint
  - Turns "ResourceNotFound" runtime errors into "Undeclared variable" config errors (fail-fast)
- **ASG Target Group Ghost Configuration** - Missing target groups now use variable fallback instead of being commented out
  - Prevents silent failures where ASG launches but receives no traffic
  - Uses `var.unmapped_tg_*` for user mapping
- **S3 Long Bucket Name Collision** - Buckets > 53 chars now use `var.bucket_name_*` instead of original name
  - Prevents global namespace collision when environment suffix can't be appended
- **AWS System Tag Poisoning** - All 21 templates now filter `aws:*` prefix tags
  - Prevents `terraform apply` rejection by AWS API for reserved tag prefixes
- **UserData Base64 Sanitization** - Redacted UserData now returns valid Base64 instead of `[REDACTED]` string
  - Prevents EC2 cloud-init encoding errors on launch
- **Main Route Table Handling** - Uses `aws_default_route_table` for VPC main route tables
  - Prevents "route table already exists" errors
- **Secondary VPC CIDR Support** - Generates `aws_vpc_ipv4_cidr_block_association` for secondary CIDRs
  - Clones complete VPC network configuration
- **Terraform 1.5+ Import Blocks** - Generates `imports.tf` with native import blocks
  - Modern alternative to legacy bash import scripts
  - Remediation generator now outputs proper Terraform 1.5+ format
- **Terraform variable naming consistency**: Variable names now consistently use underscores (e.g., `lt_083_abc` not `lt-083-abc`) across templates and variables.tf - fixes "Reference to undeclared input variable" errors during `terraform plan`
- **Right-Sizer API error handling**: Improved error messages with actual API response content for debugging
- **Right-Sizer resource extraction**: Fixed `resource_type` attribute access (was incorrectly using `type`)
- **LicenseManager API**: Fixed `current_license` property access (was incorrectly called as method)
- **Right-Sizer unsupported resource types**: Removed `aws_launch_template` from client's supported types (backend API limitation)
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

| Feature | Free | Solo ($49) | Pro ($99) | Team ($199) | Enterprise ($500+) |
|---------|------|------------|-----------|-------------|-------------------|
| Resources/Scan | ∞ | ∞ | ∞ | ∞ | ∞ |
| Scans/Month | 3 | ∞ | ∞ | ∞ | ∞ |
| AWS Accounts | 1 | 1 | 3 | 10 | ∞ |
| Terraform Output | ✅ | ✅ | ✅ | ✅ | ✅ |
| CloudFormation | ❌ | ✅ | ✅ | ✅ | ✅ |
| Pulumi | ❌ | ❌ | ✅ | ✅ | ✅ |
| Full Audit Details | ❌ | ✅ | ✅ | ✅ | ✅ |
| Local Cache/Snapshots | ❌ | ✅ (5) | ✅ (15) | ✅ (30) | ✅ (∞) |
| Async Scanning | ❌ | ✅ | ✅ | ✅ | ✅ |
| Drift Detection | ❌ | ❌ | ✅ | ✅ | ✅ |
| CI/CD Mode | ❌ | ❌ | ✅ | ✅ | ✅ |
| Trust Center | ❌ | ❌ | ❌ | ✅ | ✅ |
| Compliance Mapping | ❌ | ❌ | ❌ | ❌ | ✅ |
| Email Support SLA | ❌ | 48h | 24h | 12h | 4h |
| SSO | ❌ | ❌ | ❌ | ❌ | ✅ |

---

[Unreleased]: https://github.com/replimap/replimap/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/replimap/replimap/releases/tag/v0.1.0
