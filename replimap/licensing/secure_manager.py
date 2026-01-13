"""
Secure License Manager for RepliMap.

Security Changes from original manager.py:
- REMOVED: is_dev_mode() environment variable bypass
- ADDED: Ed25519 signature verification
- ADDED: Time validation
- ADDED: Proper error handling and logging

All license data comes from verified signatures only.
No local-only validation that can be bypassed.
"""

from __future__ import annotations

import logging
import os
import platform
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import httpx

from replimap.licensing.models import Feature, Plan, get_plan_features
from replimap.licensing.secure_models import (
    SECURE_PLAN_FEATURES,
    SECURE_PLAN_LIMITS,
    SecureLicenseData,
    SecureLicenseLimits,
)
from replimap.licensing.verifier import (
    LicenseExpiredError,
    LicenseVerificationError,
    LicenseVerifier,
)

if TYPE_CHECKING:
    from replimap.licensing.models import PlanFeatures

logger = logging.getLogger(__name__)

UTC = timezone.utc


class SecureLicenseError(Exception):
    """Secure license operation error."""

    pass


class SecureLicenseManager:
    """
    Manages license activation, verification, and feature access.

    Usage:
        manager = SecureLicenseManager()

        # Check current plan
        plan = manager.current_plan

        # Check feature access
        if manager.has_feature(Feature.AUDIT_EXPORT_PDF):
            export_pdf()

        # Activate license
        license_data = manager.activate("RM-SOLO-1234-ABCD")

        # Deactivate
        manager.deactivate()

    Security Model:
        - License comes from server (signed blob)
        - Verification uses Ed25519 (public key only)
        - No environment variable bypasses
        - Time validation prevents manipulation
    """

    LICENSE_FILE = Path.home() / ".replimap" / "license.key"
    API_BASE_URL = "https://api.replimap.io/v1"
    API_TIMEOUT = 30.0

    # Cache settings
    CACHE_DURATION = timedelta(minutes=5)

    def __init__(
        self,
        license_file: Optional[Path] = None,
        api_base_url: Optional[str] = None,
        verifier: Optional[LicenseVerifier] = None,
    ) -> None:
        """
        Initialize license manager.

        Args:
            license_file: Custom license file path (for testing)
            api_base_url: Custom API URL (for testing)
            verifier: Custom verifier (for testing)
        """
        self.license_file = license_file or self.LICENSE_FILE
        self.api_base_url = api_base_url or os.environ.get(
            "REPLIMAP_LICENSE_API", self.API_BASE_URL
        )
        self._verifier = verifier or LicenseVerifier()

        # In-memory cache
        self._cached_license: Optional[SecureLicenseData] = None
        self._cache_time: Optional[datetime] = None

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    @property
    def current_plan(self) -> Plan:
        """
        Get current subscription plan.

        Returns FREE if:
        - No license file
        - License invalid or expired
        - Verification fails

        SECURITY: No environment variable bypasses.
        """
        license_data = self._get_verified_license()

        if license_data is None:
            return Plan.FREE

        return license_data.plan

    @property
    def current_license(self) -> Optional[SecureLicenseData]:
        """Get current verified license data, or None."""
        return self._get_verified_license()

    @property
    def current_features(self) -> PlanFeatures:
        """Get the features for the current plan (legacy compatibility)."""
        return get_plan_features(self.current_plan)

    def has_feature(self, feature: Feature) -> bool:
        """
        Check if current license grants a feature.

        Args:
            feature: Feature to check

        Returns:
            True if feature is available
        """
        license_data = self._get_verified_license()

        if license_data:
            return license_data.has_feature(feature)

        # Fall back to FREE plan features
        return feature in SECURE_PLAN_FEATURES.get(Plan.FREE, set())

    def get_limits(self) -> SecureLicenseLimits:
        """Get current license limits."""
        license_data = self._get_verified_license()

        if license_data:
            return license_data.limits

        return SECURE_PLAN_LIMITS.get(Plan.FREE, SecureLicenseLimits())

    def check_limit(self, limit_name: str, value: int) -> bool:
        """
        Check if a value is within license limits.

        Args:
            limit_name: Name of limit (e.g., 'max_accounts')
            value: Current value to check

        Returns:
            True if within limits
        """
        limits = self.get_limits()
        return limits.check_limit(limit_name, value)

    def activate(self, license_key: str) -> SecureLicenseData:
        """
        Activate a license.

        Contacts server, retrieves signed blob, verifies, and saves.

        Args:
            license_key: License key (e.g., "RM-SOLO-1234-ABCD")

        Returns:
            Verified SecureLicenseData

        Raises:
            SecureLicenseError: Activation failed
        """
        logger.info(f"Activating license: {license_key[:10]}...")

        try:
            response = httpx.post(
                f"{self.api_base_url}/license/activate",
                json={
                    "license_key": license_key.upper().strip(),
                    "machine_info": self._get_machine_info(),
                    "cli_version": self._get_cli_version(),
                },
                timeout=self.API_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                license_blob = data.get("license_blob")

                if not license_blob:
                    raise SecureLicenseError("Server response missing license_blob")

                # Verify the blob before saving
                license_data = self._verifier.verify(license_blob)

                # Save to disk
                self._save_license_blob(license_blob)

                # Update cache
                self._cached_license = license_data
                self._cache_time = datetime.now(UTC)

                logger.info(f"License activated: {license_data.plan.value}")
                return license_data

            elif response.status_code == 400:
                error = response.json().get("error", "Invalid request")
                raise SecureLicenseError(f"Activation failed: {error}")

            elif response.status_code == 401:
                raise SecureLicenseError("Invalid license key")

            elif response.status_code == 403:
                error = response.json().get("error", "License not valid")
                raise SecureLicenseError(f"License rejected: {error}")

            elif response.status_code == 429:
                raise SecureLicenseError("Too many activation attempts. Please wait.")

            else:
                raise SecureLicenseError(
                    f"Activation failed: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            raise SecureLicenseError(f"Network error: {e}") from e
        except LicenseVerificationError as e:
            raise SecureLicenseError(f"License verification failed: {e}") from e

    def deactivate(self) -> None:
        """
        Deactivate current license.

        Removes license file and clears cache.
        """
        if self.license_file.exists():
            self.license_file.unlink()
            logger.info("License file removed")

        self._cached_license = None
        self._cache_time = None

        logger.info("License deactivated")

    def refresh(self) -> Optional[SecureLicenseData]:
        """
        Refresh license from server.

        Useful for checking updated limits or features.

        Returns:
            Updated license data, or None if no license
        """
        license_data = self._get_verified_license()

        if license_data is None:
            return None

        # Re-activate with existing key
        try:
            return self.activate(license_data.license_key)
        except SecureLicenseError as e:
            logger.warning(f"License refresh failed: {e}")
            return license_data

    def status(self) -> dict[str, Any]:
        """
        Get license status summary.

        Returns:
            Status dictionary for display
        """
        license_data = self._get_verified_license()

        if license_data is None:
            return {
                "status": "free",
                "plan": "Free",
                "message": "No license active. Using free tier.",
            }

        days_left = license_data.days_until_expiry()

        status: dict[str, Any] = {
            "status": "active",
            "plan": license_data.plan.value.title(),
            "email": license_data.email,
            "organization": license_data.organization,
            "license_key": self._mask_key(license_data.license_key),
            "expires_at": (
                license_data.expires_at.isoformat()
                if license_data.expires_at
                else "Never"
            ),
            "days_remaining": days_left,
        }

        if days_left is not None and days_left <= 30:
            status["warning"] = f"License expires in {days_left} days"

        return status

    def validate(self) -> tuple[str, str]:
        """
        Validate the current license.

        Returns:
            Tuple of (status, message)
        """
        license_data = self._get_verified_license()

        if license_data is None:
            return "valid", "Using free tier"

        if license_data.is_expired():
            return "expired", f"License expired at {license_data.expires_at}"

        return "valid", f"{license_data.plan.value} plan active"

    # ═══════════════════════════════════════════════════════════════════════
    # INTERNAL METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def _get_verified_license(self) -> Optional[SecureLicenseData]:
        """
        Get verified license from cache or disk.

        Returns None if:
        - No license file
        - Verification fails
        - License expired
        """
        # Check cache
        if self._is_cache_valid():
            return self._cached_license

        # Load from disk
        if not self.license_file.exists():
            return None

        try:
            license_blob = self.license_file.read_text().strip()
            license_data = self._verifier.verify(license_blob)

            # Update cache
            self._cached_license = license_data
            self._cache_time = datetime.now(UTC)

            return license_data

        except LicenseExpiredError:
            logger.info("License has expired")
            return None
        except LicenseVerificationError as e:
            logger.warning(f"License verification failed: {e}")
            return None

    def _is_cache_valid(self) -> bool:
        """Check if in-memory cache is still valid."""
        if self._cached_license is None or self._cache_time is None:
            return False

        age = datetime.now(UTC) - self._cache_time
        if age > self.CACHE_DURATION:
            return False

        # Also check expiration
        if self._cached_license.is_expired():
            return False

        return True

    def _save_license_blob(self, blob: str) -> None:
        """Save license blob to disk."""
        self.license_file.parent.mkdir(parents=True, exist_ok=True)
        self.license_file.write_text(blob)

        # Secure permissions (owner read/write only)
        try:
            os.chmod(self.license_file, 0o600)
        except OSError:
            pass  # Windows may not support

    def _get_machine_info(self) -> dict[str, str]:
        """Get machine info for activation request."""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "platform_release": platform.release(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "machine": platform.machine(),
        }

    def _get_cli_version(self) -> str:
        """Get CLI version."""
        try:
            from replimap import __version__

            return __version__
        except ImportError:
            return "unknown"

    @staticmethod
    def _mask_key(key: str) -> str:
        """Mask license key for display."""
        if len(key) <= 8:
            return "*" * len(key)
        return key[:4] + "*" * (len(key) - 8) + key[-4:]


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════

_secure_license_manager: Optional[SecureLicenseManager] = None


def get_secure_license_manager() -> SecureLicenseManager:
    """Get singleton SecureLicenseManager instance."""
    global _secure_license_manager
    if _secure_license_manager is None:
        _secure_license_manager = SecureLicenseManager()
    return _secure_license_manager


def set_secure_license_manager(manager: SecureLicenseManager) -> None:
    """Set the global secure license manager instance (for testing)."""
    global _secure_license_manager
    _secure_license_manager = manager


def require_feature(feature: Feature):
    """
    Decorator to require a feature for a function.

    Usage:
        @require_feature(Feature.AUDIT_EXPORT_PDF)
        def export_pdf():
            ...
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_secure_license_manager()
            if not manager.has_feature(feature):
                plan = manager.current_plan
                raise SecureLicenseError(
                    f"Feature '{feature.value}' requires a higher plan. "
                    f"Current plan: {plan.value}"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_plan(min_plan: Plan):
    """
    Decorator to require a minimum plan.

    Usage:
        @require_plan(Plan.TEAM)
        def team_only_feature():
            ...
    """
    plan_order = [Plan.FREE, Plan.SOLO, Plan.PRO, Plan.TEAM, Plan.ENTERPRISE]

    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_secure_license_manager()
            current = manager.current_plan

            current_idx = plan_order.index(current)
            required_idx = plan_order.index(min_plan)

            if current_idx < required_idx:
                raise SecureLicenseError(
                    f"This feature requires {min_plan.value} plan or higher. "
                    f"Current plan: {current.value}"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator
