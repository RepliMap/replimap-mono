"""
Silent Recovery Engine - Automatically recovers from errors.

Behavior by operation safety level:
- SAFE operations: Execute silently
- CAUTION operations: Notify user after execution
- SENSITIVE operations: Fail fast in CI, confirm in interactive

This engine attempts to keep operations running by automatically
handling recoverable errors without interrupting the user's workflow.
"""

from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING, Any

import boto3

from replimap.cli.utils.console import console
from replimap.core.context import ExecutionEnvironment, GlobalContext
from replimap.core.identity import IdentityGuard
from replimap.core.operations import OperationClassifier, OperationSafety
from replimap.decisions.manager import DecisionManager
from replimap.decisions.models import DecisionType
from replimap.recovery.actions import (
    RecoveryAction,
    RecoveryResult,
    create_increase_timeout_action,
    create_reduce_concurrency_action,
    create_skip_service_action,
    create_switch_profile_action,
    create_wait_and_retry_action,
)

if TYPE_CHECKING:
    from rich.console import Console

logger = logging.getLogger(__name__)


class SilentRecoveryEngine:
    """
    Attempts to recover from errors automatically.

    Recovery priority:
    1. Try SAFE operations silently
    2. Try CAUTION operations with notification
    3. Try SENSITIVE operations with confirmation (or fail in CI)

    Usage:
        engine = SilentRecoveryEngine(ctx, identity_guard, decision_manager)

        try:
            scan_resource()
        except Exception as e:
            result = engine.attempt_recovery(e, {"service": "s3", "profile": "prod"})
            if result.success and result.should_continue:
                # Retry the operation
                scan_resource()
    """

    def __init__(
        self,
        ctx: GlobalContext,
        identity_guard: IdentityGuard,
        decision_manager: DecisionManager,
        output_console: Console | None = None,
    ):
        """
        Initialize SilentRecoveryEngine.

        Args:
            ctx: Global context
            identity_guard: Identity guard for profile switches
            decision_manager: Decision manager for recording choices
            output_console: Optional console for output
        """
        self.ctx = ctx
        self.identity_guard = identity_guard
        self.decisions = decision_manager
        self.console = output_console or console
        self._recovery_log: list[dict[str, Any]] = []

    def attempt_recovery(
        self,
        error: Exception,
        context: dict[str, Any],
    ) -> RecoveryResult:
        """
        Attempt to recover from an error.

        Args:
            error: The error that occurred
            context: Execution context (profile, region, service, etc.)

        Returns:
            RecoveryResult indicating what happened and whether to continue
        """
        # Generate recovery actions based on error type
        actions = self._generate_actions(error, context)

        if not actions:
            return RecoveryResult.no_action(
                message="No recovery actions available for this error"
            )

        # Try actions in order (already sorted by safety)
        for action in actions:
            safety = OperationClassifier.classify(action.name)

            # Check if we can execute this action
            if not self._can_execute(action, safety, context):
                logger.debug(f"Skipping action {action.name} - not allowed")
                continue

            # Execute the action
            try:
                logger.info(f"Attempting recovery: {action.name}")
                success = action.execute()

                if success:
                    self._log_recovery(action, success=True)
                    self._notify_if_needed(action, safety)
                    self._record_decision_if_needed(action, context)

                    return RecoveryResult(
                        success=True,
                        action_taken=action.name,
                        message=action.success_message,
                        should_continue=True,
                        user_hint=self._generate_hint(action),
                        modified_context=action.params,
                    )

            except Exception as e:
                logger.warning(f"Recovery action failed: {action.name} - {e}")
                self._log_recovery(action, success=False, error=str(e))

        # All recovery attempts failed
        return RecoveryResult(
            success=False,
            action_taken="none",
            message="All recovery attempts failed",
            should_continue=False,
            user_hint=self._generate_fallback_hint(error, context),
        )

    def _generate_actions(
        self,
        error: Exception,
        context: dict[str, Any],
    ) -> list[RecoveryAction]:
        """
        Generate recovery actions based on error type.

        Actions are returned in order of safety (SAFE first, SENSITIVE last).
        """
        error_type = self._classify_error(error)

        actions: list[RecoveryAction] = []

        if error_type == "permission":
            actions.extend(self._permission_actions(error, context))
        elif error_type == "credentials":
            actions.extend(self._credentials_actions(error, context))
        elif error_type == "throttling":
            actions.extend(self._throttling_actions(error, context))
        elif error_type == "timeout":
            actions.extend(self._timeout_actions(error, context))
        elif error_type == "network":
            actions.extend(self._network_actions(error, context))

        # Sort by safety (SAFE first)
        safety_order = {
            OperationSafety.SAFE: 0,
            OperationSafety.CAUTION: 1,
            OperationSafety.SENSITIVE: 2,
        }
        actions.sort(
            key=lambda a: safety_order.get(
                OperationClassifier.classify(a.name),
                1,
            )
        )

        return actions

    def _permission_actions(
        self,
        error: Exception,
        context: dict[str, Any],
    ) -> list[RecoveryAction]:
        """Generate actions for permission errors."""
        service = self._extract_service(error)
        actions: list[RecoveryAction] = []

        # Check if we already have a decision for this service
        decision = self.decisions.get_decision("scan.permissions", f"skip_{service}")
        if decision and decision.value:
            # Already decided to skip this service
            return [create_skip_service_action(service, context)]

        # Action 1: Skip service (CAUTION)
        actions.append(create_skip_service_action(service, context))

        # Action 2: Switch profile (SENSITIVE) - only if alternative exists
        alt_profile = self._find_alternative_profile(context)
        if alt_profile:
            actions.append(create_switch_profile_action(alt_profile, context))

        return actions

    def _credentials_actions(
        self,
        error: Exception,
        context: dict[str, Any],
    ) -> list[RecoveryAction]:
        """Generate actions for credential errors."""
        # For credentials, we mostly need user intervention
        alt_profile = self._find_alternative_profile(context)
        if alt_profile:
            return [create_switch_profile_action(alt_profile, context)]
        return []

    def _throttling_actions(
        self,
        error: Exception,
        context: dict[str, Any],
    ) -> list[RecoveryAction]:
        """Generate actions for throttling errors."""
        actions: list[RecoveryAction] = []

        # Action 1: Wait and retry (SAFE)
        actions.append(create_wait_and_retry_action(30))

        # Action 2: Reduce concurrency (SAFE)
        current = context.get("concurrency", 10)
        if current > 1:
            target = max(1, current // 2)
            actions.append(
                create_reduce_concurrency_action(current, target, context)
            )

        return actions

    def _timeout_actions(
        self,
        error: Exception,
        context: dict[str, Any],
    ) -> list[RecoveryAction]:
        """Generate actions for timeout errors."""
        actions: list[RecoveryAction] = []

        # Action 1: Increase timeout (SAFE)
        current_ms = context.get("timeout_ms", 30000)
        if current_ms < 120000:
            target_ms = min(120000, current_ms * 2)
            actions.append(
                create_increase_timeout_action(current_ms, target_ms, context)
            )

        # Action 2: Wait and retry (SAFE)
        actions.append(create_wait_and_retry_action(10))

        return actions

    def _network_actions(
        self,
        error: Exception,
        context: dict[str, Any],
    ) -> list[RecoveryAction]:
        """Generate actions for network errors."""
        # Network errors usually need retry
        return [create_wait_and_retry_action(15)]

    def _can_execute(
        self,
        action: RecoveryAction,
        safety: OperationSafety,
        context: dict[str, Any],
    ) -> bool:
        """Check if we can execute this action in current environment."""
        # SAFE operations always allowed
        if safety == OperationSafety.SAFE:
            return True

        # SENSITIVE operations in CI = fail fast
        if safety == OperationSafety.SENSITIVE:
            if self.ctx.environment == ExecutionEnvironment.CI:
                logger.info(
                    f"Sensitive operation {action.name} blocked in CI environment"
                )
                return False

            # For identity switches, use IdentityGuard
            if action.name == "switch_profile":
                new_profile = action.params.get("new_profile")
                if new_profile:
                    return self.identity_guard.can_switch_identity(
                        new_profile,
                        action.description,
                    )

        # CAUTION operations allowed in all environments
        return True

    def _notify_if_needed(
        self,
        action: RecoveryAction,
        safety: OperationSafety,
    ) -> None:
        """Notify user if action is CAUTION level."""
        if safety == OperationSafety.CAUTION:
            self.console.print(f"[yellow]🔄 {action.success_message}[/yellow]")

    def _record_decision_if_needed(
        self,
        action: RecoveryAction,
        context: dict[str, Any],
    ) -> None:
        """Record decision for future reference."""
        if action.name == "skip_service":
            service = action.params.get("service", "unknown")
            self.decisions.set_decision(
                scope="scan.permissions",
                rule=f"skip_{service}",
                value=True,
                reason=f"Skipped due to permission error during scan",
                decision_type=DecisionType.SUPPRESS,
                created_by="auto",
            )

    def _log_recovery(
        self,
        action: RecoveryAction,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Log recovery attempt."""
        self._recovery_log.append({
            "action": action.name,
            "params": action.params,
            "success": success,
            "error": error,
            "timestamp": time.time(),
        })

    def _generate_hint(self, action: RecoveryAction) -> str:
        """Generate user hint after successful recovery."""
        hints = {
            "switch_profile": "💡 Next time, use --profile directly",
            "skip_service": (
                "💡 Use 'replimap iam --generate-policy' to get required permissions"
            ),
            "wait_and_retry": "💡 Use --concurrency 3 to reduce API calls",
            "reduce_concurrency": "💡 Use --cache to skip unchanged resources",
            "increase_timeout": "💡 Use --timeout to set custom timeout",
        }
        return hints.get(action.name, "")

    def _generate_fallback_hint(
        self,
        error: Exception,
        context: dict[str, Any],
    ) -> str:
        """Generate hint when all recovery fails."""
        profile = context.get("profile", "default")
        return (
            f"🔧 Automatic recovery failed. Try:\n"
            f"   replimap doctor --profile {profile}\n"
            f"   replimap explain <error_code>"
        )

    def _classify_error(self, error: Exception) -> str:
        """Classify error type from exception."""
        msg = str(error).lower()

        if "accessdenied" in msg or "unauthorized" in msg or "forbidden" in msg:
            return "permission"
        if "expired" in msg or ("invalid" in msg and "credential" in msg):
            return "credentials"
        if "throttl" in msg or "rate" in msg or "limit" in msg or "toomanyrequests" in msg:
            return "throttling"
        if "timeout" in msg or "timed out" in msg:
            return "timeout"
        if "connect" in msg or "network" in msg or "unreachable" in msg:
            return "network"

        return "unknown"

    def _extract_service(self, error: Exception) -> str:
        """Extract service name from error message."""
        msg = str(error)

        # Try to extract from ARN pattern
        arn_match = re.search(r"arn:aws:([a-z0-9-]+):", msg.lower())
        if arn_match:
            return arn_match.group(1)

        # Try to extract from action pattern
        action_match = re.search(r"([a-z0-9]+):[A-Z][a-zA-Z]+", msg)
        if action_match:
            return action_match.group(1)

        # Common service indicators
        service_indicators = {
            "s3": ["bucket", "object", "s3"],
            "ec2": ["instance", "vpc", "subnet", "security group"],
            "rds": ["db instance", "database", "rds"],
            "lambda": ["function", "lambda"],
            "iam": ["role", "policy", "user", "iam"],
        }

        msg_lower = msg.lower()
        for service, indicators in service_indicators.items():
            if any(ind in msg_lower for ind in indicators):
                return service

        return "unknown"

    def _find_alternative_profile(
        self,
        context: dict[str, Any],
    ) -> str | None:
        """Find an alternative profile that might have permissions."""
        try:
            session = boto3.Session()
            profiles = session.available_profiles
            current = context.get("profile", "default")

            # Look for profiles with admin/power keywords
            admin_keywords = ["admin", "power", "root", "full", "master", "super"]
            for profile in profiles:
                if profile != current:
                    if any(kw in profile.lower() for kw in admin_keywords):
                        return profile

            return None
        except Exception:
            return None

    def get_recovery_log(self) -> list[dict[str, Any]]:
        """Get the log of recovery attempts."""
        return list(self._recovery_log)


def create_recovery_engine(
    ctx: GlobalContext,
    identity_guard: IdentityGuard,
    decision_manager: DecisionManager,
) -> SilentRecoveryEngine:
    """
    Factory function to create a SilentRecoveryEngine.

    Args:
        ctx: Global context
        identity_guard: Identity guard
        decision_manager: Decision manager

    Returns:
        Configured SilentRecoveryEngine instance
    """
    return SilentRecoveryEngine(ctx, identity_guard, decision_manager)


__all__ = [
    "SilentRecoveryEngine",
    "create_recovery_engine",
]
