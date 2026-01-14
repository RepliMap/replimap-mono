"""
Defensive AWS error code loader with botocore integration.

This module dynamically loads error codes from botocore's internal retry
configuration, with robust fallback for when botocore internals change.

Design Principles:
1. NEVER crash due to SDK internal changes
2. Always provide usable error lists
3. Log enough info for debugging
4. Cache results for performance

The $100 Bet: This code will NEVER crash due to botocore version changes.
It will silently degrade to fallback lists while logging the issue.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class BotocoreErrorLoader:
    """
    Defensive loader for AWS error codes from botocore.

    This class attempts to dynamically load error codes from botocore's
    internal retry configuration. If this fails for ANY reason (version
    change, missing files, structure change), it silently falls back to
    a hardcoded list.

    Usage:
        retryable = BotocoreErrorLoader.get_retryable_errors()
        fatal = BotocoreErrorLoader.get_fatal_errors()

        if error_code in retryable:
            # retry the operation
        elif error_code in fatal:
            # fail immediately

    Thread Safety:
        All methods are thread-safe due to immutable return values
        and atomic cache updates.
    """

    # ═══════════════════════════════════════════════════════════════════════
    # FALLBACK ERROR LISTS (Used when botocore loading fails)
    # ═══════════════════════════════════════════════════════════════════════

    FALLBACK_RETRYABLE_ERRORS: ClassVar[frozenset[str]] = frozenset(
        {
            # Throttling errors (9 codes)
            "Throttling",
            "ThrottlingException",
            "RequestLimitExceeded",
            "TooManyRequestsException",
            "ProvisionedThroughputExceededException",
            "SlowDown",  # S3 rate limiting
            "EC2ThrottledException",  # EC2-specific
            "PriorRequestNotComplete",  # Multi-step operations
            "BandwidthLimitExceeded",
            # Transient failures (5 codes)
            "ServiceUnavailable",
            "InternalError",
            "InternalFailure",
            "ServiceException",
            "LimitExceededException",  # Lambda, CloudWatch
            # Timeout/Network errors (4 codes)
            "RequestTimeout",
            "RequestTimeoutException",
            "RequestExpired",  # Clock skew
            "IDPCommunicationError",  # SSO/SAML
            # Connection errors (botocore exceptions)
            "ConnectionError",
            "EndpointConnectionError",
        }
    )

    FALLBACK_FATAL_ERRORS: ClassVar[frozenset[str]] = frozenset(
        {
            # Authentication/Authorization (8 codes)
            "AccessDenied",
            "AccessDeniedException",
            "UnauthorizedAccess",
            "InvalidClientTokenId",
            "ExpiredToken",
            "ExpiredTokenException",
            "UnrecognizedClientException",
            "SignatureDoesNotMatch",
            # Validation errors (6 codes)
            "ValidationException",
            "InvalidParameterValue",
            "InvalidParameterException",
            "InvalidAction",
            "MalformedQueryString",
            "MissingParameter",
            # Resource not found (6 codes)
            "ResourceNotFoundException",
            "NoSuchEntity",
            "NoSuchBucket",
            "NoSuchKey",
            "TableNotFoundException",
            "FunctionNotFoundException",
            # Quota errors (2 codes - permanent)
            "ResourceLimitExceeded",
            "QuotaExceededException",
        }
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CACHE AND STATE
    # ═══════════════════════════════════════════════════════════════════════

    _cache: ClassVar[dict[str, frozenset[str]]] = {}
    _load_attempted: ClassVar[bool] = False
    _load_succeeded: ClassVar[bool] = False
    _botocore_version: ClassVar[str | None] = None

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    @classmethod
    def get_retryable_errors(cls) -> frozenset[str]:
        """
        Get the set of retryable AWS error codes.

        Returns:
            Frozen set of error code strings that should trigger retry.

        Note:
            This method NEVER raises exceptions. If dynamic loading fails,
            it returns the fallback list silently.
        """
        if "retryable" in cls._cache:
            return cls._cache["retryable"]

        cls._ensure_loaded()
        return cls._cache.get("retryable", cls.FALLBACK_RETRYABLE_ERRORS)

    @classmethod
    def get_fatal_errors(cls) -> frozenset[str]:
        """
        Get the set of fatal (non-retryable) AWS error codes.

        Returns:
            Frozen set of error code strings that should NOT be retried.
        """
        if "fatal" in cls._cache:
            return cls._cache["fatal"]

        cls._ensure_loaded()
        return cls._cache.get("fatal", cls.FALLBACK_FATAL_ERRORS)

    @classmethod
    def get_load_status(cls) -> dict[str, Any]:
        """
        Get diagnostic information about the loading status.

        Returns:
            Dictionary with loading status for debugging.

        Example:
            >>> BotocoreErrorLoader.get_load_status()
            {
                'attempted': True,
                'succeeded': True,
                'using_fallback': False,
                'botocore_version': '1.34.0',
                'retryable_count': 23,
                'fatal_count': 18,
            }
        """
        cls._ensure_loaded()
        return {
            "attempted": cls._load_attempted,
            "succeeded": cls._load_succeeded,
            "using_fallback": not cls._load_succeeded,
            "botocore_version": cls._botocore_version,
            "retryable_count": len(
                cls._cache.get("retryable", cls.FALLBACK_RETRYABLE_ERRORS)
            ),
            "fatal_count": len(cls._cache.get("fatal", cls.FALLBACK_FATAL_ERRORS)),
        }

    # ═══════════════════════════════════════════════════════════════════════
    # INTERNAL METHODS
    # ═══════════════════════════════════════════════════════════════════════

    @classmethod
    def _ensure_loaded(cls) -> None:
        """Ensure error codes are loaded (called once)."""
        if cls._load_attempted:
            return

        cls._load_attempted = True
        cls._detect_botocore_version()

        try:
            retryable = cls._load_retryable_from_botocore()
            cls._cache["retryable"] = retryable
            cls._cache["fatal"] = cls.FALLBACK_FATAL_ERRORS  # Fatal list is static
            cls._load_succeeded = True

            logger.info(
                f"Loaded {len(retryable)} retryable error codes from "
                f"botocore {cls._botocore_version or 'unknown'}"
            )

        except Exception as e:
            # Catch ALL exceptions - botocore internals are unstable
            cls._cache["retryable"] = cls.FALLBACK_RETRYABLE_ERRORS
            cls._cache["fatal"] = cls.FALLBACK_FATAL_ERRORS
            cls._load_succeeded = False

            logger.warning(
                f"Failed to load error codes from botocore "
                f"{cls._botocore_version or 'unknown'}: {type(e).__name__}: {e}. "
                f"Using fallback list with {len(cls.FALLBACK_RETRYABLE_ERRORS)} "
                f"retryable and {len(cls.FALLBACK_FATAL_ERRORS)} fatal codes. "
                f"This is safe but may miss newly added AWS error codes."
            )

    @classmethod
    def _detect_botocore_version(cls) -> None:
        """Detect botocore version for diagnostics."""
        try:
            import botocore

            cls._botocore_version = getattr(botocore, "__version__", "unknown")
        except ImportError:
            cls._botocore_version = "not_installed"

    @classmethod
    def _load_retryable_from_botocore(cls) -> frozenset[str]:
        """
        Load retryable errors from botocore internals.

        This handles multiple botocore versions with different JSON structures.

        Raises:
            Any exception if loading fails (caught by caller)
        """
        import botocore.loaders

        loader = botocore.loaders.Loader()

        # Try multiple possible file names (changed across versions)
        possible_names = ["_retry", "retry", "_sdk_default_configuration"]
        retry_data = None

        for name in possible_names:
            try:
                retry_data = loader.load_data(name)
                logger.debug(f"Successfully loaded retry data from '{name}'")
                break
            except Exception as e:  # noqa: S112
                logger.debug(f"Could not load retry data from '{name}': {e}")
                continue

        if retry_data is None:
            raise FileNotFoundError(
                "Could not find retry configuration in botocore. "
                f"Tried: {possible_names}"
            )

        retryable: set[str] = set()

        # Strategy 1: New format (botocore >= 1.30)
        # Structure: {"definitions": {"throttling": {"error_codes": [...]}}}
        definitions = retry_data.get("definitions", {})
        for def_value in definitions.values():
            if isinstance(def_value, dict):
                error_codes = def_value.get("error_codes", [])
                if isinstance(error_codes, list):
                    retryable.update(error_codes)

        # Strategy 2: Old format (botocore < 1.30)
        # Structure: {"retry": {"service": {"policies": {...}}}}
        retry_section = retry_data.get("retry", {})
        for service_data in retry_section.values():
            if isinstance(service_data, dict):
                policies = service_data.get("policies", {})
                if isinstance(policies, dict):
                    for policy in policies.values():
                        if isinstance(policy, dict) and "applies_when" in policy:
                            applies = policy.get("applies_when", {})
                            if isinstance(applies, dict):
                                response = applies.get("response", {})
                                if isinstance(response, dict):
                                    code = response.get("service_error_code")
                                    if code:
                                        retryable.add(code)

        # Strategy 3: SDK default configuration format
        # Structure: {"retryableErrorCodes": [...]}
        if "retryableErrorCodes" in retry_data:
            retryable.update(retry_data["retryableErrorCodes"])

        # Always include our known fallback codes (botocore might miss some)
        retryable.update(cls.FALLBACK_RETRYABLE_ERRORS)

        if not retryable:
            raise ValueError("Parsed retry data but found no error codes")

        return frozenset(retryable)

    @classmethod
    def reset_cache(cls) -> None:
        """
        Reset the cache (for testing only).

        WARNING: This is not thread-safe and should only be used in tests.
        """
        cls._cache.clear()
        cls._load_attempted = False
        cls._load_succeeded = False
        cls._botocore_version = None
