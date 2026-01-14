# P2: Usage Tracking Bypass Vulnerabilities

**Session ID:** 3.2
**Category:** Business Logic / Licensing
**Priority:** P2 (Medium)
**Date:** 2026-01-11
**Status:** Open

---

## Executive Summary

RepliMap's FREE tier enforcement relies on client-side usage tracking stored in `~/.replimap/usage_history.json`. Multiple bypass vectors exist that allow unlimited scans without authentication, enabling free usage of paid features. The 3 scans/month limit is trivially circumvented, undermining the entire freemium business model.

**Business Impact:**
- FREE tier users can bypass all scan limits indefinitely
- No server-side validation or license server enforcement
- Revenue leakage: users avoid $49/mo SOLO upgrade
- Competitive disadvantage vs cloud-based alternatives (Terraform Cloud, Spacelift)

---

## Vulnerability Analysis

### 1. **Client-Side Storage Bypass**

**File:** `/home/davidlu/private-repo/org-replimap/replimap/replimap/licensing/tracker.py`

**Finding:**
Usage history is stored in a local JSON file with no integrity protection:

```python
# Lines 273-285
def _load_history(self) -> None:
    """Load usage history from disk."""
    if not self.usage_file.exists():
        return

    try:
        data = json.loads(self.usage_file.read_text())
        self._scans = [ScanRecord.from_dict(s) for s in data.get("scans", [])]
        logger.debug(f"Loaded {len(self._scans)} scan records")
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Failed to load usage history: {e}")
        self._scans = []  # Corruption = free reset!
```

**Bypass Methods:**

```bash
# Method 1: Delete history (instant reset)
rm ~/.replimap/usage_history.json

# Method 2: Manual corruption (triggers graceful reset)
echo "invalid" > ~/.replimap/usage_history.json

# Method 3: Timestamp manipulation (edit JSON timestamps)
# Set all scan dates to previous month
sed -i 's/"2026-01-11/"2025-12-01/g' ~/.replimap/usage_history.json

# Method 4: Environment isolation (unlimited parallel accounts)
HOME=/tmp/fake1 replimap scan  # Clean slate
HOME=/tmp/fake2 replimap scan  # Another clean slate
```

**Root Cause:**
- No cryptographic signatures (HMAC/JWT)
- No server-side quota validation
- Corruption = automatic reset to FREE tier unlimited usage

---

### 2. **Monthly Limit Enforcement Gap**

**File:** `/home/davidlu/private-repo/org-replimap/replimap/replimap/licensing/gates.py`

**Finding:**
The `check_scan_allowed()` gate (lines 286-334) only counts scans THIS month:

```python
# Lines 306-326
scans_this_month = tracker.get_scans_this_month()
if scans_this_month >= features.max_scans_per_month:
    # Calculate next reset date
    now = datetime.now()
    next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
    reset_date = next_month.strftime("%B %d, %Y")

    prompt = format_scan_limit_prompt(
        used=scans_this_month,
        limit=features.max_scans_per_month,
        reset_date=reset_date,
    )
    return GateResult(allowed=False, prompt=prompt, ...)
```

**Bypass:**
```python
# tracker.py lines 220-225
def get_scans_this_month(self) -> int:
    """Get the number of scans performed this month."""
    current_month = datetime.now(UTC).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    return sum(1 for s in self._scans if s.timestamp >= current_month)
```

**Attack Vector:**
1. User modifies system clock to next month → instant reset
2. Docker container with fixed clock month → unlimited scans per container
3. Edit JSON timestamps to spread scans across "months"

---

### 3. **No Machine Fingerprinting Enforcement**

**File:** `/home/davidlu/private-repo/org-replimap/replimap/replimap/licensing/models.py`

**Finding:**
Machine fingerprinting exists (lines 849-873) but is OPTIONAL:

```python
# Lines 809-813
def validate_machine(self, fingerprint: str) -> bool:
    """Validate the machine fingerprint."""
    if self.machine_fingerprint is None:
        return True  # Not bound to machine ← BYPASS!
    return self.machine_fingerprint == fingerprint
```

