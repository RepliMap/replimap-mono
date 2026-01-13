"""
Recovery Module - Silent error recovery and gray zone resolution.

Provides intelligent error recovery that:
- Silently handles safe operations (timeout, retry, concurrency)
- Notifies user of caution-level operations (skip service)
- Confirms or fails fast for sensitive operations (identity switch)
"""

from replimap.recovery.actions import RecoveryAction, RecoveryResult
from replimap.recovery.engine import SilentRecoveryEngine
from replimap.recovery.gray_zone import GrayZoneResolver

__all__ = [
    "GrayZoneResolver",
    "RecoveryAction",
    "RecoveryResult",
    "SilentRecoveryEngine",
]
