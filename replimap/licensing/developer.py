"""
Developer license management for internal testing.

Replaces the insecure REPLIMAP_DEV_MODE environment variable.

Security Model:
- Developer licenses are signed by the server (same as regular licenses)
- Requires email verification (internal domains only)
- Short expiration (7 days)
- Automatic renewal available
- Full audit trail on server

Benefits:
- No hardcoded bypass in production code
- Audit trail of developer usage
- Can be revoked if needed
- Same verification path as production
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

UTC = timezone.utc


class DeveloperLicenseError(Exception):
    """Developer license error."""

    pass


class DeveloperLicense:
    """
    Developer license for internal testing.

    Usage:
        # Request developer license (one-time)
        DeveloperLicense.request("developer@replimap.dev")

        # Check if in test environment
        if DeveloperLicense.is_test_environment():
            # Running in pytest
    """

    # Allowed email domains for developer licenses
    ALLOWED_DOMAINS: set[str] = {
        "replimap.dev",
        "replimap.io",
        # Add your internal domains here
    }

    # Developer license duration
    DEV_LICENSE_DURATION = timedelta(days=7)

    # API endpoint
    API_BASE_URL = "https://api.replimap.io/v1"

    @classmethod
    def request(cls, email: str) -> str:
        """
        Request a developer license.

        Args:
            email: Developer email (must be from allowed domain)

        Returns:
            License key for activation

        Raises:
            DeveloperLicenseError: If request fails
        """
        import httpx

        # Validate email domain
        domain = email.split("@")[-1].lower()
        if domain not in cls.ALLOWED_DOMAINS:
            raise DeveloperLicenseError(
                f"Developer license requires email from: {cls.ALLOWED_DOMAINS}. "
                f"Got: {domain}"
            )

        logger.info(f"Requesting developer license for {email}")

        try:
            response = httpx.post(
                f"{cls.API_BASE_URL}/license/developer",
                json={
                    "email": email,
                    "purpose": "development_testing",
                    "duration_days": cls.DEV_LICENSE_DURATION.days,
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                license_key = data.get("license_key")

                logger.info(f"Developer license issued: {license_key[:10]}...")
                return license_key

            elif response.status_code == 400:
                error = response.json().get("error", "Invalid request")
                raise DeveloperLicenseError(f"Request failed: {error}")

            elif response.status_code == 403:
                raise DeveloperLicenseError(
                    "Email domain not authorized for developer licenses"
                )

            elif response.status_code == 429:
                raise DeveloperLicenseError(
                    "Too many requests. Please wait before requesting again."
                )

            else:
                raise DeveloperLicenseError(
                    f"Request failed: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            raise DeveloperLicenseError(f"Network error: {e}") from e

    @classmethod
    def is_test_environment(cls) -> bool:
        """
        Check if running in a test environment.

        Returns True ONLY if running under pytest.
        This does NOT grant license bypass - tests should use
        mock licenses or test fixtures.

        This is NOT a security bypass, just a detection mechanism.
        """
        return "pytest" in sys.modules

    @classmethod
    def get_test_license_data(cls) -> dict:
        """
        Get test license data for use in pytest fixtures.

        Returns:
            Dictionary that can be used to create test SecureLicenseData

        Note: This creates UNSIGNED test data.
        Only use in tests with mocked verification.
        """
        if not cls.is_test_environment():
            raise DeveloperLicenseError(
                "get_test_license_data() can only be called in test environment"
            )

        from replimap.licensing.models import Feature, Plan

        now = datetime.now(UTC)

        return {
            "v": 1,
            "kid": "test-key-001",
            "lic": "TEST-DEV-LICENSE",
            "plan": Plan.ENTERPRISE.value,
            "email": "test@replimap.dev",
            "org": "RepliMap Test",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=365)).timestamp()),
            "features": [f.value for f in Feature],
            "limits": {
                "max_accounts": -1,
                "max_regions": -1,
                "max_resources_per_scan": -1,
                "max_concurrent_scans": -1,
                "max_scans_per_day": -1,
                "offline_grace_days": 365,
            },
            "nonce": "test-nonce-12345",
        }


# ═══════════════════════════════════════════════════════════════════════════
# PYTEST FIXTURES HELPER
# ═══════════════════════════════════════════════════════════════════════════


def get_mock_enterprise_license():
    """
    Get a mock enterprise license for testing.

    Returns a tuple of (mock_manager, mock_license_data) that can be used
    in tests to simulate enterprise access without actual license verification.

    Usage in conftest.py:
        @pytest.fixture
        def enterprise_license(mocker):
            mock_manager, _ = get_mock_enterprise_license()
            mocker.patch(
                'replimap.licensing.secure_manager.get_secure_license_manager',
                return_value=mock_manager
            )
            return mock_manager
    """
    from unittest.mock import MagicMock

    from replimap.licensing.models import Plan
    from replimap.licensing.secure_manager import SecureLicenseManager
    from replimap.licensing.secure_models import SecureLicenseData, SecureLicenseLimits

    mock_manager = MagicMock(spec=SecureLicenseManager)
    mock_manager.current_plan = Plan.ENTERPRISE
    mock_manager.has_feature.return_value = True
    mock_manager.get_limits.return_value = SecureLicenseLimits(
        max_accounts=-1,
        max_regions=-1,
        max_resources_per_scan=-1,
        max_concurrent_scans=-1,
        max_scans_per_day=-1,
        offline_grace_days=365,
    )
    mock_manager.check_limit.return_value = True

    # Create mock license data
    now = datetime.now(UTC)
    mock_license = MagicMock(spec=SecureLicenseData)
    mock_license.plan = Plan.ENTERPRISE
    mock_license.is_expired.return_value = False
    mock_license.has_feature.return_value = True

    mock_manager.current_license = mock_license

    return mock_manager, mock_license


def get_mock_free_license():
    """
    Get a mock free license for testing.

    Returns a tuple of (mock_manager, None) that simulates free tier access.

    Usage in conftest.py:
        @pytest.fixture
        def free_license(mocker):
            mock_manager, _ = get_mock_free_license()
            mocker.patch(
                'replimap.licensing.secure_manager.get_secure_license_manager',
                return_value=mock_manager
            )
            return mock_manager
    """
    from unittest.mock import MagicMock

    from replimap.licensing.models import Plan
    from replimap.licensing.secure_manager import SecureLicenseManager
    from replimap.licensing.secure_models import (
        SECURE_PLAN_FEATURES,
        SECURE_PLAN_LIMITS,
    )

    mock_manager = MagicMock(spec=SecureLicenseManager)
    mock_manager.current_plan = Plan.FREE
    mock_manager.has_feature.side_effect = lambda f: f in SECURE_PLAN_FEATURES[Plan.FREE]
    mock_manager.get_limits.return_value = SECURE_PLAN_LIMITS[Plan.FREE]
    mock_manager.check_limit.side_effect = lambda name, val: SECURE_PLAN_LIMITS[
        Plan.FREE
    ].check_limit(name, val)
    mock_manager.current_license = None

    return mock_manager, None