**Business Risk:**
- FREE tier has no machine binding requirement
- Same user can run unlimited scans across unlimited machines
- No per-machine quotas (vs Terraform Cloud's per-workspace limits)

---

### 4. **Concurrent Scan Vulnerability**

**Finding:**
No atomic increment or locking when recording scans:

```python
# tracker.py lines 176-177
self._scans.append(record)
self._save_history()
```

**Race Condition:**
```bash
# Terminal 1
replimap scan &

# Terminal 2 (simultaneously)
replimap scan &

# Both read scans_this_month=2, both allow (should be blocked at 3)
```

**Impact:**
- FREE users can exceed 3/month limit via concurrent scans
- No file locking on `usage_history.json`

---

## Competitive Analysis

### Terraform Cloud (HashiCorp)
- ✅ Server-side quota enforcement
- ✅ Per-workspace run limits
- ✅ License server validates all operations
- ✅ Usage metering API

### Spacelift
- ✅ SaaS-only model (no client bypass)
- ✅ Real-time license validation
- ✅ Audit trail immutable in cloud

### RepliMap
- ❌ Client-side quota tracking
- ❌ No license server
- ❌ File-based limits (easily bypassed)
- ❌ No audit trail integrity

---

## Business Impact Assessment

### Revenue Leakage Scenarios

**Scenario 1: Power User Bypass**
- Target: DevOps engineer at 500-person company
- Expected: Pay $49/mo for SOLO (unlimited scans)
- Reality: Delete `usage_history.json` monthly → $0/mo
- **Annual Loss:** $588/user × 100 companies = $58,800

**Scenario 2: Multi-Machine Exploitation**
- Target: Consultant scanning 10 client accounts
- Expected: Pay $199/mo for TEAM (10 accounts)
- Reality: Run scans on 10 different VMs → $0/mo
- **Annual Loss:** $2,388/user × 50 consultants = $119,400

**Scenario 3: Educational Use**
- Target: Bootcamp with 200 students
- Expected: 3 scans/month per student (acceptable)
- Reality: Students share bypass technique → 600 scans/month
- **Resource Cost:** 200x higher AWS API usage than projected

---

## Recommended Mitigations

### Short-Term (v0.4.0 - Immediate)

**1. Add Tamper Detection**
```python
# Sign usage history with HMAC
import hmac
import hashlib

def _save_history(self) -> None:
    data = {"version": 1, "scans": [...]}
    payload = json.dumps(data, sort_keys=True)

    # Generate HMAC using machine fingerprint as key
    signature = hmac.new(
        get_machine_fingerprint().encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    data["signature"] = signature
    self.usage_file.write_text(json.dumps(data))

def _load_history(self) -> None:
    # Verify signature, reject if invalid
    if not verify_signature(data):
        logger.error("Usage history corrupted - resetting to SAFE mode")
        self._scans = []
        self._enforce_strict_limit()  # Immediate upgrade prompt
```

**2. Implement Usage Lockout**
```python
# After 3 failed verification attempts, require online license check
if self._tampering_attempts > 3:
    raise LicenseValidationError(
        "Usage tracking integrity violated. "
        "Please contact support@replimap.com or upgrade to SOLO."
    )
```

---

### Medium-Term (v0.5.0 - Q2 2026)

**3. Optional License Server**
```python
# Hybrid model: offline-first, online-verify
class LicenseManager:
    def check_scan_quota(self) -> bool:
        # Try local check first
        if self.offline_mode:
            return self._check_local_quota()

        # Online validation for FREE tier
        if self.current_plan == Plan.FREE:
            return self._verify_with_server()  # Requires internet

        # Paid tiers: offline with periodic sync
        return True
```

**Implementation:**
- FREE tier: Monthly online check required (3 scans = 3 pings)
- SOLO+: Offline-first with 30-day grace period
- Grace period allows air-gapped environments (compliance requirement)

---

### Long-Term (v1.0.0 - H2 2026)

**4. Hardware-Bound Licensing**
```python
# Bind FREE tier to hardware fingerprint + cloud validation
license = License(
    plan=Plan.FREE,
    machine_fingerprint=get_machine_fingerprint(),
    device_id=get_device_id(),  # TPM/Secure Enclave on supported platforms
    online_check_required=True,
)
```

**5. Telemetry Opt-In for FREE Tier**
```
FREE tier users consent to anonymous usage telemetry:
- Scan timestamps (not resource data)
- Resource counts (aggregate only)
- Region distribution

Privacy-preserving quota enforcement without exposing infrastructure details.
```

---

## Acceptance Criteria

1. **Tamper Detection:**
   - ✅ HMAC signature on `usage_history.json`
   - ✅ Invalid signature triggers upgrade prompt (not silent reset)
   - ✅ Test: Manual corruption blocks scans after 3 attempts

2. **Machine Binding:**
   - ✅ FREE tier scans tied to hardware fingerprint
   - ✅ Fingerprint mismatch requires re-verification
   - ✅ Paid tiers: 3 machines per license (SOLO), unlimited (TEAM+)

3. **Concurrent Safety:**
   - ✅ File locking on `usage_history.json` writes
   - ✅ Atomic increment of scan counter
   - ✅ Test: 10 simultaneous scans respect limit

4. **Monitoring:**
   - ✅ Log tampering attempts (local only, no cloud)
   - ✅ Metrics: "corrupted_history_events", "quota_bypass_attempts"

---

## Alternative: Embrace Open Source Model

**Strategic Pivot:**
Instead of fighting bypasses, consider:

1. **Open Core Model**
   - Scan + Graph = 100% free, unlimited
   - Clone/Audit/Drift = paid features (already gated)
   - Focus enforcement on OUTPUT, not INPUT

2. **Value-Based Pricing**
   - FREE: Unlimited scans, limited exports
   - SOLO: Export rights + support
   - PRO+: Drift/Compliance/Multi-account

3. **Precedent:**
   - Terraform Open Source: Free CLI, unlimited usage
   - Revenue from Terraform Cloud: Collaboration + Enterprise features
   - RepliMap could follow: Free scanning, paid orchestration/SaaS

---

## References

- **Affected Files:**
  - `/replimap/licensing/tracker.py` (storage layer)
  - `/replimap/licensing/gates.py` (enforcement)
  - `/replimap/cli/commands/scan.py` (gate check callsite)

- **Related Findings:**
  - P0-licensing-security.md (crypto weaknesses)
  - P2-pricing-inconsistencies.md (pricing model issues)

- **Competitor Research:**
  - Terraform Cloud pricing: https://www.terraform.io/cloud/pricing
  - Spacelift licensing: https://spacelift.io/pricing
  - Former2: 100% free (browser-based, no enforcement)

---

## Conclusion

The current usage tracking system provides **zero revenue protection** for the FREE tier. Any technically competent user can bypass limits in under 60 seconds. This undermines the freemium funnel and creates an unfair competitive landscape.

**Recommended Path:**
1. Implement HMAC signatures (1 sprint, low risk)
2. Add online license check for FREE tier (2 sprints, medium risk)
3. Re-evaluate pricing strategy: Is enforcement worth the UX friction?

**Decision Point:**
Should RepliMap compete on restrictive licensing (HashiCorp model) or embrace open-source scanning with paid features (Terraform OSS model)? Current hybrid approach achieves neither.

---

**Sign-off:** Code Review - Session 3.2
**Next Session:** 3.3 - Pricing Model Validation
