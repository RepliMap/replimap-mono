"""
AWS Error Handling Module for RepliMap.

This module provides production-grade error classification for AWS API calls,
enabling intelligent retry decisions, circuit breaker integration, and
comprehensive observability.

Key Components:
- BotocoreErrorLoader: Dynamic error code loading with defensive fallback
- ServiceSpecificRules: Service and operation-aware rules (S3 hybrid strategy)
- ErrorClassifier: Context-aware error classification
- ErrorAction: Action enum (RETRY, FAIL, IGNORE, BACKOFF)

Example:
    from replimap.core.resilience.errors import ErrorClassifier, ErrorContext, ErrorAction

    classifier = ErrorClassifier()
    context = ErrorContext(
        service_name='s3',
        region='us-east-1',
        operation_name='ListObjectsV2',
    )

    try:
        await s3_client.list_objects_v2(Bucket='my-bucket')
    except ClientError as e:
        classification = classifier.classify(e, context)
        if classification.action == ErrorAction.RETRY:
            await asyncio.sleep(classification.suggested_delay_ms / 1000)
            # retry...

Note:
    This package extends the existing replimap.core.errors module (errors.py)
    with enhanced features. For backward compatibility, the original module's
    exports are preserved and accessible.
"""

from __future__ import annotations

from replimap.core.resilience.errors.classifier import (
    ErrorAction,
    ErrorClassification,
    ErrorClassifier,
    ErrorContext,
)
from replimap.core.resilience.errors.loader import BotocoreErrorLoader
from replimap.core.resilience.errors.rules import ServiceSpecificRules

__all__ = [
    # Enums and dataclasses
    "ErrorAction",
    "ErrorClassification",
    "ErrorContext",
    # Classes
    "ErrorClassifier",
    "BotocoreErrorLoader",
    "ServiceSpecificRules",
]
