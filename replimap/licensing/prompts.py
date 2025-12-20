"""
Upgrade Prompt Messages for RepliMap.

These messages are shown when users hit plan limits.
Designed to be helpful, not annoying - show value first, then ask for upgrade.

核心原则: 用户已经体验了价值，现在需要付费才能"带走"
"""

from __future__ import annotations

from typing import Any


# =============================================================================
# UPGRADE PROMPTS
# =============================================================================

UPGRADE_PROMPTS: dict[str, str] = {
    # =========================================================================
    # SCAN LIMITS
    # =========================================================================
    "scan_monthly_limit": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  📊 Monthly Scan Limit Reached                                               │
│                                                                               │
│  You've used {used}/{limit} free scans this month.                           │
│  Next reset: {reset_date}                                                    │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Your previous scans are still available.                               │ │
│  │  You can still view graphs, preview code, and see audit summaries.      │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  Upgrade to Solo ($49/mo) for unlimited scans:                               │
│  → replimap upgrade solo                                                     │
│  → https://replimap.dev/pricing                                              │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    # =========================================================================
    # CLONE LIMITS
    # =========================================================================
    "clone_download_blocked": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  📦 Terraform Code Generated Successfully!                                    │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Resources scanned:    {resource_count:,}                                │ │
│  │  Lines of code:        {lines_count:,}                                   │ │
│  │  Files generated:      {file_count}                                      │ │
│  │  Estimated time saved: {hours_saved} hours (~${money_saved} value)       │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  🔒 FREE PLAN: Preview only (first {preview_lines} lines shown)              │
│                                                                               │
│  To download the complete Terraform code:                                    │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Solo Plan: $49/month                                                    │ │
│  │                                                                          │ │
│  │  ✓ Download unlimited Terraform code                                     │ │
│  │  ✓ Full audit reports with remediation steps                             │ │
│  │  ✓ Graph exports without watermark                                       │ │
│  │  ✓ Email support                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  → replimap upgrade solo                                                     │
│  → https://replimap.dev/pricing                                              │
│                                                                               │
│  💡 At $49/mo, that's less than 30 minutes of your hourly rate.              │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    "clone_preview_truncated": """
# ─────────────────────────────────────────────────────────────────────────────
# ... {remaining_lines:,} more lines hidden ...
#
# 🔒 FREE PLAN: Preview only ({preview_lines} of {total_lines:,} lines)
#
# Generated: {resource_count:,} resources in {file_count} files
# Estimated time saved: {hours_saved} hours
#
# → replimap upgrade solo  (Download complete code)
# ─────────────────────────────────────────────────────────────────────────────
""",

    # =========================================================================
    # AUDIT LIMITS
    # =========================================================================
    "audit_limited_view": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  🛡️ Security Audit Complete                                                  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                          │ │
│  │  Security Score:  {score}/100  Grade: {grade}                           │ │
│  │                                                                          │ │
│  │  Issues Found:                                                           │ │
│  │  ├── 🔴 CRITICAL:  {critical_count}                                      │ │
│  │  ├── 🟠 HIGH:      {high_count}                                          │ │
│  │  ├── 🟡 MEDIUM:    {medium_count}                                        │ │
│  │  └── 🔵 LOW:       {low_count}                                           │ │
│  │                                                                          │ │
│  │  TOTAL: {total_count} security issues detected                          │ │
│  │                                                                          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  🔒 FREE PLAN: Showing {shown_count} of {total_count} issues                 │
│                                                                               │
│  ⚠️  {hidden_critical} CRITICAL issues are hidden!                           │
│                                                                               │
│  Hidden issues may include:                                                  │
│  • Publicly accessible S3 buckets                                            │
│  • Unencrypted databases                                                     │
│  • Security groups open to 0.0.0.0/0                                         │
│  • IAM policies with excessive permissions                                   │
│                                                                               │
│  Upgrade to Solo ($49/mo) to see all {total_count} issues:                   │
│  → replimap upgrade solo                                                     │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    "audit_export_blocked": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  📄 Report Export Requires Solo Plan                                         │
│                                                                               │
│  FREE plan includes:                                                         │
│  ✓ Full security scanning                                                    │
│  ✓ Summary scores and counts                                                 │
│  ✓ Preview of top 3 issues                                                   │
│                                                                               │
│  Solo plan ($49/mo) adds:                                                    │
│  ✓ Export to HTML report                                                     │
│  ✓ View all findings with details                                            │
│  ✓ Terraform fix suggestions                                                 │
│                                                                               │
│  → replimap upgrade solo                                                     │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    "audit_ci_blocked": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  🔧 CI/CD Mode Requires Pro Plan                                             │
│                                                                               │
│  The --fail-on-high flag is a Pro feature.                                   │
│                                                                               │
│  Pro plan ($99/mo) includes:                                                 │
│  ✓ CI/CD integration (--fail-on-high, --fail-on-score)                       │
│  ✓ Drift detection                                                           │
│  ✓ Cost estimation                                                           │
│  ✓ 3 AWS accounts                                                            │
│                                                                               │
│  → replimap upgrade pro                                                      │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    # =========================================================================
    # DRIFT LIMITS
    # =========================================================================
    "drift_not_available": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  🔍 Drift Detection is a Pro Feature                                         │
│                                                                               │
│  Drift detection helps you:                                                  │
│  • Find unauthorized changes in AWS                                          │
│  • Ensure Terraform state stays in sync                                      │
│  • Meet SOC2 CC8.1 Change Management requirements                            │
│  • Catch "console cowboys" who bypass IaC                                    │
│                                                                               │
│  Pro plan ($99/mo) includes:                                                 │
│  ✓ Drift detection                                                           │
│  ✓ Cost estimation                                                           │
│  ✓ CI/CD mode for audit                                                      │
│  ✓ 3 AWS accounts                                                            │
│                                                                               │
│  → replimap upgrade pro                                                      │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    "drift_watch_not_available": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  👁️ Drift Watch Mode is a Team Feature                                       │
│                                                                               │
│  Watch mode provides:                                                        │
│  • Continuous drift monitoring                                               │
│  • Slack/Teams alerts when drift detected                                    │
│  • Scheduled scans                                                           │
│                                                                               │
│  Team plan ($199/mo) includes:                                               │
│  ✓ Drift watch mode                                                          │
│  ✓ Alert notifications                                                       │
│  ✓ Blast radius analysis                                                     │
│  ✓ 10 AWS accounts                                                           │
│  ✓ 5 team members                                                            │
│                                                                               │
│  → replimap upgrade team                                                     │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    # =========================================================================
    # OTHER FEATURE LIMITS
    # =========================================================================
    "cost_not_available": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  💰 Cost Estimation is a Pro Feature                                         │
│                                                                               │
│  Cost estimation helps you:                                                  │
│  • Know how much your staging will cost before cloning                       │
│  • Find cost optimization opportunities                                      │
│  • Plan infrastructure budgets                                               │
│                                                                               │
│  → replimap upgrade pro ($99/mo)                                             │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    "blast_not_available": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  💥 Blast Radius Analysis is a Team Feature                                  │
│                                                                               │
│  Blast radius shows you:                                                     │
│  • What will break if you delete a resource                                  │
│  • Dependency chains you might not know about                                │
│  • Safe deletion order for cleanup                                           │
│                                                                               │
│  → replimap upgrade team ($199/mo)                                           │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    "multi_account_limit": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  🔐 Multiple AWS Accounts Require Upgrade                                    │
│                                                                               │
│  You're trying to use {current_count} AWS accounts.                          │
│  Your current plan allows {limit} account(s).                                │
│                                                                               │
│  Upgrade to {upgrade_plan} (${upgrade_price}/mo) for more accounts.          │
│                                                                               │
│  → replimap upgrade {upgrade_plan_lower}                                     │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    # =========================================================================
    # GRAPH WATERMARK
    # =========================================================================
    "graph_watermark_notice": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  📊 Graph Exported (with watermark)                                          │
│                                                                               │
│  Your architecture graph has been exported.                                  │
│  FREE plan exports include a RepliMap watermark.                             │
│                                                                               │
│  Upgrade to Solo ($49/mo) for watermark-free exports.                        │
│  → replimap upgrade solo                                                     │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    # =========================================================================
    # OUTPUT FORMAT LIMITS
    # =========================================================================
    "cloudformation_not_available": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  ☁️ CloudFormation Output Requires Pro Plan                                  │
│                                                                               │
│  FREE/Solo plans include Terraform output.                                   │
│                                                                               │
│  Pro plan ($99/mo) adds:                                                     │
│  ✓ CloudFormation YAML output                                                │
│  ✓ Pulumi Python output                                                      │
│  ✓ Drift detection                                                           │
│  ✓ 3 AWS accounts                                                            │
│                                                                               │
│  → replimap upgrade pro                                                      │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    "pulumi_not_available": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  🔧 Pulumi Output Requires Pro Plan                                          │
│                                                                               │
│  FREE/Solo plans include Terraform output.                                   │
│                                                                               │
│  Pro plan ($99/mo) adds:                                                     │
│  ✓ Pulumi Python output                                                      │
│  ✓ CloudFormation YAML output                                                │
│  ✓ Drift detection                                                           │
│  ✓ 3 AWS accounts                                                            │
│                                                                               │
│  → replimap upgrade pro                                                      │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",

    "cdk_not_available": """
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  🔧 CDK Output Requires Team Plan                                            │
│                                                                               │
│  Team plan ($199/mo) includes:                                               │
│  ✓ AWS CDK output                                                            │
│  ✓ All IaC formats (Terraform, CloudFormation, Pulumi)                       │
│  ✓ Drift watch mode with alerts                                              │
│  ✓ Blast radius analysis                                                     │
│  ✓ 10 AWS accounts                                                           │
│                                                                               │
│  → replimap upgrade team                                                     │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
""",
}


def get_upgrade_prompt(key: str, params: dict[str, Any] | None = None) -> str:
    """
    Get an upgrade prompt with parameters filled in.

    Args:
        key: The prompt key from UPGRADE_PROMPTS
        params: Dictionary of parameters to format into the prompt

    Returns:
        Formatted upgrade prompt string
    """
    prompt = UPGRADE_PROMPTS.get(key, "")
    if params:
        try:
            prompt = prompt.format(**params)
        except KeyError:
            # If some params are missing, just return what we can
            pass
    return prompt


def format_scan_limit_prompt(used: int, limit: int, reset_date: str) -> str:
    """Format the scan limit reached prompt."""
    return get_upgrade_prompt("scan_monthly_limit", {
        "used": used,
        "limit": limit,
        "reset_date": reset_date,
    })


def format_clone_blocked_prompt(
    resource_count: int,
    lines_count: int,
    file_count: int,
    preview_lines: int = 100,
) -> str:
    """Format the clone download blocked prompt."""
    hours_saved = max(1, resource_count // 10)
    money_saved = hours_saved * 100  # $100/hour estimate

    return get_upgrade_prompt("clone_download_blocked", {
        "resource_count": resource_count,
        "lines_count": lines_count,
        "file_count": file_count,
        "preview_lines": preview_lines,
        "hours_saved": hours_saved,
        "money_saved": money_saved,
    })


def format_clone_preview_footer(
    remaining_lines: int,
    preview_lines: int,
    total_lines: int,
    resource_count: int,
    file_count: int,
) -> str:
    """Format the footer to append to truncated clone output."""
    hours_saved = max(1, resource_count // 10)

    return get_upgrade_prompt("clone_preview_truncated", {
        "remaining_lines": remaining_lines,
        "preview_lines": preview_lines,
        "total_lines": total_lines,
        "resource_count": resource_count,
        "file_count": file_count,
        "hours_saved": hours_saved,
    })


def format_audit_limited_prompt(
    score: int,
    grade: str,
    critical_count: int,
    high_count: int,
    medium_count: int,
    low_count: int,
    shown_count: int,
    total_count: int,
    hidden_critical: int,
) -> str:
    """Format the audit limited findings prompt."""
    return get_upgrade_prompt("audit_limited_view", {
        "score": score,
        "grade": grade,
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "shown_count": shown_count,
        "total_count": total_count,
        "hidden_critical": hidden_critical,
    })


def format_multi_account_prompt(
    current_count: int,
    limit: int,
    upgrade_plan: str,
    upgrade_price: int,
) -> str:
    """Format the multi-account limit prompt."""
    return get_upgrade_prompt("multi_account_limit", {
        "current_count": current_count,
        "limit": limit,
        "upgrade_plan": upgrade_plan,
        "upgrade_price": upgrade_price,
        "upgrade_plan_lower": upgrade_plan.lower(),
    })
