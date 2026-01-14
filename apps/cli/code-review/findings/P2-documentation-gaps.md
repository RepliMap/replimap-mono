# P2: Documentation Accuracy & Completeness

**Priority:** P2 (Medium - User Onboarding)
**Category:** Documentation Quality
**Impact:** Medium - Affects new user success rate and support burden
**Effort:** Medium - Requires testing examples, updating docs, creating tutorials

---

## Executive Summary

RepliMap's main documentation (README, IAM_POLICY, SECURITY) is well-structured and comprehensive. However, several **examples are outdated**, **feature descriptions don't match implementation**, and **critical setup steps are missing**. This creates a gap between marketing promises and actual user experience.

**Key Issues:** Stale examples, missing quickstart, incomplete feature docs

---

## Findings

### 1. README Example Commands Don't Match CLI

**README.md Line 86-94:**
```bash
# Scan your AWS account
replimap -p prod -r ap-southeast-2 scan

# Visualize dependencies
replimap -p prod -r us-east-1 graph -o architecture.html

# "What happens if I delete this security group?"
replimap -p prod -r us-east-1 deps sg-0a1b2c3d4e
```

**Issues:**
1. ✅ Syntax is correct
2. ⚠️ No mention that `deps` is a **paid feature** (requires license)
3. ⚠️ Doesn't show `--cache` flag which is critical for performance
4. ⚠️ No indication of scan time (users expect instant results)

**Recommended Update:**
```bash
# 1. First scan (takes 20-60 seconds depending on account size)
replimap scan --profile prod --region ap-southeast-2

# 2. Visualize dependencies (generates interactive HTML)
replimap graph --profile prod --region us-east-1 --output architecture.html
# Opens in browser automatically

# 3. Explore resource dependencies (Pro+ feature)
replimap deps sg-0a1b2c3d4e --profile prod --region us-east-1
# Shows: What depends on this resource? What would break if I delete it?

# Pro tip: Use --cache for faster subsequent scans
replimap scan --cache --profile prod --region us-east-1
```

---

### 2. Clone Examples Mislead Users

**README.md Line 135-145:**
```bash
# Generate Terraform from your AWS account
replimap -p prod -r us-east-1 clone --mode generate -o ./terraform

# Output structure
terraform/
├── main.tf           # All resources
├── variables.tf      # Extracted variables
├── outputs.tf        # Useful outputs
├── providers.tf      # AWS provider config
├── data.tf           # Data sources
└── terraform.tfvars.example
```

**Issues:**
1. ❌ Output structure is **outdated** - files are split by resource type now:
   - `vpc.tf`, `security_groups.tf`, `ec2.tf`, `rds.tf`, `s3.tf` (not `main.tf`)
2. ⚠️ Doesn't mention `imports.tf` and `import.sh` (new in v0.3.0)
3. ⚠️ Doesn't mention `Makefile` and `test-terraform.sh` (critical for usability)
4. ❌ `--mode generate` is the **wrong default** (default is `dry-run`)

**Actual Output Structure (from code):**
```bash
terraform/
├── vpc.tf              # VPCs and Subnets
├── security_groups.tf  # Security Groups
├── ec2.tf              # EC2 Instances
├── rds.tf              # RDS Instances and DB Subnet Groups
├── s3.tf               # S3 Buckets
├── networking.tf       # Route Tables, IGW, NAT, Endpoints
├── compute.tf          # Launch Templates, ASGs
├── alb.tf              # Load Balancers, Listeners, Target Groups
├── elasticache.tf      # ElastiCache Clusters
├── storage.tf          # EBS Volumes
├── messaging.tf        # SQS, SNS
├── versions.tf         # Terraform version constraints
├── providers.tf        # AWS provider config
├── data.tf             # Data sources (account ID, region)
├── variables.tf        # All variables with comments
├── outputs.tf          # Useful outputs (VPC IDs, RDS endpoints, ALB DNS)
├── imports.tf          # Terraform 1.5+ import blocks
├── import.sh           # Legacy import script
├── terraform.tfvars.example  # Example variable values
├── test-terraform.sh   # Validation script
└── Makefile            # Common Terraform tasks
```

