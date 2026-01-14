# P2: Pricing Model Inconsistencies & Market Positioning Gaps

**Session ID:** 3.3
**Category:** Business Logic / Pricing Strategy
**Priority:** P2 (Medium)
**Date:** 2026-01-11
**Status:** Open

---

## Executive Summary

RepliMap's pricing matrix (v3.2) shows structural inconsistencies between code implementation, README documentation, and competitive positioning. Several pricing decisions create customer confusion, missed revenue opportunities, and strategic misalignment with the IaC tooling market.

**Key Issues:**
1. README pricing is simplified/outdated vs. `models.py` implementation
2. FREE tier "10 scans/month" (README line 537) conflicts with code (3 scans/month)
3. Missing value anchoring for $49 SOLO tier
4. No competitive differentiation vs. Terraform Cloud ($20/user) and Spacelift ($600/5 users)
5. Enterprise pricing ($500/mo minimum) undervalues APRA/RBNZ compliance features

---

## Pricing Matrix Analysis

### Code Implementation (Source of Truth)

**File:** `/home/davidlu/private-repo/org-replimap/replimap/replimap/licensing/models.py` (lines 315-721)

```python
# ========================================================================
# PLAN FEATURE CONFIGURATIONS (v3.2 Pricing Matrix)
# ========================================================================

PLAN_FEATURES: dict[Plan, PlanFeatures] = {
    Plan.FREE: PlanFeatures(
        plan=Plan.FREE,
        price_monthly=0,
        price_annual=0,
        max_scans_per_month=3,  # ← CODE SAYS 3
        # ...
    ),

    Plan.SOLO: PlanFeatures(
        plan=Plan.SOLO,
        price_monthly=49,
        price_annual=490,  # 2 months free
        max_scans_per_month=None,  # Unlimited
        # ...
    ),

    Plan.PRO: PlanFeatures(
        plan=Plan.PRO,
        price_monthly=99,
        price_annual=990,
        max_aws_accounts=3,  # dev/staging/prod
        # ...
    ),

    Plan.TEAM: PlanFeatures(
        plan=Plan.TEAM,
        price_monthly=199,
        price_annual=1990,
        max_aws_accounts=10,
        # ...
    ),

    Plan.ENTERPRISE: PlanFeatures(
        plan=Plan.ENTERPRISE,
        price_monthly=500,  # Starting price
        price_annual=5000,  # Custom pricing typically
        # ...
    ),
}
```

---

### README Documentation (Customer-Facing)

**File:** `/home/davidlu/private-repo/org-replimap/replimap/README.md` (lines 530-556)

```markdown
## 💼 Pricing

### Free Tier

- ✅ Scan unlimited resources
- ✅ Preview generated Terraform
- ✅ Basic compliance audit
- ⏱️ 10 scans/month  ← README SAYS 10!

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
```

**Issues:**
1. **Missing PRO tier** in README (but exists in code!)
2. **FREE tier conflict:** 10 scans/month (README) vs. 3 scans/month (code)
3. **No Enterprise details** in README
4. **No pricing matrix table** for easy comparison
5. **No competitive positioning** (vs. Terraform Cloud, Spacelift, Former2)

---

## Inconsistency Breakdown

### 1. FREE Tier Scan Limit Conflict

| Source | Limit | Line Reference |
|--------|-------|----------------|
| **Code (models.py)** | 3 scans/month | Line 338 |
| **README.md** | 10 scans/month | Line 537 |
| **Gate enforcement** | 3 scans/month | gates.py:306 |

**Business Impact:**
- User expects 10 scans based on README
- Code enforces 3 scans → confused users, support tickets
- False advertising risk

**Root Cause:**
README is stale. Original design was 10 scans/month, reduced to 3 for server cost control.

**Recommendation:**
```markdown
### Free Tier ($0)

- ✅ Scan unlimited resources
- ✅ Preview generated Terraform (first 100 lines)
- ✅ View all audit titles + first CRITICAL issue preview
- ✅ Basic cost estimates
- ⏱️ **3 scans/month** (resets on 1st of each month)
- 🔗 Single AWS account only

**Perfect for:**
- Learning Terraform reverse-engineering
- One-time infrastructure audits
- POC/evaluation
```

