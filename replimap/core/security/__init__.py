"""
Security module for RepliMap.

Provides tools for:
- Detecting and preventing sensitive data leakage in generated IaC
- Graph-aware IAM least privilege policy generation
"""

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

__all__ = [
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