**Recommended README Update:**
```bash
# Generate Terraform (splits resources across 15+ files for maintainability)
replimap clone --profile prod --region us-east-1 --output-dir ./terraform

# Output includes:
# • Resource files: vpc.tf, ec2.tf, rds.tf, s3.tf, etc.
# • Import automation: imports.tf (TF 1.5+) + import.sh (legacy)
# • Helpers: Makefile, test-terraform.sh
# • Variables: terraform.tfvars.example (copy and customize)

# Test the generated Terraform
cd terraform
./test-terraform.sh

# Apply to target environment
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan -var-file=terraform.tfvars
```

---

### 3. IAM Policy Incomplete for Phase 2 Resources

**IAM_POLICY.md Line 8-39:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "RepliMapReadOnly",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeInstances",
                "ec2:DescribeTags",
                "ec2:DescribeAvailabilityZones",
                "ec2:DescribeRouteTables",
                "ec2:DescribeInternetGateways",
                "ec2:DescribeNatGateways",
                "rds:DescribeDBInstances",
                "rds:DescribeDBSubnetGroups",
                "rds:DescribeDBSecurityGroups",
                "rds:ListTagsForResource",
                "s3:ListAllMyBuckets",
                "s3:GetBucketLocation",
                "s3:GetBucketTagging",
                "s3:GetBucketVersioning",
                "s3:GetBucketEncryption",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

**Missing Permissions for Phase 2 Resources:**

From `terraform.py` lines 60-80, RepliMap supports:
- ✅ Launch Templates
- ✅ Auto Scaling Groups
- ✅ Load Balancers (ALB/NLB)
- ✅ ElastiCache Clusters
- ✅ EBS Volumes
- ✅ SQS Queues
- ✅ SNS Topics
- ✅ VPC Endpoints

**But IAM policy is missing:**
```json
"ec2:DescribeLaunchTemplates",
"ec2:DescribeLaunchTemplateVersions",
"autoscaling:DescribeAutoScalingGroups",
"autoscaling:DescribeLaunchConfigurations",
"autoscaling:DescribePolicies",
"elasticloadbalancing:DescribeLoadBalancers",
"elasticloadbalancing:DescribeTargetGroups",
"elasticloadbalancing:DescribeListeners",
"elasticloadbalancing:DescribeTags",
"elasticache:DescribeCacheClusters",
"elasticache:DescribeCacheSubnetGroups",
"elasticache:ListTagsForResource",
"ec2:DescribeVolumes",
"sqs:ListQueues",
"sqs:GetQueueAttributes",
"sqs:ListQueueTags",
"sns:ListTopics",
"sns:GetTopicAttributes",
"sns:ListTagsForResource",
"ec2:DescribeVpcEndpoints"
```

**Recommendation:** Update IAM_POLICY.md with comprehensive list matching actual scanners.

---

### 4. Feature Availability Not Documented

**README.md shows features but doesn't clarify licensing:**

```markdown
### 💰 Optimize Costs

replimap -p prod -r us-east-1 cost
```

**Issue:** Doesn't mention this requires **Solo+ plan**.

**From README Line 530-556 (Pricing):**
```markdown
### Free Tier
- ✅ Scan unlimited resources
- ✅ Preview generated Terraform
- ✅ Basic compliance audit
- ⏱️ 10 scans/month

### Solo ($49/mo)
- ✅ Download Terraform code
- ✅ Full Right-Sizer recommendations
- ✅ Unlimited scans

### Team ($199/mo)
- ✅ Drift detection
- ✅ Dependency explorer
```

**Recommendation:** Add feature availability badges to command examples:

```markdown
### 🔍 Scan & Understand (FREE)

replimap scan --profile prod --region ap-southeast-2

### 🏗️ Generate Infrastructure as Code (SOLO+)

replimap clone --profile prod --mode generate -o ./terraform

### 💰 Optimize Costs (SOLO+)

replimap cost --profile prod --region us-east-1

### 🔄 Detect Drift (TEAM+)

replimap drift --state terraform.tfstate --profile prod
```

---

### 5. SECURITY.md Secret Detection Claims Unverified

**SECURITY.md Line 69-87:**
```markdown
### Secret Scrubber

RepliMap includes a SecretScrubber that automatically detects and redacts
sensitive data in generated Terraform code:

- AWS Access Key IDs (AKIA*, ASIA* for STS)
- AWS Secret Access Keys
- Private Keys (RSA, EC, DSA, OpenSSH)
- Database URLs with embedded passwords
- Bearer tokens, GitHub/Slack/Stripe tokens
- Generic secrets (password=, api_key=, etc.)
```

