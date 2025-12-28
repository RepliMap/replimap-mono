"""
Cache module for RepliMap.

Provides caching and persistence capabilities:
- Historical snapshots (Time Machine)
- 30-day resource snapshot retention
- Point-in-time comparison
- Audit evidence chain support
"""

from replimap.cache.snapshots import (
    AuditEvent,
    AuditEventType,
    AuditTrail,
    ResourceSnapshot,
    SnapshotComparison,
    SnapshotDiff,
    SnapshotManager,
    SnapshotMetadata,
    compare_snapshots,
    create_snapshot_manager,
)

__all__ = [
    # Core classes
    "SnapshotManager",
    "ResourceSnapshot",
    "SnapshotMetadata",
    # Comparison
    "SnapshotComparison",
    "SnapshotDiff",
    "compare_snapshots",
    # Audit trail
    "AuditTrail",
    "AuditEvent",
    "AuditEventType",
    # Factory
    "create_snapshot_manager",
]
