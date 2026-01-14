"""
Recovery Actions - Definitions for error recovery strategies.

Provides structured definitions for recovery actions that can be
attempted when errors occur during AWS operations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecoveryAction:
    """
    A recovery action that can be attempted.

    Attributes:
        name: Action identifier (used for classification)
        description: Human-readable description
        execute: Callable that performs the recovery (returns True if successful)
        success_message: Message to show on success
        failure_message: Message to show on failure
        params: Additional parameters for the action
    """

    name: str
    description: str
    execute: Callable[[], bool]
    success_message: str
    failure_message: str
    params: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


@dataclass
class RecoveryResult:
    """
    Result of a recovery attempt.

    Attributes:
        success: Whether recovery succeeded
        action_taken: Name of action that was taken
        message: Human-readable result message
        should_continue: Whether to continue the original operation
        user_hint: Optional hint for the user
        modified_context: Context modifications made by recovery
    """

    success: bool
    action_taken: str
    message: str
    should_continue: bool
    user_hint: str | None = None
    modified_context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def no_action(
        cls, message: str = "No recovery actions available"
    ) -> RecoveryResult:
        """Create a result indicating no action was taken."""
        return cls(
            success=False,
            action_taken="none",
            message=message,
            should_continue=False,
        )

    @classmethod
    def skipped(cls, reason: str) -> RecoveryResult:
        """Create a result indicating recovery was skipped."""
        return cls(
            success=False,
            action_taken="skipped",
            message=reason,
            should_continue=False,
        )


# Common recovery action templates
def create_wait_and_retry_action(seconds: int) -> RecoveryAction:
    """Create a wait-and-retry action."""
    import time

    return RecoveryAction(
        name="wait_and_retry",
        description=f"Wait {seconds}s and retry",
        execute=lambda: (time.sleep(seconds), True)[1],
        success_message=f"Resumed after {seconds}s cooldown",
        failure_message="Still experiencing issues after wait",
        params={"wait_seconds": seconds},
    )


def create_reduce_concurrency_action(
    current: int,
    target: int,
    context: dict[str, Any],
) -> RecoveryAction:
    """Create a reduce-concurrency action."""

    def execute() -> bool:
        context["concurrency"] = target
        return True

    return RecoveryAction(
        name="reduce_concurrency",
        description=f"Reduce concurrency from {current} to {target}",
        execute=execute,
        success_message=f"Reduced concurrency to {target}",
        failure_message="Cannot reduce concurrency further",
        params={"from": current, "to": target},
    )


def create_skip_service_action(
    service: str,
    context: dict[str, Any],
) -> RecoveryAction:
    """Create a skip-service action."""

    def execute() -> bool:
        context.setdefault("skip_services", []).append(service)
        return True

    return RecoveryAction(
        name="skip_service",
        description=f"Skip {service} and continue scanning",
        execute=execute,
        success_message=f"Skipped {service}, scanning other resources...",
        failure_message="Cannot skip service",
        params={"service": service},
    )


def create_switch_profile_action(
    new_profile: str,
    context: dict[str, Any],
) -> RecoveryAction:
    """Create a switch-profile action."""

    def execute() -> bool:
        context["profile"] = new_profile
        return True

    return RecoveryAction(
        name="switch_profile",
        description=f"Switch to profile '{new_profile}'",
        execute=execute,
        success_message=f"Switched to profile '{new_profile}'",
        failure_message=f"Profile '{new_profile}' also lacks permission",
        params={"new_profile": new_profile},
    )


def create_increase_timeout_action(
    current_ms: int,
    target_ms: int,
    context: dict[str, Any],
) -> RecoveryAction:
    """Create an increase-timeout action."""

    def execute() -> bool:
        context["timeout_ms"] = target_ms
        return True

    return RecoveryAction(
        name="increase_timeout",
        description=f"Increase timeout from {current_ms}ms to {target_ms}ms",
        execute=execute,
        success_message=f"Increased timeout to {target_ms}ms",
        failure_message="Cannot increase timeout further",
        params={"from_ms": current_ms, "to_ms": target_ms},
    )


__all__ = [
    "RecoveryAction",
    "RecoveryResult",
    "create_increase_timeout_action",
    "create_reduce_concurrency_action",
    "create_skip_service_action",
    "create_switch_profile_action",
    "create_wait_and_retry_action",
]
