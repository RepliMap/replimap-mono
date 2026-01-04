<!--
<p align="center">
  <img src="docs/assets/logo.png" alt="RepliMap Logo" width="120" />
</p>
-->

<h1 align="center">RepliMap</h1>

<p align="center">
  <strong>AWS Infrastructure Intelligence Engine</strong>
</p>

<p align="center">
  Reverse-engineer any AWS account. Visualize dependencies. Generate Terraform. Optimize costs.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#use-cases">Use Cases</a> •
  <a href="#installation">Installation</a> •
  <a href="#documentation">Docs</a>
</p>

<p align="center">
  <a href="https://pypi.org/project/replimap/">
    <img src="https://img.shields.io/pypi/v/replimap?color=blue&label=PyPI" alt="PyPI" />
  </a>
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+" />
  <a href="https://github.com/RepliMap/replimap/actions/workflows/auto-release.yml">
    <img src="https://github.com/RepliMap/replimap/actions/workflows/auto-release.yml/badge.svg?branch=main" alt="Build" />
  </a>
  <a href="https://github.com/RepliMap/replimap/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-BSL--1.1-green.svg" alt="License" />
  </a>
</p>

<p align="center">
  <img src="docs/assets/demo.gif" alt="RepliMap Demo" width="700" />
</p>

---

## The Problem

You inherited an AWS account. Or maybe you built it yourself over 3 years of "just one more click."

Now you have:
- 🤷 **500+ resources** and no idea what connects to what
- 😰 **No Terraform** — everything was ClickOps
- 💸 **Oversized instances** burning money 24/7
- 📋 **SOC2 audit next month** — good luck

Sound familiar?

## The Solution

**RepliMap scans your AWS, builds a dependency graph, and gives you superpowers.**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   $ replimap -p prod scan                                               │
│                                                                         │
│   ✓ Scanned 847 resources in 23.4s                                      │
│   ✓ Mapped 1,203 dependencies                                           │
│   ✓ Found 12 compliance issues                                          │
│   ✓ Identified $2,847/month in savings                                  │
│                                                                         │
│   Your infrastructure graph is ready.                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Features

### 🔍 Scan & Understand

**See your infrastructure like never before.**

RepliMap builds a complete dependency graph of your AWS account using a sophisticated graph engine. Finally understand what connects to what — and what breaks if you touch it.

```bash
# Scan your AWS account
replimap -p prod -r ap-southeast-2 scan

# Visualize dependencies
replimap -p prod -r us-east-1 graph -o architecture.html

# "What happens if I delete this security group?"
replimap -p prod -r us-east-1 deps sg-0a1b2c3d4e
```

<details>
<summary>📸 See example dependency graph</summary>

```
                    ┌─────────────┐
                    │   ALB       │
                    │ (public)    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌────▼────┐ ┌─────▼─────┐
        │  EC2 #1   │ │  EC2 #2 │ │  EC2 #3   │
        │ (web)     │ │  (web)  │ │  (web)    │
        └─────┬─────┘ └────┬────┘ └─────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │     RDS     │
                    │  (primary)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ ElastiCache │
                    │  (redis)    │
                    └─────────────┘
```

</details>

### 🏗️ Generate Infrastructure as Code

**From ClickOps to Terraform in minutes, not months.**

Turn any AWS account into version-controlled Terraform. No manual `terraform import`. No guesswork. Generates 90% of the HCL boilerplate so you can focus on the logic.

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

**Supported IaC formats:**
- ✅ Terraform (HCL)
- ✅ CloudFormation (YAML/JSON)
- 🔜 Pulumi (TypeScript)
- 🔜 CDK (TypeScript)

### 💰 Optimize Costs

**Stop paying production prices for dev environments.**

RepliMap's Right-Sizer analyzes your resources and recommends optimizations. Clone production to staging with automatic downsizing — save 40-60% on non-prod environments.

```bash
# Clone prod to staging with cost optimization
replimap -p prod -r us-east-1 clone --dev-mode --mode generate -o ./staging

# See what you'll save
replimap -p prod -r us-east-1 cost
```

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        💰 Right-Sizer Report                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Resource              Current        Recommended      Monthly Savings  │
│  ─────────────────────────────────────────────────────────────────────  │
│  web-server-1          m5.2xlarge     t3.large         $198.56         │
│  web-server-2          m5.2xlarge     t3.large         $198.56         │
│  api-server            m5.xlarge      t3.medium        $124.10         │
│  analytics-db          db.r5.2xlarge  db.r5.large      $365.00         │
│  cache-cluster         r6g.xlarge     r6g.large        $131.40         │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│  TOTAL MONTHLY SAVINGS                                 $1,017.62        │
│  ANNUAL SAVINGS                                        $12,211.44       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### ✅ Audit Compliance

