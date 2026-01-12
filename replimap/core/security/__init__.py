"""
Security module for RepliMap.

Provides tools for:
- Detecting and preventing sensitive data leakage in generated IaC
- Graph-aware IAM least privilege policy generation
- Secure credential caching with enforced file permissions
- Centralized AWS session management with credential refresh
- Credential health checks and security recommendations

Credential Security Components:
- SecureStorage: Atomic file operations with pre-write permissions
- SessionManager: Singleton for AWS session lifecycle management
- CredentialChecker: Proactive credential health warnings
"""

from .credential_checker import CredentialChecker
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
from .scrubber import SecretScrubber
from .session_manager import SessionManager
from .storage import SecureStorage

__all__ = [
    # Credential security
    "CredentialChecker",
    "SecureStorage",
    "SessionManager",
    # Secret scrubbing
    "SecretScrubber",
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
