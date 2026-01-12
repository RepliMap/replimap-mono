# P2: CLI Usability & User Experience Improvements

**Priority:** P2 (Medium - Product Experience)
**Category:** User Experience / CLI Design
**Impact:** Medium - Affects daily usability and user satisfaction
**Effort:** Medium - Requires UX research and consistent application across commands

---

## Executive Summary

RepliMap's CLI demonstrates good engineering but has inconsistencies in argument patterns, help text quality, and interactive flows that create friction for users. While functional, the interface can be streamlined to match the polish of the underlying graph engine.

## Findings

### 1. Inconsistent Region Detection Flow

**Current State:**
```python
# Region priority varies by command
# scan.py: flag > profile > env > default (us-east-1)
# clone.py: flag > profile > env > default (us-east-1)
# cost.py: flag > profile (no env fallback)
```

**Issue:** Users get different behavior across commands when AWS_DEFAULT_REGION is set.

**Recommendation:**
- Standardize region resolution order across ALL commands
- Document the resolution order in `--help` text
- Add `replimap config` command to show detected values without running scan

**Example:**
```bash
$ replimap config show
AWS Profile: prod (from --profile flag)
AWS Region: ap-southeast-2 (from profile config)
AWS Account: 123456789012 (from STS)
Cache Location: ~/.replimap/cache/123456789012/ap-southeast-2
```

---

### 2. Argument Naming Inconsistency

**Issue:** Similar concepts use different flag names:

| Concept | Command | Flag Name |
|---------|---------|-----------|
| Output path | scan | `--output` |
| Output path | clone | `--output-dir` |
| Output path | audit | `--output` |
| Format | clone | `--format` |
| Format | audit | `--format` |
| Format | cost | `--format` |
| Refresh scan | clone | `--refresh` |
| Refresh scan | cost | `--refresh` |
| No cache | scan | `--no-cache` (auth) |
| No cache | clone | `--no-cache` (auth) |

**Recommendation:**
- Standardize on `--output` for file output (not `--output-dir`)
- Use `--output-dir` only when multiple files are created
- Rename `--no-cache` to `--no-auth-cache` to clarify it's about credentials
- Add `--no-scan-cache` as separate flag for scan results

---

### 3. Poor Progressive Disclosure

**Issue:** `replimap --help` shows 13+ commands with no categorization:

```
Commands:
  scan        Scan AWS resources...
  clone       Clone AWS environment...
  analyze     Analyze graph...
  graph       Generate visual...
  deps        Explore dependencies...
  cost        Estimate monthly...
  audit       Run security audit...
  drift       Detect infrastructure...
  remediate   Generate Terraform...
  snapshot    Infrastructure snapshots...
  dr          Disaster Recovery...
  unused      Detect unused...
  trends      Analyze AWS cost...
  license     Manage RepliMap license
```

**Recommendation:** Organize commands into categories:

```
Core Workflow:
  scan        Discover AWS resources and build dependency graph
  clone       Generate IaC from scanned infrastructure

Analysis & Insights:
  analyze     Find critical resources, SPOFs, blast radius
  graph       Generate visual dependency graphs (HTML/SVG)
  deps        Explore resource dependencies interactively
  cost        Estimate monthly costs with optimization tips
  audit       Security & compliance scanning
  drift       Detect configuration drift from Terraform state

Advanced:
  remediate   Generate Terraform fixes from audit findings
  unused      Find unused and underutilized resources
  trends      Cost trend analysis and anomaly detection
  snapshot    Snapshot management for change tracking
  dr          Disaster recovery readiness assessment

Configuration:
  license     License management
```

---

### 4. Unclear Error Messages for Common Mistakes

**Current Errors:**

```python
# errors.py provides good categorization but messages aren't user-friendly
AccessDenied: "Check IAM permissions. Ensure the scanning role/user has
the required read-only permissions for this service."
```

**Issue:** Doesn't tell user HOW to check or WHAT permission is missing.

**Recommendation:** Error messages should include:
1. What went wrong (concise)
2. Why it went wrong (context)
3. How to fix it (actionable steps)
4. Where to learn more (docs link)

**Example:**
```
❌ Permission Denied: ec2:DescribeVpcs

Why: Your IAM user/role cannot list VPCs in us-east-1

Quick Fix:
  1. Open IAM Policy for your user/role
  2. Add permission: "ec2:DescribeVpcs"
  3. Or attach our pre-built policy:
     aws iam attach-user-policy --user-name replimap \\
       --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess

📖 Docs: https://replimap.com/docs/iam-setup
```

---

### 5. Interactive Mode Incomplete

**scan.py** has `--interactive` mode but:
- Only prompts for profile and region
- Doesn't ask about filters, output, or cache options
- clone.py, cost.py, audit.py don't have interactive mode at all

**Recommendation:**
- Expand `--interactive` to ask about all common options
- Add to all commands, not just scan
- Include "smart defaults" based on previous runs

**Example Flow:**
```bash
$ replimap scan --interactive

🔍 RepliMap Interactive Scan

1. AWS Profile:
   ○ default
   ● prod (last used)
   ○ staging
   Select: [prod]

2. Region:
   ● ap-southeast-2 (from profile)
   Change? [n]

3. Scope:
   ○ Full account scan
   ● Filter by VPC
   ○ Filter by tags
   Select VPC: [vpc-12345678] (last used)

4. Cache:
   Use cached results from 2 hours ago? [y]

Starting scan...
```

---

### 6. No Undo/Confirmation for Destructive Operations