**Find compliance gaps before your auditor does.**

Built-in security and compliance scanning powered by industry-standard rules. Get actionable findings with auto-generated remediation code.

```bash
# Run compliance audit
replimap -p prod -r us-east-1 audit

# Generate fix code (from audit JSON output)
replimap -p prod -r us-east-1 audit --format json -o audit_report.json
replimap remediate audit_report.json -o ./fixes
```

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        🔒 Compliance Report                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Framework: SOC2 Type II                                                │
│  Resources Scanned: 847                                                 │
│  Findings: 12                                                           │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 🔴 CRITICAL (2)                                                    │ │
│  │    • S3 bucket 'logs-prod' has public access enabled               │ │
│  │    • RDS instance 'main-db' not encrypted at rest                  │ │
│  │                                                                    │ │
│  │ 🟡 HIGH (4)                                                        │ │
│  │    • Security group sg-xxx allows 0.0.0.0/0 on port 22            │ │
│  │    • IAM user 'deploy-bot' has inline policies                     │ │
│  │    • CloudTrail not enabled in ap-southeast-2                      │ │
│  │    • EBS volumes not encrypted by default                          │ │
│  │                                                                    │ │
│  │ 🟢 MEDIUM (6)                                                      │ │
│  │    • [View full report: ./audit-report.html]                       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 🔄 Detect Drift

**Know when reality diverges from your Terraform.**

Compare your actual AWS state against your Terraform code. Catch ClickOps changes before they cause incidents.

```bash
# Detect drift from local state file
replimap -p prod -r us-east-1 drift --state ./terraform.tfstate

# Detect drift from remote S3 state
replimap -p prod -r us-east-1 drift --state-bucket my-tf-state --state-key prod/terraform.tfstate

# Output
Drift detected in 3 resources:
  • aws_security_group.web: ingress rule added (port 8080)
  • aws_instance.api: instance_type changed (t3.large → t3.xlarge)
  • aws_s3_bucket.logs: versioning disabled
```

---

## Use Cases

### 🚀 Startup Scale-Up

> "We built everything in the console. Now we need Terraform."

Stop the painful manual migration. RepliMap reverse-engineers your entire infrastructure and generates production-ready IaC. From ClickOps to GitOps in an afternoon, not a quarter.

### 🧪 Test & Staging Environments

> "I need a copy of prod for testing. By tomorrow."

Spin up production-identical environments in minutes, not days:

- **Legacy Project Handoff** — Inherited a mess? Scan it, clone it, understand it.
- **Ephemeral Test Environments** — Replicate prod, run tests, destroy. Rinse and repeat.
- **Chaos Engineering** — Clone prod for Chaos Monkey experiments without risking the real thing.
- **DR Drills** — Quarterly disaster recovery exercises? One command to duplicate your entire stack.

```bash
# Clone prod to staging with cost-optimized instances
replimap -p prod -r us-east-1 clone --dev-mode --mode generate -o ./staging

# Test complete? Destroy with confidence
cd staging && terraform destroy
```

### 💸 FinOps & Cost Optimization

> "We're spending $50k/month but don't know where it goes."

RepliMap maps every resource, identifies waste, and shows exactly where to cut. Right-size instances, find unused resources, optimize reserved capacity. See savings before you commit.

### 🔒 SOC2 / ISO27001 Preparation

> "Audit is in 30 days. We have no documentation."

RepliMap generates architecture diagrams, compliance reports, and remediation code. Turn audit prep from months to days. Auditors love the dependency graphs.

### 🏢 M&A Due Diligence

> "We're acquiring a company. What does their AWS look like?"

RepliMap gives you complete visibility into any AWS account in minutes. Understand architecture quality, compliance posture, and cost structure — before signing the term sheet.

### 🌍 Disaster Recovery

> "We need to replicate prod to another region. Yesterday."

Clone your entire infrastructure to a DR region with one command. All dependencies mapped, all configurations preserved. Test your DR plan without the drama.

---

## Quick Start

### Installation

```bash
# Using pipx (recommended - isolated environment)
pipx install replimap

# Using pip
pip install replimap

# From source (latest development version)
pip install git+https://github.com/RepliMap/replimap.git

# Verify installation
replimap --version
```

### Your First Scan

```bash
# 1. Configure AWS credentials (if not already done)
aws configure --profile myaccount

# 2. Scan your infrastructure
replimap -p myaccount -r us-east-1 scan

# 3. Explore the results
replimap -p myaccount -r us-east-1 graph -o architecture.html
open architecture.html
```

### Generate Terraform

```bash
# Generate Terraform from scanned infrastructure
replimap -p myaccount -r us-east-1 clone --mode generate -o ./terraform

# Review and apply
cd terraform
terraform init
terraform plan
```

---

## 📖 Commands

