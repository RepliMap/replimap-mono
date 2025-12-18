"""
Feature Gating for RepliMap.

Provides decorators and utilities for gating features based on plan tier.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from replimap.licensing.models import Feature, Plan

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class FeatureNotAvailableError(Exception):
    """Raised when a feature is not available in the current plan."""

    def __init__(
        self,
        feature: Feature | str,
        current_plan: Plan,
        required_plan: Plan | None = None,
    ) -> None:
        self.feature = feature
        self.current_plan = current_plan
        self.required_plan = required_plan

        message = f"Feature '{feature}' is not available in {current_plan} plan"
        if required_plan:
            message += f". Upgrade to {required_plan} or higher to unlock this feature."

        super().__init__(message)


class ResourceLimitExceededError(Exception):
    """Raised when resource limits are exceeded."""

    def __init__(
        self,
        limit_type: str,
        current: int,
        maximum: int,
        current_plan: Plan,
    ) -> None:
        self.limit_type = limit_type
        self.current = current
        self.maximum = maximum
        self.current_plan = current_plan

        message = (
            f"{limit_type} limit exceeded: {current}/{maximum} "
            f"(current plan: {current_plan})"
        )
        super().__init__(message)


def feature_gate(
    feature: Feature,
    fallback: R | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to gate a function behind a feature flag.

    Args:
        feature: The feature required to use this function
        fallback: Optional fallback value to return if feature is unavailable

    Returns:
        Decorated function that checks feature availability

    Example:
        @feature_gate(Feature.ASYNC_SCANNING)
        async def run_async_scan():
            ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            from replimap.licensing.manager import get_license_manager

            manager = get_license_manager()
            if not manager.current_features.has_feature(feature):
                if fallback is not None:
                    logger.debug(f"Feature {feature} not available, using fallback")
                    return fallback
                raise FeatureNotAvailableError(
                    feature=feature,
                    current_plan=manager.current_plan,
                    required_plan=_get_minimum_plan_for_feature(feature),
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_plan(
    minimum_plan: Plan,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to require a minimum plan tier.

    Args:
        minimum_plan: The minimum plan required

    Returns:
        Decorated function that checks plan tier

    Example:
        @require_plan(Plan.PRO)
        def generate_custom_template():
            ...
    """
    plan_order = [Plan.FREE, Plan.SOLO, Plan.PRO, Plan.TEAM, Plan.ENTERPRISE]

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            from replimap.licensing.manager import get_license_manager

            manager = get_license_manager()
            current_plan = manager.current_plan

            current_index = plan_order.index(current_plan)
            required_index = plan_order.index(minimum_plan)

            if current_index < required_index:
                raise FeatureNotAvailableError(
                    feature=func.__name__,
                    current_plan=current_plan,
                    required_plan=minimum_plan,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def check_resource_limit(
    resource_count: int,
    limit_type: str = "resources_per_scan",
) -> None:
    """
    Check if resource count is within plan limits.

    Args:
        resource_count: Number of resources to check
        limit_type: Type of limit to check

    Raises:
        ResourceLimitExceededError: If limit is exceeded
    """
    from replimap.licensing.manager import get_license_manager

    manager = get_license_manager()
    features = manager.current_features

    if limit_type == "resources_per_scan":
        max_limit = features.max_resources_per_scan
    elif limit_type == "scans_per_month":
        max_limit = features.max_scans_per_month
    elif limit_type == "aws_accounts":
        max_limit = features.max_aws_accounts
    else:
        logger.warning(f"Unknown limit type: {limit_type}")
        return

    if max_limit is not None and resource_count > max_limit:
        raise ResourceLimitExceededError(
            limit_type=limit_type,
            current=resource_count,
            maximum=max_limit,
            current_plan=manager.current_plan,
        )


def _get_minimum_plan_for_feature(feature: Feature) -> Plan | None:
    """Get the minimum plan that includes a feature."""
    from replimap.licensing.models import PLAN_FEATURES

    plan_order = [Plan.FREE, Plan.SOLO, Plan.PRO, Plan.TEAM, Plan.ENTERPRISE]

    for plan in plan_order:
        if PLAN_FEATURES[plan].has_feature(feature):
            return plan

    return None


def get_upgrade_prompt(feature: Feature, current_plan: Plan) -> str:
    """
    Generate a helpful upgrade prompt for a missing feature.

    Args:
        feature: The feature that's not available
        current_plan: The user's current plan

    Returns:
        Helpful upgrade message
    """
    required_plan = _get_minimum_plan_for_feature(feature)
    if required_plan is None:
        return f"Feature '{feature}' is not available in any plan."

    from replimap.licensing.models import get_plan_features

    required_features = get_plan_features(required_plan)
    price = required_features.price_monthly

    return (
        f"'{feature.value}' requires {required_plan.value} plan (${price}/month).\n"
        f"Upgrade at: https://replimap.io/upgrade"
    )


def is_feature_available(feature: Feature) -> bool:
    """
    Check if a feature is available in the current plan.

    Args:
        feature: The feature to check

    Returns:
        True if feature is available
    """
    from replimap.licensing.manager import get_license_manager

    manager = get_license_manager()
    return manager.current_features.has_feature(feature)


def get_available_features() -> list[Feature]:
    """Get all features available in the current plan."""
    from replimap.licensing.manager import get_license_manager

    manager = get_license_manager()
    return list(manager.current_features.features)


def get_unavailable_features() -> list[Feature]:
    """Get all features NOT available in the current plan."""
    from replimap.licensing.manager import get_license_manager

    manager = get_license_manager()
    all_features = set(Feature)
    available = manager.current_features.features
    return list(all_features - available)
