"""
Decision Management Module.

Tracks user decisions with TTL (Time To Live) support to prevent
zombie configurations that persist forever without review.

Key Features:
- All decisions saved to YAML (human-readable, diffable)
- Suppress decisions expire in 30 days
- Extraction decisions expire in 90 days
- Permanent decisions require explicit --permanent flag
- Expired decisions trigger re-confirmation
"""

from replimap.decisions.manager import DecisionManager
from replimap.decisions.models import Decision, DecisionManifest, DecisionType

__all__ = [
    "Decision",
    "DecisionManager",
    "DecisionManifest",
    "DecisionType",
]
