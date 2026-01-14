"""
Security module for RepliMap.

Provides tools for:
- Detecting and preventing sensitive data leakage in generated IaC
- Graph-aware IAM least privilege policy generation
- Secure credential caching with enforced file permissions
- Centralized AWS session management with credential refresh
- Credential health checks and security recommendations
- Sovereign-grade data sanitization with deterministic redaction
- Drift detection for sanitized configurations

Credential Security Components:
- SecureStorage: Atomic file operations with pre-write permissions
- SessionManager: Singleton for AWS session lifecycle management
- CredentialChecker: Proactive credential health warnings

Data Sanitization Components:
- DeterministicRedactor: HMAC-based redaction with instance-level salt
- SensitivePatternLibrary: Comprehensive secret detection patterns
- GlobalSanitizer: Recursive sanitization with depth/cycle protection
- DriftDetector: Configuration drift detection for redacted values
"""

from .credential_checker import CredentialChecker
from .drift import DriftDetector, DriftItem, DriftResult, DriftType
from .global_sanitizer import (
    GlobalSanitizer,
    SanitizationResult,
    sanitize_resource_config,
)
from .iam_generator import (
    AccessRole,
    ARNBuilder,
    GraphAwareIAMGenerator,
    IAMPolicy,
    IAMStatement,
    IntentAwareActionMapper,
    PolicyOptimizer,
    PolicyScope,
    ResourceBoundary,
    SafeResourceCompressor,
    TraversalController,
)
from .patterns import SensitivePattern, SensitivePatternLibrary, Severity
from .redactor import DeterministicRedactor
from .scrubber import SecretScrubber
from .session_manager import SessionManager
from .storage import SecureStorage

__all__ = [
    # Credential security
    "CredentialChecker",
    "SecureStorage",
    "SessionManager",
    # Secret scrubbing (legacy)
    "SecretScrubber",
    # Data sanitization (Sovereign Grade)
    "DeterministicRedactor",
    "SensitivePatternLibrary",
    "SensitivePattern",
    "Severity",
    "GlobalSanitizer",
    "SanitizationResult",
    "sanitize_resource_config",
    # Drift detection
    "DriftDetector",
    "DriftType",
    "DriftItem",
    "DriftResult",
    # IAM generation
    "AccessRole",
    "ARNBuilder",
    "GraphAwareIAMGenerator",
    "IAMPolicy",
    "IAMStatement",
    "IntentAwareActionMapper",
    "PolicyOptimizer",
    "PolicyScope",
    "ResourceBoundary",
    "SafeResourceCompressor",
    "TraversalController",
]
