# Changelog

All notable changes to RepliMap will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Unified Error Collection** - ScanErrorCollector mechanism for scanner error tracking
  - `replimap/core/errors.py` - ErrorSeverity enum (WARNING/ERROR/CRITICAL), ScanError dataclass
  - `ScanErrorCollector` class with Rich console summary output
  - `@handle_scan_error` decorator for automatic error capture and classification
  - Error classification: AccessDenied, Throttled, NotFound, Timeout, generic types
  - Global collector with `get_scan_error_collector()` and `reset_scan_error_collector()`
  - 23 comprehensive tests in `tests/test_scan_error_collector.py`

- **Enhanced Secret Scrubber** - Full-replacement strategy for Base64 UserData integrity
  - `ScrubResult` dataclass tracking modification state and secrets found
  - `scrub_user_data()` - Replaces ENTIRE UserData when secrets detected (preserves Base64)
  - `scrub_attribute()` - Smart attribute-level scrubbing with result tracking
  - `scrub_resource()` - Resource-level scrubbing with summary generation
  - `get_summary()` - Statistics on scrubbed resources and secret types
  - Prevents Terraform apply failures from corrupted Base64 encoding
  - 9 new tests in `tests/test_secret_scrubber.py` for Base64 integrity

- **Secret Scrubber** - Automatic detection and redaction of sensitive data in generated Terraform
  - `replimap/core/security/scrubber.py` - SecretScrubber class with regex patterns
  - Detects: AWS access keys (AKIA/ASIA), secret keys, private keys, database URLs, tokens
  - Integrated into TerraformRenderer - scrubs user_data, environment, container_definitions
  - Warning summary shown after clone: "Sensitive Data Redacted: AWS Access Key ID: 2"
  - 36 comprehensive tests in `tests/test_secret_scrubber.py`

- **First-Run Privacy Message** - One-time welcome message building user trust
  - `replimap/core/first_run.py` - First-run experience module
  - Shows "100% Local & Private" message on first run only
  - `replimap --privacy` flag to show privacy info anytime
  - Marker file at `~/.replimap/.first_run_complete` prevents repeat
  - Hidden `replimap cache reset-first-run` command for testing

- **High-Concurrency AWS Config** - Adaptive retry mode for large account scanning
  - `HIGH_CONCURRENCY_CONFIG` with adaptive retry mode and 50 connection pool
  - `get_boto_config(mode="high-concurrency")` for large accounts
  - Maintains existing custom retry decorator design
  - 22 tests in `tests/test_aws_config.py`

- **Cross-Platform Browser Launcher** - Smart browser opening with WSL2 support
  - `replimap/core/browser.py` - Cross-platform browser launcher module
  - Detects WSL2 environment via kernel release string ("microsoft" or "wsl")
  - WSL2 strategy: wslview (if available) → wslpath + cmd.exe /C start
  - Native strategy: Python webbrowser module
  - `cwd="/mnt/c/"` eliminates "UNC paths not supported" warning
  - Fallback shows manual instructions with Windows path for WSL users
  - 17 tests in `tests/test_browser.py`

- **Audit Concise Summary** - Compact audit output instead of 1000+ lines of findings
  - `replimap/audit/terminal_reporter.py` - New terminal reporter module
  - Default: Summary table + top 5 critical/high issues (~30 lines)
  - `--verbose` / `-V` flag for full findings output
  - Only FAILED checks counted (filters out PASSED)
  - Severity normalization (handles None/unknown)
  - Resource name truncation (prevents line overflow)
  - Score and grade shown in summary table
  - 26 tests in `tests/test_audit_terminal_reporter.py`

- **Improved CLI Help Formatting** - Clean, readable command help output
  - Uses `\b` markers to preserve example formatting in docstrings
  - All commands fixed: scan, clone, audit, graph, deps, cost, dr, drift,
    unused, validate, transfer, trends, remediate, load, profiles
  - Before: Examples ran together on one unreadable line
  - After: Properly indented, grouped examples with section headers

- **Improved Renderer Skip Summary** - Compact output for unsupported resource types
  - Uses Counter for tracking, shows top 5 types with counts
  - Single-line output: "ℹ Skipped 133 resources: type1 (N), type2 (N), +X more types"
  - Handles zero-skip case gracefully

- **Global CLI Options** - Profile and region options available at top level
  - `replimap -p <profile> <command>` works for all commands
  - `replimap -r <region> <command>` works for all commands
  - Subcommands (snapshot, dr) inherit from global options if not set locally
  - Example: `replimap -p prod snapshot save -n "before-deploy"`

- **Global Graceful Shutdown** - Clean Ctrl-C handling across all commands
  - `replimap/core/concurrency.py` - Thread pool factory with centralized tracking
    - `create_thread_pool()` - Factory for tracked ThreadPoolExecutor instances
    - `shutdown_all_executors()` - Emergency shutdown for all active pools
    - `check_shutdown()` - Cooperative cancellation for long-running loops
    - WeakSet-based tracking for automatic cleanup
  - `replimap/core/signals.py` - Global signal handlers
    - SIGINT handler shows "Cancelled by user" and exits cleanly (code 130)
    - SIGTERM handler shows "Terminated" and exits cleanly (code 143)
    - Uses `os._exit()` to avoid Python threading cleanup tracebacks
  - Eliminates ugly threading exceptions on Ctrl-C during scans