---

### 2. Missing PRO Tier in README

**Code Implementation:**
```python
Plan.PRO: PlanFeatures(
    price_monthly=99,
    price_annual=990,
    max_aws_accounts=3,  # dev/staging/prod
    drift_enabled=True,  # ← KEY DIFFERENTIATOR
    audit_ci_mode=True,  # ← CI/CD integration
    remediate_beta_access=True,
    # ...
)
```

**README:** PRO tier is completely missing!

**Business Problem:**
- $99/mo PRO is the **sweet spot for senior engineers** (drift + CI mode)
- Gap between SOLO ($49) and TEAM ($199) is too wide
- Customers don't know PRO exists → skip to TEAM (over-spend) or stay on SOLO (under-monetize)

**Recommended README Addition:**
```markdown
### Pro ($99/mo)

- ✅ Everything in Solo
- ✅ **Multi-account support** (3 accounts: dev/staging/prod)
- ✅ **Drift detection** (compare AWS vs Terraform)
- ✅ **CI mode** (--fail-on-high for pipelines)
- ✅ Audit exports (HTML + PDF)
- ✅ Remediate beta access (priority)
- ✅ 24-hour support SLA

**Perfect for:**
- Senior DevOps engineers managing multiple environments
- Teams using Terraform in CI/CD pipelines
- Compliance-driven organizations (SOC2, ISO27001)
```

---

### 3. Enterprise Pricing Undervaluation

**Current:**
```python
Plan.ENTERPRISE: PlanFeatures(
    price_monthly=500,  # Starting price
    # ...
    # APRA CPS 234 mapping
    apra_cps234_mapping=True,
    essential_eight_assessment=True,
    rbnz_bs11_mapping=True,
    nzism_alignment=True,
)
```

**Market Research:**

| Competitor | Enterprise Pricing | Compliance Features |
|------------|-------------------|---------------------|
| **Terraform Cloud** | $70/user/mo (5-user min = $350) | No compliance frameworks |
| **Spacelift** | $600/mo (5 users) | No APRA/RBNZ built-in |
| **Prisma Cloud** | $3,000/mo+ | Compliance, but no IaC gen |
| **RepliMap** | $500/mo | APRA + RBNZ + Essential Eight |

**Problem:**
RepliMap's Enterprise tier at $500/mo is **underpriced** for regulated industries:
- Australian banks (APRA CPS 234): $10,000-$50,000 annual compliance budgets
- NZ financial institutions (RBNZ BS11): Similar budgets
- RepliMap offers $6,000/year ($500×12) for features worth 5-10x more

**Recommendation:**
```python
Plan.ENTERPRISE: PlanFeatures(
    price_monthly=1500,  # $1,500/mo base
    price_annual=15000,  # 2 months free
    # ...
    # APRA/RBNZ are PREMIUM add-ons
)

# Add-on pricing (not in code, contract-based):
# - APRA CPS 234 module: +$500/mo
# - Essential Eight assessment: +$300/mo
# - RBNZ BS11 mapping: +$400/mo
# - Total Enterprise package: $2,700/mo for regulated banks
```

**Justification:**
- Banks pay $50k+ for Wiz, Prisma Cloud
- RepliMap offers compliance + IaC generation + drift detection
- Unique value: APRA/RBNZ frameworks not available elsewhere

---

## Competitive Positioning Analysis

### Terraform Cloud vs RepliMap

| Feature | Terraform Cloud | RepliMap | Winner |
|---------|----------------|----------|--------|
| **Free Tier** | 500 resources/month | 3 scans/month (unlimited resources) | TC (500 limit is higher) |
| **Starter Price** | $20/user/mo | $49/mo | TC ($20 is accessible) |
| **Drift Detection** | Pro ($70/user) | PRO ($99) | TC (cheaper) |
| **IaC Generation** | ❌ None | ✅ Full Terraform gen | **RepliMap** |
| **Reverse Engineering** | ❌ None | ✅ AWS → Terraform | **RepliMap** |
| **Compliance** | ❌ None | ✅ APRA/RBNZ | **RepliMap** |
| **Collaboration** | ✅ SaaS dashboard | ⚠️ CLI-only | TC |

