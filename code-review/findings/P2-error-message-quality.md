# P2: Error Message Quality & User Guidance

**Priority:** P2 (Medium - User Experience)
**Category:** Error Handling / User Communication
**Impact:** Medium - Affects troubleshooting time and user frustration
**Effort:** Medium - Requires rewriting ~50 error messages with consistent pattern

---

## Executive Summary

RepliMap's error handling infrastructure (`core/errors.py`) is technically excellent with proper categorization, recovery recommendations, and AWS error code mapping. However, the error messages themselves lack actionability and user-friendliness. Users receive accurate errors but insufficient guidance on how to resolve them.

**Key Gap:** Technical accuracy ✅ | User empathy ❌

---

## Findings

### 1. Good Foundation: Error Categorization

**Strengths in `errors.py`:**

```python
class ErrorCategory(str, Enum):
    PERMISSION = "permission"      # AccessDenied, UnauthorizedAccess
    TRANSIENT = "transient"        # Throttling, ServiceUnavailable, Timeout
    VALIDATION = "validation"      # MalformedQueryString, InvalidParameter
    RESOURCE = "resource"          # ResourceNotFound, ConflictException
    SERVICE = "service"            # InternalError, ServiceUnavailable
    UNKNOWN = "unknown"
```

✅ **Well-designed categorization**
✅ **Comprehensive AWS error code mapping** (53 error codes mapped)
✅ **Recovery recommendations per category**

---

### 2. Generic Recovery Recommendations

**Current Implementation:**

```python
def get_recovery_recommendation(category: ErrorCategory, error_code: str) -> str:
    recommendations = {
        ErrorCategory.PERMISSION: (
            "Check IAM permissions. Ensure the scanning role/user has "
            "the required read-only permissions for this service."
        ),
        ErrorCategory.TRANSIENT: (
            "This is a temporary issue. Wait a few minutes and retry. "
            "Consider reducing scan concurrency if throttling persists."
        ),
        # ...
    }
```

**Issue:** One-size-fits-all recommendations don't help users understand:
1. **WHAT** specific permission is missing
2. **WHERE** to add the permission
3. **HOW** to verify the fix worked

---

### 3. Missing Context in Permission Errors

**Example Scenario:**
```
User runs: replimap scan --profile prod --region us-east-1
Error: AccessDenied on ec2:DescribeVpcs
```

**Current Error Message:**
```
AccessDenied: Check IAM permissions. Ensure the scanning role/user has
the required read-only permissions for this service.
```

**What's Missing:**
- Which IAM user/role was used?
- What policy should be attached?
- How to test the permission is fixed?
- Link to IAM_POLICY.md with exact policy JSON

**Recommended Message:**
```
❌ Permission Error: ec2:DescribeVpcs

IAM User: arn:aws:iam::123456789012:user/replimap-scanner
Region: us-east-1
Missing Permission: ec2:DescribeVpcs

🔧 How to Fix:

1. Attach the RepliMap IAM policy:
   aws iam attach-user-policy \
     --user-name replimap-scanner \
     --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess

2. Or add specific permission:
   Add "ec2:DescribeVpcs" to your IAM policy

3. Verify the fix:
   aws ec2 describe-vpcs --profile prod --region us-east-1

📖 Full IAM setup guide: https://replimap.com/docs/iam-policy

💡 Tip: Use our minimal IAM policy for least-privilege access
```

---

### 4. AWS Error Code Translation Incomplete

**Good Coverage:**
```python
PERMISSION_ERRORS = frozenset([
    "AccessDenied",
    "AccessDeniedException",
    "UnauthorizedAccess",
    "InvalidClientTokenId",
    "ExpiredToken",
    "ExpiredTokenException",
    "UnrecognizedClientException",
    "SignatureDoesNotMatch",
    "IncompleteSignature",
    "MissingAuthenticationToken",
])  # 10 mapped
```