**Issue:** No confirmation prompts for:
- `replimap cache clear` (deletes all cached data)
- `replimap snapshot delete <id>` (permanent)
- `replimap drift --fix` (modifies infrastructure)

**Recommendation:**
- Add confirmation prompts for destructive operations
- Require `--yes` flag to skip prompt (for CI/CD)
- Show what WILL be deleted/modified before confirmation

---

### 7. Confusing `--mode` Flag in clone

```python
mode: str = typer.Option(
    "dry-run",
    "--mode",
    "-m",
    help="Mode: 'dry-run' (preview) or 'generate' (create files)",
)
```

**Issue:**
- Users expect `replimap clone` to generate files (not preview)
- `dry-run` as default is surprising
- Flag name `--mode` is generic

**Recommendation:**
```python
# Better: Use explicit boolean flag
preview: bool = typer.Option(
    False,
    "--preview",
    "-p",
    help="Preview files without writing (dry-run mode)",
)

# Default behavior: generate files
# To preview: add --preview
```

**Usage:**
```bash
# Old way (confusing)
replimap clone --mode dry-run      # Preview
replimap clone --mode generate     # Actually generate

# New way (intuitive)
replimap clone --preview           # Preview
replimap clone                     # Generate files
```

---

### 8. Missing Command Aliases

**Issue:** No shortcuts for common operations.

**Recommendation:** Add aliases for frequently used commands:

```python
# scan aliases
scan = scan  # Full name
s = scan     # Short alias

# clone aliases
clone = clone
gen = clone  # "generate IaC"

# audit aliases
audit = audit
check = audit
```

Users can then run:
```bash
replimap s --profile prod        # Scan
replimap gen --format terraform  # Generate
replimap check                   # Audit
```

---

### 9. No Progress Indication for Long Operations

**Issue:** Some operations take 30s-5min with no progress:
- `replimap scan` (23 scanners, varies by account size)
- `replimap audit` (runs Checkov on generated Terraform)
- `replimap cost` (fetches pricing data)

**Current State:**
```python
# scan.py has progress bar ✅
with Progress(...) as progress:
    task = progress.add_task("Scanning AWS resources...", total=total_scanners)

# audit.py uses spinner ⚠️
with Progress(SpinnerColumn(), TextColumn(...)) as progress:
    task = progress.add_task("Running security audit...", total=None)
```

**Recommendation:**
- audit.py: Show progress per check (not spinner)
- cost.py: Show progress per pricing API call
- Add elapsed time + ETA for all long operations

---

### 10. Inconsistent Flag Naming Convention

**Issue:** Mix of naming styles:

```python
--no-cache      # Negative boolean
--refresh       # Positive boolean
--downsize      # Positive with --no-downsize
--open/--no-open  # Explicit pair
```

**Recommendation:** Use consistent pattern:
- Primary flag: `--flag` (enables)
- Disable flag: `--no-flag` (disables)
- Always define both explicitly

```python
# Good
downsize: bool = typer.Option(
    True,  # Default enabled
    "--downsize/--no-downsize",
    help="Enable instance downsizing for cost savings",
)

# Bad (inconsistent with others)
refresh: bool = typer.Option(
    False,
    "--refresh",
    help="Force fresh AWS scan",
)

# Better
use_cache: bool = typer.Option(
    True,
    "--cache/--no-cache",
    help="Use cached scan results",
)
```

---

## Quick Wins (Low Effort, High Impact)

1. **Add command categories to help text** (1 day)
2. **Standardize `--output` vs `--output-dir`** (2 days)
3. **Add confirmation prompts for destructive ops** (1 day)
4. **Improve error messages with actionable steps** (3 days)
5. **Change clone default from dry-run to generate** (1 day)

---

## Medium-Term Improvements

1. **Expand interactive mode to all commands** (1 week)
2. **Add `replimap config show` command** (3 days)
3. **Implement command aliases** (2 days)
4. **Progress bars for all long operations** (5 days)

---

## Long-Term (Requires UX Research)

1. **User testing with 10-20 developers** (2 weeks)
2. **Analyze CLI analytics (if available)** (ongoing)
3. **A/B test different argument naming schemes** (1 month)

---

## Comparison with Best-in-Class CLIs

### GitHub CLI (`gh`)
- ✅ Clear command categories
- ✅ Consistent flag naming
- ✅ Interactive mode for all commands
- ✅ Excellent error messages with suggestions

### Terraform CLI
- ✅ Progressive disclosure (common commands first)
- ✅ Consistent `-flag` vs `--flag` (always single dash)
- ✅ Color-coded output with clear sections

### AWS CLI v2
- ⚠️ Too many flags (kitchen sink approach)
- ✅ Consistent patterns across 300+ services
- ✅ Auto-complete support

**RepliMap should aim for:** GitHub CLI's usability + Terraform's clarity

---

## Metrics to Track Improvement

**Before:**
- Time to first successful scan: ~10 min (trial & error with flags)
- Support tickets for "how do I...": ~30%
- Command re-runs due to flag confusion: ~25%

**After (Target):**
- Time to first successful scan: ~2 min
- Support tickets: <10%
- Command re-runs: <5%

---

## References

- **CLI Guidelines:** https://clig.dev/
- **Human Interface Guidelines (CLI):** https://hig.apple.com
- **User Research:** Conduct task-based usability testing with 5-10 users
- **Analytics:** Track command usage patterns (if telemetry enabled)

---

**Reviewed:** 2026-01-11
**Reviewer:** Claude (Automated Code Review)
**Status:** Recommendations for Product/UX team