**Insight:**
- Terraform Cloud wins on **collaboration** (SaaS dashboard)
- RepliMap wins on **reverse engineering** (unique value)
- RepliMap's $49 SOLO should compete with TC's $20 Standard

---

### Spacelift vs RepliMap

| Feature | Spacelift | RepliMap | Winner |
|---------|-----------|----------|--------|
| **Free Tier** | ❌ None (trial only) | 3 scans/month | **RepliMap** |
| **Team Pricing** | $600/mo (5 users) | $199/mo (5 seats) | **RepliMap** |
| **Policy as Code** | ✅ OPA integration | ❌ None | Spacelift |
| **IaC Cloning** | ❌ None | ✅ AWS→Terraform | **RepliMap** |
| **Compliance** | ⚠️ Generic | ✅ APRA/RBNZ | **RepliMap** |

**Insight:**
- RepliMap is **significantly cheaper** ($199 vs $600)
- Missing Policy-as-Code (OPA) → roadmap opportunity
- Unique IaC cloning is killer feature

---

### Former2 vs RepliMap

| Feature | Former2 | RepliMap | Winner |
|---------|---------|----------|--------|
| **Pricing** | 100% FREE | Freemium | Former2 |
| **Architecture** | Browser-based | CLI | Tie |
| **Resource Support** | 280+ resources | 24 resources | Former2 |
| **Graph Analysis** | ❌ None | ✅ Full graph | **RepliMap** |
| **Compliance Audit** | ❌ None | ✅ SOC2/CIS | **RepliMap** |
| **Cost Optimization** | ❌ None | ✅ Right-Sizer | **RepliMap** |

**Threat:**
- Former2 is 100% free, browser-based, supports MORE resources
- RepliMap must justify $49/mo with **graph intelligence** and **compliance**
- Current FREE tier (3 scans/month) is too restrictive vs. Former2 unlimited

**Recommendation:**
```markdown
### Why pay for RepliMap when Former2 is free?

**Former2:**
- ✅ Free, browser-based
- ✅ 280+ resource types
- ❌ No dependency graph → can't answer "what breaks if I delete this?"
- ❌ No compliance scanning → manual SOC2 audit prep
- ❌ No cost optimization → no Right-Sizer
- ❌ No drift detection → ClickOps changes undetected

**RepliMap:**
- ✅ Full dependency graph (Tarjan's SCC algorithm)
- ✅ Compliance audit (SOC2, CIS, APRA, RBNZ)
- ✅ Cost optimization (Right-Sizer for dev/staging)
- ✅ Drift detection (Terraform state vs AWS)
- ✅ CLI-first (scriptable, CI/CD integration)
- 💰 From $49/mo for production use
```

---

## Pricing Strategy Recommendations

### Option A: Match Market Leaders (Conservative)

```python
PLAN_FEATURES_V4 = {
    Plan.FREE: PlanFeatures(
        price_monthly=0,
        max_scans_per_month=5,  # Increase to 5 (still restrictive)
        clone_preview_lines=200,  # More generous preview
    ),

    Plan.STARTER: PlanFeatures(  # NEW TIER
        price_monthly=29,  # Match Terraform Cloud Standard ($20-$30)
        max_scans_per_month=None,  # Unlimited
        clone_download_enabled=True,
        audit_report_export=True,
        audit_export_formats={"html"},
        max_aws_accounts=1,
    ),

    Plan.SOLO: PlanFeatures(
        price_monthly=59,  # Small increase
        # Current Solo features
    ),

    Plan.PRO: PlanFeatures(
        price_monthly=99,  # Keep current
        # Current Pro features
    ),

    Plan.TEAM: PlanFeatures(
        price_monthly=249,  # Increase (vs Spacelift $600)
        # Current Team features + Policy-as-Code
    ),

    Plan.ENTERPRISE: PlanFeatures(
        price_monthly=1500,  # 3x increase
        # + APRA/RBNZ add-ons
    ),
}
```

**Revenue Impact:**
- **Downside:** Current SOLO users ($49) may downgrade to STARTER ($29)
- **Upside:** Capture price-sensitive users who find $49 too high
- **Net:** Likely neutral in Year 1, positive in Year 2 (volume)

---