- **Observability Infrastructure** - Structured logging and graph tracing for debugging
  - `replimap/core/logging.py` - Structured logging with `structlog`
    - `configure_logging()` - Environment-aware formatters (JSON for prod, human-readable for dev)
    - `LogContext` - Context manager for request/operation binding
    - `Timer` - Context manager for timing operations with auto-logging
    - `ScanMetrics` - API call statistics, p95 latency, error counts
    - Automatic redaction of sensitive fields (passwords, tokens, keys)
  - `replimap/core/graph_tracer.py` - Graph processing debugger
    - 7 processing phases: DISCOVERY → LINKING → PHANTOM_RESOLUTION → SANITIZATION → OPTIMIZATION → VARIABLE_INJECTION → FINAL
    - `GraphSnapshot` - Captures node/edge state at any phase
    - `GraphDiff` - Calculates changes between phases
    - Export to GraphML (Gephi/Cytoscape) and JSON formats
    - Global singleton pattern with `init_tracer()`/`get_tracer()`
  - HTML structural validation tests (BeautifulSoup-based)
    - DOM structure, JavaScript function, CSS class validation
    - XSS prevention and accessibility testing

### Fixed

- **Windows/WSL Compatibility** - Fixed `AttributeError: os.uname not available on Windows`
  - `replimap/core/browser.py` now uses `platform.release()` instead of `os.uname()`
  - Added `is_remote_ssh()` - Detects SSH sessions via SSH_CLIENT/SSH_TTY env vars
  - Added `is_container()` - Detects Docker/Podman via /.dockerenv and cgroups
  - Added `can_open_browser()` - Pre-check for browser opening capability
  - WSL detection via kernel release string ("microsoft" or "wsl") with /proc/version fallback
  - 14 new tests in `tests/test_browser.py` for cross-platform detection

- **Unused Command API** - Fixed `AttributeError: 'UnusedResourceDetector' has no attribute 'detect_from_graph'`
  - Changed constructor from `UnusedResourceDetector(session, region)` to `UnusedResourceDetector(region=, account_id=)`
  - Changed method from `detect_from_graph(graph)` to async `scan(graph, check_metrics=True)`
  - Returns `UnusedResourcesReport` with `.unused_resources` list

- **Trends Command API** - Fixed `analyze() got an unexpected keyword argument 'days'`
  - Changed constructor from `CostTrendAnalyzer(session)` to `CostTrendAnalyzer(region=, account_id=)`
  - Changed parameter from `days=` to `lookback_days=`
  - Fixed attribute access: `result.trend` → `result.overall_trend`
  - Fixed service data: `result.service_breakdown` → `result.service_trends`
  - Fixed forecast: now sums list of `CostForecastResult` objects

- **XSS Vulnerability in Drift Report** - Jinja2 autoescape wasn't working for `.html.j2` files
  - Changed from `select_autoescape(["html", "xml"])` to `autoescape=True`

- **Drift Report Remediation Command Tests** - Comprehensive test suite for terraform command generation
  - 44 new tests in `test_drift_reporter.py` covering all edge cases
  - `TestSanitizeTfResourceName` - 15 tests for TF resource name sanitization
  - `TestShellQuote` - 11 tests for shell quoting safety
  - `TestGenerateRemediationCmd` - 11 tests for all drift types
  - `TestGetDriftClassification` - 7 tests for classification logic

- **Resource Dependency Analyzers** - Deep dependency analysis for AWS resources
  - `deps --analyze` mode for comprehensive resource dependency analysis
  - 9 specialized analyzers: EC2, Security Group, IAM Role, RDS, ASG, S3, Lambda, ELB, ElastiCache
  - Relationship classification: MANAGER, CONSUMER, DEPENDENCY, NETWORK, IDENTITY, TRUST, REPLICATION
  - Weighted blast radius scoring based on resource criticality
  - IaC detection (CloudFormation, Terraform, manual)
  - Contextual warnings for cross-account access, encryption keys, managed resources
  - EC2 analyzer detects: ASG managers, Target Group consumers, EBS/AMI dependencies, KMS encryption keys
  - Security Group analyzer detects: EC2/RDS/Lambda consumers, cross-account rules
  - IAM Role analyzer detects: trust relationships, attached policies, consumer services
  - RDS analyzer detects: read replicas, subnet groups, parameter groups, KMS keys
  - S3 analyzer detects: replication targets, Lambda/SQS/SNS notifications, encryption
  - Lambda analyzer detects: layers, event sources (SQS/Kinesis/DynamoDB), VPC config
  - ELB/ALB analyzer detects: target groups, SSL certificates, security groups
  - ElastiCache analyzer detects: replication groups, parameter groups

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

### Fixed
- **Drift Report Terraform Command Generation** - Comprehensive fixes for remediation commands
  - Empty resource IDs now use fallback names (`unknown` or `imported`) instead of generating invalid TF addresses
  - Resource IDs starting with digits now get `r_` prefix (e.g., `123-bucket` → `r_123_bucket`) for valid TF names
  - Consecutive special characters collapsed to single underscore (e.g., `foo///bar` → `foo_bar`)
  - Extended special character sanitization: handles `@#$%^&*()[]{}|\\'"<>,?!=+~\`` in addition to `-./: `
  - Shell quoting for resource IDs with spaces or shell metacharacters in `terraform import` commands
  - Resource IDs with only special characters (e.g., `///`) now use `imported` fallback name

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