| Command | Description |
|---------|-------------|
| `replimap scan` | Scan AWS resources and build dependency graph |
| `replimap clone` | Clone AWS environment to Infrastructure-as-Code |
| `replimap graph` | Generate visual dependency graph |
| `replimap deps` | Explore dependencies for a resource |
| `replimap cost` | Estimate monthly AWS costs |
| `replimap audit` | Run security audit on AWS infrastructure |
| `replimap drift` | Detect infrastructure drift between Terraform state and AWS |
| `replimap remediate` | Generate Terraform remediation code from audit JSON |

<details>
<summary>View all commands</summary>

```bash
replimap --help

Usage: replimap [OPTIONS] COMMAND [ARGS]...

AWS Infrastructure Intelligence Engine
Scan, understand, and transform your cloud.

Global Options:
  -p, --profile TEXT    AWS profile name (inherited by subcommands)
  -r, --region TEXT     AWS region (inherited by subcommands)
  -q, --quiet           Suppress verbose output
  -V, --version         Show version and exit
  -h, --help            Show help and exit

Commands:
  scan        Scan AWS resources and build dependency graph
  clone       Clone AWS environment to Infrastructure-as-Code
  graph       Generate visual dependency graph of AWS infrastructure
  deps        Explore dependencies for a resource
  cost        Estimate monthly AWS costs for your infrastructure
  audit       Run security audit on AWS infrastructure
  drift       Detect infrastructure drift between Terraform state and AWS
  remediate   Generate Terraform remediation code from audit JSON
  snapshot    Infrastructure snapshots for change tracking
  dr          Disaster Recovery readiness assessment
  unused      Detect unused and underutilized resources
  trends      Analyze AWS cost trends and detect anomalies
  license     Manage RepliMap license
```

</details>

---

## 🔧 Configuration

### AWS Credentials

RepliMap uses standard AWS credential chain:

```bash
# Option 1: AWS CLI profile (recommended)
replimap -p my-profile scan

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
replimap scan

# Option 3: IAM role (EC2/ECS/Lambda)
replimap scan  # Auto-detects instance role
```

### Required IAM Permissions

RepliMap only needs **read-only** access. See [IAM_POLICY.md](IAM_POLICY.md) for the minimal policy.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "rds:Describe*",
        "elasticache:Describe*",
        "s3:GetBucket*",
        "s3:ListBucket*",
        "lambda:List*",
        "lambda:GetFunction*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🏗️ Architecture

RepliMap is built around a **Graph Engine** powered by NetworkX. This isn't just a CLI wrapper around AWS APIs — it's an infrastructure intelligence platform.

The **Graph Engine** is the secret sauce: it transforms discrete cloud resources into a connected dependency graph, enabling impact analysis, visualization, and intelligent code generation that understands relationships.