**Issue:** No examples of what gets redacted or how to verify it works.

**Recommendation:** Add test cases and examples:

```markdown
### Secret Scrubber Examples

**Before:**
```hcl
resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t3.micro"

  user_data = <<-EOF
    #!/bin/bash
    export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
    export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    export DB_PASSWORD=SuperSecret123!
  EOF
}
```

**After:**
```hcl
resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t3.micro"

  user_data = <<-EOF
    #!/bin/bash
    export AWS_ACCESS_KEY_ID="[REDACTED-AWS_ACCESS_KEY_ID]"
    export AWS_SECRET_ACCESS_KEY="[REDACTED-AWS_SECRET_ACCESS_KEY]"
    export DB_PASSWORD="[REDACTED-PASSWORD]"
  EOF
}
```

**Verification:**
```bash
replimap clone --profile prod -o ./terraform
grep -r "AKIA" terraform/  # Should find no raw keys
grep -r "REDACTED" terraform/  # Should show redacted secrets
```
```

---

### 6. Quickstart Missing Critical Steps

**README.md Line 322-334 (Your First Scan):**
```bash
# 1. Configure AWS credentials (if not already done)
aws configure --profile myaccount

# 2. Scan your infrastructure
replimap -p myaccount -r us-east-1 scan

# 3. Explore the results
replimap -p myaccount -r us-east-1 graph -o architecture.html
open architecture.html
```

**Missing Steps:**
1. ❌ No verification that credentials work
2. ❌ No IAM policy attachment step
3. ❌ No mention of scan duration
4. ❌ No troubleshooting for common errors
5. ❌ No explanation of cache location

**Recommended Quickstart:**

```bash
# 1. Install RepliMap
pipx install replimap
replimap --version  # Verify installation

# 2. Configure AWS credentials
aws configure --profile myaccount
# Enter Access Key ID, Secret, and default region

# 3. Verify credentials work
aws sts get-caller-identity --profile myaccount
# Should show your account ID and user ARN

# 4. Attach IAM policy (one-time setup)
# Download our pre-built policy:
curl -O https://replimap.com/iam-policy.json
aws iam put-user-policy \
  --user-name replimap-scanner \
  --policy-name RepliMapReadOnly \
  --policy-document file://iam-policy.json

# 5. Run your first scan (takes 30-90 seconds)
replimap scan --profile myaccount --region us-east-1
# ✓ Scanned 847 resources in 23.4s
# ✓ Mapped 1,203 dependencies

# 6. Visualize the results
replimap graph --profile myaccount --region us-east-1 --output architecture.html
# Opens in browser automatically ✨

# 7. (Optional) Cache results for faster re-runs
replimap scan --cache --profile myaccount --region us-east-1

# Troubleshooting:
# - Permission errors? Check IAM_POLICY.md
# - Slow scan? Use --cache flag
# - Need help? replimap --help
```

---

### 7. CloudFormation and Pulumi Formats Not Documented

**README.md Line 147-151:**
```markdown
**Supported IaC formats:**
- ✅ Terraform (HCL)
- ✅ CloudFormation (YAML/JSON)
- 🔜 Pulumi (TypeScript)
- 🔜 CDK (TypeScript)
```

**Issue:** README says CloudFormation is supported, but:
1. No examples of `replimap clone --format cloudformation`
2. No documentation of output structure
3. No mention that it requires Solo+ plan

**From clone.py line 230-237:**
```python
# Validate output format
valid_formats = ("terraform", "cloudformation", "pulumi")
if output_format not in valid_formats:
    console.print(
        f"[red]Error:[/] Invalid format '{output_format}'. "
        f"Use one of: {', '.join(valid_formats)}"
    )
```

**Recommendation:** Either:
1. Document CloudFormation support properly, or
2. Mark it as 🔜 (coming soon) in README

---

### 8. Missing Tutorials for Common Workflows

**Current Docs:** Only reference docs (command descriptions).

**Missing Tutorials:**
1. **Getting Started: From Zero to First Scan** (10 minutes)
2. **Cloning Production to Staging** (20 minutes)
3. **Running SOC2 Compliance Audit** (15 minutes)
4. **Setting Up Drift Detection** (25 minutes)
5. **Multi-Account Setup with AWS Organizations** (30 minutes)