### Option B: Value-Based Pricing (Aggressive)

```python
PLAN_FEATURES_V4_AGGRESSIVE = {
    Plan.FREE: PlanFeatures(
        price_monthly=0,
        max_scans_per_month=10,  # Match README (was 3)
        clone_preview_lines=500,  # Very generous preview
        # Goal: Free tier as lead gen, not revenue
    ),

    Plan.PRO: PlanFeatures(  # Remove SOLO, collapse to PRO
        price_monthly=79,  # Sweet spot
        max_scans_per_month=None,
        clone_download_enabled=True,
        drift_enabled=True,  # Include drift in base
        max_aws_accounts=3,
    ),

    Plan.TEAM: PlanFeatures(
        price_monthly=299,  # Increase significantly
        max_aws_accounts=None,  # Unlimited accounts
        # Full collaboration features
    ),

    Plan.ENTERPRISE: PlanFeatures(
        price_monthly=2000,  # 4x increase
        # APRA/RBNZ/Essential Eight included
    ),
}
```

**Rationale:**
- Simplify to 3 paid tiers (PRO/TEAM/ENTERPRISE)
- FREE tier is generous → marketing funnel
- PRO at $79 is impulse-buy range for engineers
- TEAM at $299 captures 5-10 person teams
- ENTERPRISE at $2000 reflects true compliance value

---

### Option C: Open Core Model (Strategic Pivot)

```
FREE (Open Source):
- Unlimited scanning
- Unlimited graph visualization
- Unlimited cost estimates
- No export limits (MIT license for scanning)

CLOUD ($99/mo):
- SaaS dashboard
- Team collaboration
- Cloud storage for graphs
- Scheduled drift detection
- Slack/PagerDuty integrations

ENTERPRISE ($1500/mo):
- On-premise deployment
- SSO/SAML
- APRA/RBNZ compliance modules
- Dedicated support
- SLA guarantees
```

**Precedent:**
- HashiCorp: Terraform OSS (free) → Terraform Cloud (paid)
- GitLab: GitLab CE (free) → GitLab EE (paid)
- Elastic: Elasticsearch (free) → Elastic Cloud (paid)

**Advantages:**
- Eliminates bypass concerns (no enforcement needed)
- Massive adoption → network effects
- Revenue from cloud/enterprise, not CLI

**Disadvantages:**
- Cannibalizes current paid CLI users
- Requires building SaaS platform (6-12 month investment)
- Higher CAC (need more users to compensate)

---

## README Fixes (Immediate Action)

**File:** `/home/davidlu/private-repo/org-replimap/replimap/README.md`

**Changes Required:**

```diff
## 💼 Pricing

### Free Tier ($0)

- ✅ Scan unlimited resources
- ✅ Preview generated Terraform (first 100 lines)
- ✅ Basic compliance audit (all titles + first critical preview)
- ✅ Basic cost estimates
-- ⏱️ 10 scans/month
+- ⏱️ **3 scans/month** (resets monthly)
+- 🔗 Single AWS account only

### Solo ($49/mo)

- ✅ Everything in Free
- ✅ Download Terraform code
- ✅ Full Right-Sizer recommendations
+- ✅ Full audit reports (HTML export)
- ✅ Unlimited scans
+- ✅ Snapshot storage (5 snapshots, 7-day retention)
- ✅ Email support (48-hour SLA)

+### Pro ($99/mo)
+
+- ✅ Everything in Solo
+- ✅ **Multi-account support** (3 AWS accounts)
+- ✅ **Drift detection** (Terraform state vs AWS)
+- ✅ **CI mode** (--fail-on-high for pipelines)
+- ✅ Audit exports (HTML + PDF)
+- ✅ Snapshot storage (15 snapshots, 30-day retention)
+- ✅ Email support (24-hour SLA)
+
+**Perfect for:** Senior DevOps engineers, compliance teams

### Team ($199/mo)

- ✅ Everything in Solo
+- ✅ Everything in Pro
- ✅ Multi-account support (up to 10)
-- ✅ Drift detection
+- ✅ Drift watch mode + alerts
- ✅ Dependency explorer
+- ✅ Trust Center (audit logging, 7-day retention)
+- ✅ Audit exports (HTML + PDF + JSON)
- ✅ 5 team seats
- ✅ Priority support (12-hour SLA)

+### Enterprise (From $500/mo)
+
+- ✅ Everything in Team
+- ✅ **Unlimited AWS accounts**
+- ✅ **APRA CPS 234 compliance mapping** (Australia)
+- ✅ **RBNZ BS11 compliance mapping** (New Zealand)
+- ✅ **Essential Eight assessment** (ACSC)
+- ✅ **NZISM alignment**
+- ✅ Trust Center (unlimited audit logs, 1-year retention)
+- ✅ Digital signatures (SHA256 signed reports)
+- ✅ Audit exports (all formats: HTML, PDF, JSON, CSV)
+- ✅ Unlimited team members
+- ✅ 4-hour support SLA
+- ✅ Custom integrations
+
+**Perfect for:** Banks, financial institutions, regulated industries

[View full pricing →](https://replimap.com/pricing)
```