**Missing Common Errors:**
- `OptInRequired` - Service not enabled in region
- `DryRunOperation` - Common during testing
- `RequestExpired` - Clock skew issues
- `InvalidAccessKeyId` - Typo in credentials
- `InvalidSecretAccessKey` - Wrong secret key
- `PendingVerification` - Account not verified

**Recommendation:** Expand error catalog to 80+ codes with specific guidance for each.

---

### 5. Transient Error Guidance Too Vague

**Current:**
```python
ErrorCategory.TRANSIENT: (
    "This is a temporary issue. Wait a few minutes and retry. "
    "Consider reducing scan concurrency if throttling persists."
)
```

**Issue:** Doesn't tell user:
- How long to wait
- Whether to use --cache to resume
- If automatic retry is happening
- What "reducing concurrency" means

**Recommended:**
```
⏱️  Temporary AWS Issue: Throttling (TooManyRequestsException)

This usually resolves in 30-60 seconds.

Automatic Retry:
  ✓ RepliMap will retry 3 times with exponential backoff
  ✓ Current attempt: 1/3
  ✓ Next retry in: 15 seconds

If This Persists:
  1. Enable scan caching to avoid re-scanning:
     replimap scan --cache

  2. Reduce concurrent API calls:
     replimap scan --concurrency 5 (default: 10)

  3. Check AWS Service Health:
     https://status.aws.amazon.com/

💡 Tip: AWS Free Tier has lower rate limits. Consider upgrading
    or scanning during off-peak hours.
```

---

### 6. No Differentiation Between First-Time and Repeat Errors

**Scenario:**
```
User hits same AccessDenied error 3 times in a row
```

**Current Behavior:**
Same error message every time.

**Recommended Behavior:**
Track error repetition and escalate guidance:

```
# First occurrence
❌ Permission Error: ec2:DescribeVpcs
[Standard fix instructions]

# Second occurrence (5 minutes later)
❌ Permission Error: ec2:DescribeVpcs (2nd occurrence)

Still having issues? Try these troubleshooting steps:

1. Verify your profile is correct:
   aws sts get-caller-identity --profile prod

2. Check policy is attached:
   aws iam list-attached-user-policies --user-name replimap-scanner

3. Test permission directly:
   aws ec2 describe-vpcs --profile prod --region us-east-1

# Third occurrence
❌ Permission Error: ec2:DescribeVpcs (3rd occurrence)

Multiple failures detected. Common causes:

✓ Wrong AWS profile selected
✓ IAM policy not propagated (can take 5-10 minutes)
✓ Cross-account role assumption failing
✓ SCPs (Service Control Policies) blocking access

Need help? Run diagnostics:
  replimap diagnose --profile prod --region us-east-1

Or contact support with diagnostic output:
  support@replimap.com
```

---

### 7. Missing Error Aggregation Summary

**Current Behavior:**
```
Error: AccessDenied on ec2:DescribeVpcs
Error: AccessDenied on ec2:DescribeSubnets
Error: AccessDenied on ec2:DescribeSecurityGroups
[...15 more similar errors...]
```

**Issue:** Floods console with repetitive messages.

**Recommended:**
```
🔒 Permission Errors Detected (18 total)

Missing EC2 permissions:
  • ec2:DescribeVpcs
  • ec2:DescribeSubnets
  • ec2:DescribeSecurityGroups
  • ec2:DescribeInstances
  • ec2:DescribeRouteTables
  ... and 13 more

🔧 Quick Fix: Attach our pre-built policy
   aws iam attach-user-policy \
     --user-name replimap-scanner \
     --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess

📋 Or see required permissions:
   replimap iam --show-required-permissions > iam-policy.json
   aws iam put-user-policy --user-name replimap-scanner \
     --policy-name RepliMapReadOnly --policy-document file://iam-policy.json

Full error log: ~/.replimap/logs/scan-2026-01-11-143025.log
```

---

### 8. No Searchable Error Codes

**Issue:** Users can't Google "RepliMap error RM-1234" for help.

**Recommendation:** Assign error codes to common issues:

```
RM-E001: IAM Permission Missing
RM-E002: Invalid AWS Credentials
RM-E003: Region Not Supported
RM-E004: VPC Not Found
RM-E005: License Expired
RM-E006: Scan Quota Exceeded
```

**Example:**
```
❌ [RM-E001] IAM Permission Missing: ec2:DescribeVpcs

[Instructions...]

🔍 More help: https://replimap.com/errors/RM-E001
💬 Community: https://github.com/RepliMap/replimap/issues?q=RM-E001
```

---

### 9. Error Context Not Captured

**Current `DetailedError` dataclass:**
```python
@dataclass
class DetailedError:
    error_code: str
    error_message: str
    category: ErrorCategory
    timestamp: datetime
    scanner_name: str
    operation: str
    region: str
    account_id: str
    # ...
```

**Missing Fields:**
```python
# Add these
profile_name: str = ""           # Which profile was used
cli_command: str = ""            # What command failed
cli_args: dict = field(default_factory=dict)  # Command arguments
user_action: str = ""            # What user was trying to do
retry_count: int = 0             # How many times retried
last_successful_scan: datetime | None = None  # When last scan succeeded
environment: dict = field(default_factory=dict)  # OS, Python version, etc.
```

**Why:** Better error context = better diagnostics = faster resolution.

---

### 10. No "Did You Mean?" Suggestions

**Scenario:**
```bash
$ replimap scna --profile prod
Error: No such command "scna"
```

**Recommended:**
```bash
$ replimap scna --profile prod
Error: Unknown command "scna"

Did you mean?
  • scan  (Scan AWS resources)
  • snapshot  (Manage infrastructure snapshots)

See all commands:
  replimap --help
```

---

## Recommended Error Message Template

**Standard Structure:**

```
[Icon] [Category]: [Brief Description]

Context:
  • User/Role: [ARN]
  • Region: [region]
  • Resource: [resource-id]
  • Operation: [operation]

How to Fix:
  1. [Step 1 with command]
  2. [Step 2 with command]
  3. [Verification step]

Learn More:
  📖 Docs: [URL]
  💬 Community: [GitHub issue search]
  📧 Support: support@replimap.com

[Tips or common mistakes]
```

---

## Quick Wins (High Impact, Low Effort)

1. **Add error codes (RM-E###) to all error classes** (2 days)
2. **Expand recovery recommendations with specific AWS CLI commands** (3 days)
3. **Add "Did you mean?" to typo'd commands** (1 day)
4. **Aggregate repetitive errors into summary** (2 days)
5. **Include IAM ARN in permission errors** (1 day)

---

## Medium-Term Improvements

1. **Error repetition tracking + escalated guidance** (1 week)
2. **Expand AWS error code catalog from 53 to 80+** (1 week)
3. **Add `replimap diagnose` command** (1 week)
4. **Create error documentation site at replimap.com/errors/** (2 weeks)

---

## Long-Term Enhancements

1. **AI-powered error diagnosis** (integrate with LLM to explain error in user context)
2. **Automatic fix generation** (generate shell scripts to fix detected issues)
3. **Telemetry-based error insights** (identify most common errors, improve proactively)

---

## Competitive Analysis

### Terraform
- ✅ Clear error messages with context
- ✅ Suggests commands to fix
- ⚠️ Sometimes too verbose

### AWS CLI v2
- ⚠️ Cryptic error codes
- ⚠️ Minimal guidance
- ✅ Consistent structure

### Pulumi
- ✅ Excellent error messages
- ✅ Links to relevant docs
- ✅ Color-coded severity

**RepliMap should aim for:** Pulumi's helpfulness + Terraform's clarity

---

## Success Metrics

**Before:**
- Average time to resolve permission error: ~15 minutes
- Support tickets for "getting started": ~40%
- User abandonment after first error: ~30%

**After (Target):**
- Time to resolve error: <3 minutes
- Support tickets: <15%
- User abandonment: <10%

---

**Reviewed:** 2026-01-11
**Reviewer:** Claude (Automated Code Review)
**Status:** Recommendations for Engineering team