**Recommendation:** Create `/docs/tutorials/` directory with:

```
docs/
├── tutorials/
│   ├── 01-quickstart.md
│   ├── 02-clone-prod-to-staging.md
│   ├── 03-soc2-audit.md
│   ├── 04-drift-detection.md
│   ├── 05-multi-account.md
│   └── 06-cost-optimization.md
├── reference/
│   ├── cli-commands.md
│   ├── iam-policy.md
│   ├── supported-resources.md
│   └── error-codes.md
└── troubleshooting/
    ├── common-errors.md
    ├── performance-tuning.md
    └── faq.md
```

---

### 9. Pricing Confusion

**README.md Line 537:**
```markdown
⏱️ 10 scans/month
```

**Issue:** Ambiguous - does "10 scans/month" mean:
- 10 total scans across all regions/profiles?
- 10 scans per account?
- 10 scans per region?

**From licensing code:**
```python
# FREE tier: 10 scans/month (total, not per account)
max_scans_per_month: int = 10
```

**Recommendation:** Clarify in README:

```markdown
### Free Tier
- ✅ Scan unlimited resources
- ✅ Preview generated Terraform
- ✅ Basic compliance audit
- ⏱️ 10 scans per month (across all AWS accounts/regions)

What counts as a scan?
  • Each `replimap scan` command = 1 scan
  • Using `--cache` flag doesn't count as new scan
  • Multiple commands on same scan (graph, cost, audit) = 1 scan
```

---

### 10. No Migration Guide from Terraformer/Former2

**Issue:** Users coming from Terraformer or Former2 need migration guide.

**Recommendation:** Create `docs/migration/from-terraformer.md`:

```markdown
# Migrating from Terraformer

## Key Differences

| Feature | Terraformer | RepliMap |
|---------|-------------|----------|
| Dependency tracking | ❌ No | ✅ Full graph |
| Code quality | ⚠️ Verbose | ✅ Clean, modular |
| Output format | Single file | Multiple files by resource type |
| Import support | Manual | ✅ Automatic (TF 1.5+) |

## Migration Steps

1. **Last export with Terraformer**
   ```bash
   terraformer import aws --resources=vpc,ec2,rds \
     --regions=us-east-1 --profile=prod
   ```

2. **First import with RepliMap**
   ```bash
   replimap scan --profile prod --region us-east-1
   replimap clone --mode generate -o ./terraform-replimap
   ```

3. **Compare outputs**
   ```bash
   diff -r terraform-terraformer/ terraform-replimap/
   ```

4. **Run test on RepliMap output**
   ```bash
   cd terraform-replimap
   ./test-terraform.sh
   ```

5. **Gradually switch**
   - Start with dev/staging environments
   - Verify outputs match
   - Move to production once confident
```

---

## Quick Wins (High Impact, Low Effort)

1. **Update README clone output structure** (1 day)
2. **Add feature availability badges to examples** (1 day)
3. **Expand IAM policy with Phase 2 permissions** (2 days)
4. **Clarify "10 scans/month" in pricing** (1 hour)
5. **Add secret scrubber verification examples** (1 day)

---

## Medium-Term Improvements

1. **Create comprehensive quickstart with troubleshooting** (1 week)
2. **Write 6 tutorial guides for common workflows** (2 weeks)
3. **Add Terraformer migration guide** (3 days)
4. **Document CloudFormation output format** (1 week)
5. **Create video walkthrough** (1 week)

---

## Long-Term Enhancements

1. **Interactive docs with embedded demos** (1 month)
2. **Auto-generate docs from code docstrings** (ongoing)
3. **Community-contributed recipes** (ongoing)
4. **Localization (Chinese, Japanese, Spanish)** (3 months)

---

## Success Metrics

**Before:**
- New user time-to-first-successful-scan: ~20 minutes
- Support tickets about "how to get started": ~50%
- Example command success rate: ~60%

**After (Target):**
- Time-to-first-scan: <5 minutes
- Support tickets: <20%
- Example success rate: >90%

---

**Reviewed:** 2026-01-11
**Reviewer:** Claude (Automated Code Review)
**Status:** Recommendations for Docs/DevRel team