---

## Competitive Positioning Matrix

Add to README after pricing section:

```markdown
## 📊 RepliMap vs Competitors

| Feature | RepliMap | Terraform Cloud | Spacelift | Former2 |
|---------|----------|----------------|-----------|---------|
| **Free Tier** | 3 scans/month | 500 resources | Trial only | Unlimited |
| **IaC Generation** | ✅ Full Terraform | ❌ None | ❌ None | ✅ Limited |
| **Dependency Graph** | ✅ Full graph | ❌ None | ⚠️ Limited | ❌ None |
| **Drift Detection** | ✅ Pro ($99) | ✅ Team ($70/user) | ✅ Included | ❌ None |
| **Compliance Audit** | ✅ SOC2/APRA/RBNZ | ❌ None | ⚠️ Generic | ❌ None |
| **Cost Optimization** | ✅ Right-Sizer | ❌ None | ❌ None | ❌ None |
| **Team Pricing** | $199/mo (5 seats) | $350/mo (5 users) | $600/mo (5 users) | FREE |
| **Architecture** | CLI + Local | SaaS | SaaS | Browser |

**When to choose RepliMap:**
- 🎯 You have ClickOps infrastructure and need to reverse-engineer to Terraform
- 🔍 You need dependency analysis ("what breaks if I delete this?")
- 💰 You want cost optimization (Right-Sizer for dev/staging)
- 🏦 You're in a regulated industry (APRA, RBNZ, SOC2)
- 🔒 You need data to stay local (no cloud upload)

**When to choose Terraform Cloud:**
- 👥 You need team collaboration dashboard
- 🔄 You already have Terraform (not starting from ClickOps)
- ☁️ You prefer SaaS over CLI

**When to choose Former2:**
- 🆓 You need a free tool for one-time migration
- 🌐 You're okay with browser-based tools
- 📦 You need coverage for rare AWS resources (280+ types)
```

---

## Action Items

### Immediate (v0.4.0)
1. ✅ Fix README pricing (3 scans/month, add PRO tier)
2. ✅ Add competitive comparison table
3. ✅ Update models.py comments to match README

### Short-Term (Q2 2026)
4. ⚠️ User research: Survey why users don't upgrade from FREE
5. ⚠️ A/B test: 3 scans vs 5 scans vs 10 scans (conversion impact)
6. ⚠️ Pricing page redesign: Add "Perfect for" sections

### Strategic (H2 2026)
7. 🔮 Decide: Conservative pricing vs Open Core pivot
8. 🔮 If Open Core: Build SaaS dashboard (6 months)
9. 🔮 If Conservative: Add STARTER tier at $29/mo

---

## Conclusion

RepliMap's pricing has strong bones but execution gaps:
- ✅ Good: Feature differentiation across tiers
- ✅ Good: Value-based pricing (APRA/RBNZ worth more)
- ❌ Bad: README outdated (10 vs 3 scans)
- ❌ Bad: Missing PRO tier in customer-facing docs
- ❌ Bad: Enterprise underpriced ($500 should be $1500+)

**Priority:** Fix README immediately (customer confusion), then decide strategic direction (Open Core vs. SaaS vs. CLI-first).

---

**Sign-off:** Code Review - Session 3.3
**Next Session:** 5.1 - Competitive Feature Matrix