```
┌──────────────────────────────────────────────────────────────────┐
│                         RepliMap Architecture                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│   │  Scanners   │────▶│ ⭐ Graph    │────▶│  Renderers  │       │
│   │  (AWS API)  │     │   Engine ⭐ │     │  (Terraform)│       │
│   └─────────────┘     └──────┬──────┘     └─────────────┘       │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│   ┌───────────┐      ┌─────────────┐      ┌───────────┐        │
│   │   Audit   │      │ Right-Sizer │      │   Drift   │        │
│   │  Engine   │      │   Engine    │      │  Detector │        │
│   └───────────┘      └─────────────┘      └───────────┘        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Description |
|-----------|-------------|
| **Graph Engine** | NetworkX-based dependency graph with Tarjan's SCC for cycle detection |
| **Scanners** | Async AWS API clients for 20+ resource types |
| **Renderers** | Jinja2 templates for Terraform/CloudFormation generation |
| **Right-Sizer** | Rule-based + API cost optimization engine |
| **Audit Engine** | Compliance scanning with Checkov integration |

### Supported Resources

<details>
<summary>View all 24 supported resource types</summary>

| Category | Resources |
|----------|-----------|
| **Compute** | EC2, Lambda, ECS, EKS |
| **Database** | RDS, Aurora, DynamoDB, ElastiCache |
| **Network** | VPC, Subnet, Security Group, Route Table, NAT Gateway, Internet Gateway, ALB/NLB |
| **Storage** | S3, EBS, EFS |
| **Security** | IAM Role, IAM Policy, KMS Key, Secrets Manager |
| **Other** | CloudWatch, SNS, SQS |

</details>

---

## 📊 Comparison

### RepliMap vs Terraformer

| Feature | RepliMap | Terraformer |
|---------|----------|-------------|
| Dependency Graph | ✅ Full graph with cycle detection | ❌ No dependency tracking |
| Code Quality | ✅ Clean, modular, variables extracted | ⚠️ Verbose, hardcoded values |
| Cost Optimization | ✅ Built-in Right-Sizer | ❌ None |
| Compliance Audit | ✅ SOC2/CIS built-in | ❌ None |
| Drift Detection | ✅ Yes | ❌ No |
| Visualization | ✅ Interactive HTML graphs | ❌ None |
| Active Development | ✅ Yes | ⚠️ Slow |

### RepliMap vs Former2

| Feature | RepliMap | Former2 |
|---------|----------|---------|
| Architecture | CLI (local) | Browser-based |
| Large Environments | ✅ Handles 1000+ resources | ⚠️ Browser memory limits |
| Dependency Analysis | ✅ Full graph | ⚠️ Limited |
| Cost Analysis | ✅ Yes | ❌ No |
| Data Privacy | ✅ Data stays local | ⚠️ Runs in browser |

---

## 💼 Pricing

### Free Tier

- ✅ Scan unlimited resources
- ✅ Preview generated Terraform
- ✅ Basic compliance audit
- ⏱️ 10 scans/month

### Solo ($49/mo)

- ✅ Everything in Free
- ✅ Download Terraform code
- ✅ Full Right-Sizer recommendations
- ✅ Unlimited scans
- ✅ Email support

### Team ($199/mo)

- ✅ Everything in Solo
- ✅ Multi-account support (up to 10)
- ✅ Drift detection
- ✅ Dependency explorer
- ✅ 5 team seats
- ✅ Priority support

[View full pricing →](https://replimap.com/pricing)

---

## 🔒 Security & Privacy

**Your data never leaves your machine.**

- ✅ RepliMap runs entirely client-side
- ✅ No cloud account required
- ✅ Read-only AWS access (no modifications)
- ✅ Sensitive data (passwords, keys) automatically redacted
- ✅ SOC2-compliant design

See [SECURITY.md](SECURITY.md) for details.

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Clone the repo
git clone git@github.com:RepliMap/replimap.git

# Install dev dependencies
cd replimap
pip install -e ".[dev]"

# Run tests
pytest
```

---

## 💬 Ready to See Your Infrastructure Clearly?

```bash
pip install replimap && replimap -r us-east-1 scan
```

Run your first scan in 2 minutes. See what you've been missing.

<p align="center">
  <a href="https://replimap.com/pricing"><strong>Get Pro License →</strong></a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="https://cal.com/replimap/demo"><strong>Book a Demo →</strong></a>
</p>

---

## Documentation

- [Installation Guide](docs/installation.md)
- [Quick Start Tutorial](docs/quickstart.md)
- [CLI Reference](docs/cli-reference.md)
- [IAM Policy](IAM_POLICY.md)
- [FAQ](docs/faq.md)

---

## Support & Contact

| Purpose | Contact |
|---------|---------|
| General inquiries | [hello@replimap.com](mailto:hello@replimap.com) |
| Technical support | [support@replimap.com](mailto:support@replimap.com) |
| Enterprise & Sales | [david@replimap.com](mailto:david@replimap.com) |
| Bug reports | [GitHub Issues](https://github.com/RepliMap/replimap/issues) |
| Discussions | [GitHub Discussions](https://github.com/RepliMap/replimap/discussions) |

## Links

- Website: [replimap.com](https://replimap.com)
- Documentation: [replimap.com/docs](https://replimap.com/docs)
- Pricing: [replimap.com/pricing](https://replimap.com/pricing)

---

## 📄 License

RepliMap is licensed under the [Business Source License 1.1](LICENSE.md).

**Free Tier (No license required):**
- ✅ Scan unlimited resources
- ✅ Visualize infrastructure (`graph`)
- ✅ Preview Terraform output (`--mode dry-run`)
- ✅ Basic cost estimates (console)
- ✅ Audit summary

**Paid Plans unlock:**
- 📥 Download generated Terraform/CloudFormation code
- 💰 Right-Sizer cost optimization
- 🔄 Drift detection between Terraform state and AWS
- 📊 Full audit reports with remediation code
- 🔍 Impact analysis (`deps`) — "What breaks if I delete this?"
- 💵 Cost reports export (HTML/CSV/JSON)

[View full pricing →](https://replimap.com/pricing)

---

## 📈 Star History

<a href="https://star-history.com/#RepliMap/replimap&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=RepliMap/replimap&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=RepliMap/replimap&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=RepliMap/replimap&type=Date" />
 </picture>
</a>

---

<p align="center">
  <strong>From chaos to clarity. From ClickOps to GitOps.</strong>
</p>

<p align="center">
  <a href="https://replimap.com">Website</a> •
  <a href="https://docs.replimap.com">Docs</a> •
  <a href="https://twitter.com/replimap">Twitter</a>
</p>

<p align="center">
  Made with ☕ in New Zealand
</p>
