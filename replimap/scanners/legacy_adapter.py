"""
Legacy scanner adapter using Strangler Fig pattern.

This adapter wraps legacy BaseScanner and AsyncBaseScanner instances with modern
resilience features (circuit breaker, retry, rate limiting) without
requiring code changes to the legacy scanners.

Migration Strategy:
1. Phase 1: Wrap all legacy scanners with this adapter
2. Phase 2: Migrate high-traffic scanners to UnifiedScannerBase
3. Phase 3: Remove adapter and legacy base class

Usage:
    # Automatic wrapping at startup
    scanners = discover_scanners()
    wrapped = wrap_legacy_scanners(scanners)

    # Or manual wrapping
    legacy = VPCScanner(session, region, account_id)
    wrapped = LegacyScannerAdapter(legacy)
    result = await wrapped.scan(graph)

The adapter provides:
1. Circuit breaker protection (prevents cascading failures)
2. Error classification for intelligent retry
3. Deprecation warnings (encourage migration)
4. Full API compatibility (drop-in replacement)
"""

from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING, Any, TypeVar

from replimap.core.errors.classifier import ErrorClassifier, ErrorContext
from replimap.core.resilience.circuit_breaker import (
    CircuitBreakerRegistry,
    CircuitOpenError,
)
from replimap.scanners.unified_base import ScanResult, UnifiedScannerBase

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LegacyScannerAdapter:
    """
    Adapter that wraps legacy scanners with resilience features.

    This provides:
    1. Circuit breaker protection
    2. Error classification
    3. Deprecation warnings

    The adapter maintains external API compatibility while adding
    internal resilience.
    """

    # Mapping of scanner name keywords to AWS service names
    SERVICE_MAPPING: dict[str, str] = {
        "vpc": "ec2",
        "ec2": "ec2",
        "s3": "s3",
        "rds": "rds",
        "iam": "iam",
        "lambda": "lambda",
        "dynamodb": "dynamodb",
        "sqs": "sqs",
        "sns": "sns",
        "networking": "ec2",
        "compute": "ec2",
        "storage": "s3",
        "elasticache": "elasticache",
        "monitoring": "cloudwatch",
        "messaging": "sqs",
    }

    def __init__(
        self,
        legacy_scanner: Any,
        error_classifier: ErrorClassifier | None = None,
        suppress_deprecation_warning: bool = False,
    ) -> None:
        """
        Wrap a legacy scanner.

        Args:
            legacy_scanner: Instance of BaseScanner or AsyncBaseScanner subclass
            error_classifier: Optional custom error classifier
            suppress_deprecation_warning: If True, don't emit deprecation warning
        """
        self._legacy = legacy_scanner
        self._classifier = error_classifier or ErrorClassifier()
        self._service_name = self._infer_service_name()

        # Emit deprecation warning
        if not suppress_deprecation_warning:
            warnings.warn(
                f"{type(legacy_scanner).__name__} uses deprecated scanner base class. "
                f"Migrate to UnifiedScannerBase for full resilience support. "
                f"See docs/migration/unified-scanner.md",
                DeprecationWarning,
                stacklevel=2,
            )

    def _infer_service_name(self) -> str:
        """Infer AWS service name from scanner class name."""
        class_name = type(self._legacy).__name__.lower()

        for keyword, service in self.SERVICE_MAPPING.items():
            if keyword in class_name:
                return service

        return "unknown"

    @property
    def region(self) -> str:
        """Get region from legacy scanner."""
        return getattr(self._legacy, "region", "unknown")

    @property
    def account_id(self) -> str:
        """Get account ID from legacy scanner."""
        return getattr(self._legacy, "account_id", "unknown")

    @property
    def service_name(self) -> str:
        """Get inferred service name."""
        return self._service_name

    async def scan(self, graph: GraphEngine) -> ScanResult:
        """
        Run legacy scanner with circuit breaker protection.

        Args:
            graph: GraphEngine to populate

        Returns:
            ScanResult with statistics
        """
        result = ScanResult(scanner_name=type(self._legacy).__name__)

        # Get circuit breaker for this service
        breaker = await CircuitBreakerRegistry.get_breaker(
            service_name=self._service_name,
            region=self.region,
            operation_name="Scan",  # Generic operation
        )

        # Check circuit state
        if breaker.state.name == "OPEN":
            logger.warning(
                f"Circuit open for {self._service_name}:{self.region}, "
                f"skipping {type(self._legacy).__name__}"
            )
            result.circuit_open = True
            result.skipped_regions.append(self.region)
            raise CircuitOpenError(
                f"Circuit breaker for {self._service_name}:{self.region} is open"
            )

        # Create error context
        context = ErrorContext(
            service_name=self._service_name,
            region=self.region,
            operation_name="Scan",
        )

        try:
            # Call the legacy scanner's scan method
            # Handle both sync and async scanners
            if hasattr(self._legacy, "scan_async"):
                await self._legacy.scan_async(graph)
            elif hasattr(self._legacy, "scan"):
                scan_method = self._legacy.scan
                # Check if it's async
                import asyncio

                if asyncio.iscoroutinefunction(scan_method):
                    await scan_method(graph)
                else:
                    # Run sync scanner in executor
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, scan_method, graph)
            else:
                raise AttributeError(
                    f"Legacy scanner {type(self._legacy).__name__} has no scan method"
                )

            breaker.record_result(success=True)
            return result

        except CircuitOpenError:
            # Re-raise circuit errors
            raise

        except Exception as e:
            # Classify error
            classification = self._classifier.classify(e, context)

            # Record in circuit breaker
            breaker.record_result(success=False, classification=classification)

            result.errors.append(str(e))

            # Re-raise
            raise

    def scan_sync(self, graph: GraphEngine) -> ScanResult:
        """
        Synchronous scan for legacy code paths.

        Args:
            graph: GraphEngine to populate

        Returns:
            ScanResult with statistics
        """
        result = ScanResult(scanner_name=type(self._legacy).__name__)

        # Get circuit breaker for this service (sync version)
        breaker = CircuitBreakerRegistry.get_breaker_sync(
            service_name=self._service_name,
            region=self.region,
            operation_name="Scan",
        )

        # Check circuit state
        if breaker.state.name == "OPEN":
            logger.warning(
                f"Circuit open for {self._service_name}:{self.region}, "
                f"skipping {type(self._legacy).__name__}"
            )
            result.circuit_open = True
            result.skipped_regions.append(self.region)
            raise CircuitOpenError(
                f"Circuit breaker for {self._service_name}:{self.region} is open"
            )

        context = ErrorContext(
            service_name=self._service_name,
            region=self.region,
            operation_name="Scan",
        )

        try:
            self._legacy.scan(graph)
            breaker.record_result(success=True)
            return result

        except CircuitOpenError:
            raise

        except Exception as e:
            classification = self._classifier.classify(e, context)
            breaker.record_result(success=False, classification=classification)
            result.errors.append(str(e))
            raise

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to legacy scanner."""
        return getattr(self._legacy, name)


def wrap_legacy_scanners(
    scanners: list[Any],
    unified_base_class: type | None = None,
    suppress_warnings: bool = False,
) -> list[Any]:
    """
    Automatically wrap legacy scanners with adapter.

    Args:
        scanners: List of scanner instances
        unified_base_class: Optional class to check against (skip if already unified)
        suppress_warnings: If True, suppress deprecation warnings

    Returns:
        List with legacy scanners wrapped
    """
    unified_base = unified_base_class or UnifiedScannerBase
    wrapped: list[Any] = []

    for scanner in scanners:
        # Check if already a modern scanner
        if isinstance(scanner, unified_base):
            wrapped.append(scanner)
            continue

        # Check if already wrapped
        if isinstance(scanner, LegacyScannerAdapter):
            wrapped.append(scanner)
            continue

        # Check if it's a legacy scanner (has certain attributes)
        if hasattr(scanner, "scan") and (
            hasattr(scanner, "get_client") or hasattr(scanner, "_session")
        ):
            logger.info(f"Wrapping legacy scanner: {type(scanner).__name__}")
            wrapped.append(
                LegacyScannerAdapter(
                    scanner,
                    suppress_deprecation_warning=suppress_warnings,
                )
            )
        else:
            wrapped.append(scanner)

    return wrapped


def add_deprecation_to_base_class(base_class: type) -> None:
    """
    Add deprecation warning to BaseScanner/AsyncBaseScanner.__init__.

    Call this at application startup to warn on any legacy scanner creation.

    Args:
        base_class: The legacy base class to patch
    """
    original_init = base_class.__init__

    def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            f"{self.__class__.__name__} inherits from deprecated {base_class.__name__}. "
            f"Migrate to UnifiedScannerBase. See docs/migration/unified-scanner.md",
            DeprecationWarning,
            stacklevel=2,
        )
        original_init(self, *args, **kwargs)

    base_class.__init__ = patched_init
