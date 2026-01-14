"""
Historical Snapshots (Time Machine) for RepliMap.

Provides point-in-time infrastructure snapshots with:
- 30-day resource snapshot retention
- Point-in-time comparison
- Audit evidence chain support
- Diff generation between snapshots

This enables infrastructure time travel, compliance auditing,
and understanding how infrastructure evolved over time.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.core import GraphEngine
    from replimap.core.models import ResourceNode

logger = logging.getLogger(__name__)


# Default retention period (30 days)
DEFAULT_RETENTION_DAYS = 30

# Maximum snapshots to keep (prevents unbounded growth)
MAX_SNAPSHOTS = 1000


class AuditEventType(str, Enum):
    """Types of audit events."""

    SNAPSHOT_CREATED = "snapshot_created"
    SNAPSHOT_DELETED = "snapshot_deleted"
    SNAPSHOT_COMPARED = "snapshot_compared"
    RESOURCE_ADDED = "resource_added"
    RESOURCE_MODIFIED = "resource_modified"
    RESOURCE_REMOVED = "resource_removed"
    RETENTION_CLEANUP = "retention_cleanup"

    def __str__(self) -> str:
        return self.value


@dataclass
class AuditEvent:
    """An event in the audit trail."""

    event_type: AuditEventType
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)
    actor: str = "system"
    snapshot_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "actor": self.actor,
            "snapshot_id": self.snapshot_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEvent:
        """Create from dictionary."""
        return cls(
            event_type=AuditEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            details=data.get("details", {}),
            actor=data.get("actor", "system"),
            snapshot_id=data.get("snapshot_id"),
        )


@dataclass
class AuditTrail:
    """Audit trail for compliance and forensics."""

    events: list[AuditEvent] = field(default_factory=list)
    max_events: int = 10000

    def add_event(self, event: AuditEvent) -> None:
        """Add an event to the trail."""
        self.events.append(event)
        # Trim if over limit
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

    def get_events(
        self,
        event_type: AuditEventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        snapshot_id: str | None = None,
    ) -> list[AuditEvent]:
        """Query events with filters."""
        events = self.events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        if snapshot_id:
            events = [e for e in events if e.snapshot_id == snapshot_id]

        return events

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "events": [e.to_dict() for e in self.events],
            "max_events": self.max_events,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditTrail:
        """Create from dictionary."""
        return cls(
            events=[AuditEvent.from_dict(e) for e in data.get("events", [])],
            max_events=data.get("max_events", 10000),
        )


@dataclass
class ResourceSnapshot:
    """Snapshot of a single resource."""

    resource_id: str
    resource_type: str
    resource_name: str
    arn: str | None
    region: str
    config: dict[str, Any]
    tags: dict[str, str]
    dependencies: list[str]
    config_hash: str = ""

    def __post_init__(self) -> None:
        """Compute config hash if not provided."""
        if not self.config_hash:
            self.config_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute hash of the resource configuration."""
        data = json.dumps(self.config, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "arn": self.arn,
            "region": self.region,
            "config": self.config,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "config_hash": self.config_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceSnapshot:
        """Create from dictionary."""
        return cls(
            resource_id=data["resource_id"],
            resource_type=data["resource_type"],
            resource_name=data.get("resource_name", ""),
            arn=data.get("arn"),
            region=data.get("region", ""),
            config=data.get("config", {}),
            tags=data.get("tags", {}),
            dependencies=data.get("dependencies", []),
            config_hash=data.get("config_hash", ""),
        )

    @classmethod
    def from_resource_node(cls, node: ResourceNode) -> ResourceSnapshot:
        """Create snapshot from a ResourceNode."""
        return cls(
            resource_id=node.id,
            resource_type=node.resource_type,
            resource_name=node.original_name or node.terraform_name,
            arn=node.arn,
            region=node.region or "",
            config=node.config,
            tags=node.tags,
            dependencies=list(node.dependencies),
        )


@dataclass
class SnapshotMetadata:
    """Metadata for a snapshot."""

    snapshot_id: str
    created_at: datetime
    region: str
    account_id: str
    resource_count: int
    description: str = ""
    tags: dict[str, str] = field(default_factory=dict)
    compressed: bool = True
    file_size_bytes: int = 0
    checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at.isoformat(),
            "region": self.region,
            "account_id": self.account_id,
            "resource_count": self.resource_count,
            "description": self.description,
            "tags": self.tags,
            "compressed": self.compressed,
            "file_size_bytes": self.file_size_bytes,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SnapshotMetadata:
        """Create from dictionary."""
        return cls(
            snapshot_id=data["snapshot_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            region=data["region"],
            account_id=data.get("account_id", "unknown"),
            resource_count=data.get("resource_count", 0),
            description=data.get("description", ""),
            tags=data.get("tags", {}),
            compressed=data.get("compressed", True),
            file_size_bytes=data.get("file_size_bytes", 0),
            checksum=data.get("checksum", ""),
        )


@dataclass
class SnapshotDiff:
    """Difference between two resource snapshots."""

    resource_id: str
    resource_type: str
    change_type: str  # "added", "removed", "modified"
    old_snapshot: ResourceSnapshot | None = None
    new_snapshot: ResourceSnapshot | None = None
    changed_fields: list[str] = field(default_factory=list)
    config_diff: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "change_type": self.change_type,
            "old_snapshot": self.old_snapshot.to_dict() if self.old_snapshot else None,
            "new_snapshot": self.new_snapshot.to_dict() if self.new_snapshot else None,
            "changed_fields": self.changed_fields,
            "config_diff": self.config_diff,
        }


@dataclass
class SnapshotComparison:
    """Comparison between two snapshots."""

    old_snapshot_id: str
    new_snapshot_id: str
    old_timestamp: datetime
    new_timestamp: datetime
    diffs: list[SnapshotDiff] = field(default_factory=list)
    added_count: int = 0
    removed_count: int = 0
    modified_count: int = 0

    @property
    def total_changes(self) -> int:
        """Total number of changes."""
        return self.added_count + self.removed_count + self.modified_count

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return self.total_changes > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "old_snapshot_id": self.old_snapshot_id,
            "new_snapshot_id": self.new_snapshot_id,
            "old_timestamp": self.old_timestamp.isoformat(),
            "new_timestamp": self.new_timestamp.isoformat(),
            "diffs": [d.to_dict() for d in self.diffs],
            "summary": {
                "added_count": self.added_count,
                "removed_count": self.removed_count,
                "modified_count": self.modified_count,
                "total_changes": self.total_changes,
            },
        }


class SnapshotManager:
    """
    Manages infrastructure snapshots.

    Provides:
    - Snapshot creation and storage
    - 30-day retention with automatic cleanup
    - Point-in-time retrieval
    - Snapshot comparison/diff
    - Audit trail for compliance
    """

    DEFAULT_DIR = ".replimap/snapshots"
    METADATA_FILE = "metadata.json"
    AUDIT_FILE = "audit_trail.json"

    def __init__(
        self,
        base_dir: str | Path | None = None,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        compress: bool = True,
    ) -> None:
        """
        Initialize the snapshot manager.

        Args:
            base_dir: Directory for snapshot storage
            retention_days: Number of days to retain snapshots
            compress: Whether to compress snapshot files
        """
        if base_dir is None:
            base_dir = Path.home() / self.DEFAULT_DIR
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self.compress = compress
        self._audit_trail: AuditTrail | None = None

    @property
    def audit_trail(self) -> AuditTrail:
        """Get or load the audit trail."""
        if self._audit_trail is None:
            self._audit_trail = self._load_audit_trail()
        return self._audit_trail

    def _get_snapshot_path(self, snapshot_id: str) -> Path:
        """Get path to a snapshot file."""
        ext = ".json.gz" if self.compress else ".json"
        return self.base_dir / f"{snapshot_id}{ext}"

    def _generate_snapshot_id(self, region: str, account_id: str) -> str:
        """Generate a unique snapshot ID."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return f"{account_id}_{region}_{timestamp}"

    def _load_audit_trail(self) -> AuditTrail:
        """Load audit trail from disk."""
        audit_file = self.base_dir / self.AUDIT_FILE
        if audit_file.exists():
            try:
                with open(audit_file) as f:
                    return AuditTrail.from_dict(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load audit trail: {e}")
        return AuditTrail()

    def _save_audit_trail(self) -> None:
        """Save audit trail to disk."""
        audit_file = self.base_dir / self.AUDIT_FILE
        try:
            with open(audit_file, "w") as f:
                json.dump(self.audit_trail.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save audit trail: {e}")

    def _record_event(
        self,
        event_type: AuditEventType,
        details: dict[str, Any] | None = None,
        snapshot_id: str | None = None,
    ) -> None:
        """Record an audit event."""
        event = AuditEvent(
            event_type=event_type,
            timestamp=datetime.now(UTC),
            details=details or {},
            snapshot_id=snapshot_id,
        )
        self.audit_trail.add_event(event)
        self._save_audit_trail()

    def create_snapshot(
        self,
        graph: GraphEngine,
        region: str,
        account_id: str,
        description: str = "",
        tags: dict[str, str] | None = None,
    ) -> SnapshotMetadata:
        """
        Create a snapshot from a GraphEngine.

        Args:
            graph: GraphEngine with scanned resources
            region: AWS region
            account_id: AWS account ID
            description: Optional description
            tags: Optional tags

        Returns:
            SnapshotMetadata for the created snapshot
        """
        snapshot_id = self._generate_snapshot_id(region, account_id)
        created_at = datetime.now(UTC)

        # Create resource snapshots
        resources: list[dict[str, Any]] = []
        for node in graph.nodes.values():
            snapshot = ResourceSnapshot.from_resource_node(node)
            resources.append(snapshot.to_dict())

        # Prepare snapshot data
        snapshot_data = {
            "snapshot_id": snapshot_id,
            "created_at": created_at.isoformat(),
            "region": region,
            "account_id": account_id,
            "description": description,
            "resources": resources,
        }

        # Compute checksum
        data_json = json.dumps(snapshot_data, sort_keys=True)
        checksum = hashlib.sha256(data_json.encode()).hexdigest()

        # Write snapshot file
        snapshot_path = self._get_snapshot_path(snapshot_id)

        if self.compress:
            with gzip.open(snapshot_path, "wt", encoding="utf-8") as f:
                json.dump(snapshot_data, f)
        else:
            with open(snapshot_path, "w") as f:
                json.dump(snapshot_data, f, indent=2)

        file_size = snapshot_path.stat().st_size

        # Create metadata
        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            created_at=created_at,
            region=region,
            account_id=account_id,
            resource_count=len(resources),
            description=description,
            tags=tags or {},
            compressed=self.compress,
            file_size_bytes=file_size,
            checksum=checksum,
        )

        # Save metadata index
        self._update_metadata_index(metadata)

        # Record audit event
        self._record_event(
            AuditEventType.SNAPSHOT_CREATED,
            {
                "resource_count": len(resources),
                "file_size_bytes": file_size,
            },
            snapshot_id,
        )

        logger.info(f"Created snapshot {snapshot_id} with {len(resources)} resources")

        return metadata

    def load_snapshot(
        self,
        snapshot_id: str,
    ) -> tuple[SnapshotMetadata, list[ResourceSnapshot]] | None:
        """
        Load a snapshot by ID.

        Args:
            snapshot_id: Snapshot ID to load

        Returns:
            Tuple of (metadata, resources) or None if not found
        """
        # Try compressed first, then uncompressed
        for ext in [".json.gz", ".json"]:
            snapshot_path = self.base_dir / f"{snapshot_id}{ext}"
            if snapshot_path.exists():
                try:
                    if ext == ".json.gz":
                        with gzip.open(snapshot_path, "rt", encoding="utf-8") as f:
                            data = json.load(f)
                    else:
                        with open(snapshot_path) as f:
                            data = json.load(f)

                    # Parse resources
                    resources = [
                        ResourceSnapshot.from_dict(r) for r in data.get("resources", [])
                    ]

                    # Create metadata
                    metadata = SnapshotMetadata(
                        snapshot_id=data["snapshot_id"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        region=data["region"],
                        account_id=data.get("account_id", "unknown"),
                        resource_count=len(resources),
                        description=data.get("description", ""),
                        compressed=ext == ".json.gz",
                        file_size_bytes=snapshot_path.stat().st_size,
                    )

                    return metadata, resources

                except Exception as e:
                    logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
                    return None

        return None

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.

        Args:
            snapshot_id: Snapshot ID to delete

        Returns:
            True if deleted, False if not found
        """
        for ext in [".json.gz", ".json"]:
            snapshot_path = self.base_dir / f"{snapshot_id}{ext}"
            if snapshot_path.exists():
                snapshot_path.unlink()

                # Update metadata index
                self._remove_from_metadata_index(snapshot_id)

                # Record audit event
                self._record_event(
                    AuditEventType.SNAPSHOT_DELETED,
                    snapshot_id=snapshot_id,
                )

                logger.info(f"Deleted snapshot {snapshot_id}")
                return True

        return False

    def list_snapshots(
        self,
        region: str | None = None,
        account_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[SnapshotMetadata]:
        """
        List available snapshots with optional filters.

        Args:
            region: Filter by region
            account_id: Filter by account ID
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of matching snapshot metadata
        """
        metadata_list = self._load_metadata_index()

        # Apply filters
        if region:
            metadata_list = [m for m in metadata_list if m.region == region]

        if account_id:
            metadata_list = [m for m in metadata_list if m.account_id == account_id]

        if start_date:
            metadata_list = [m for m in metadata_list if m.created_at >= start_date]

        if end_date:
            metadata_list = [m for m in metadata_list if m.created_at <= end_date]

        # Sort by creation time (newest first)
        metadata_list.sort(key=lambda m: m.created_at, reverse=True)

        return metadata_list

    def get_snapshot_at_time(
        self,
        target_time: datetime,
        region: str,
        account_id: str | None = None,
    ) -> SnapshotMetadata | None:
        """
        Get the snapshot closest to (but not after) a target time.

        Args:
            target_time: Target point in time
            region: AWS region
            account_id: Optional account ID filter

        Returns:
            SnapshotMetadata or None if not found
        """
        snapshots = self.list_snapshots(
            region=region,
            account_id=account_id,
            end_date=target_time,
        )

        if snapshots:
            return snapshots[0]  # Already sorted newest first
        return None

    def compare_snapshots(
        self,
        old_snapshot_id: str,
        new_snapshot_id: str,
    ) -> SnapshotComparison | None:
        """
        Compare two snapshots.

        Args:
            old_snapshot_id: ID of older snapshot
            new_snapshot_id: ID of newer snapshot

        Returns:
            SnapshotComparison or None if snapshots not found
        """
        old_result = self.load_snapshot(old_snapshot_id)
        new_result = self.load_snapshot(new_snapshot_id)

        if not old_result or not new_result:
            return None

        old_metadata, old_resources = old_result
        new_metadata, new_resources = new_result

        # Build lookup maps
        old_map = {r.resource_id: r for r in old_resources}
        new_map = {r.resource_id: r for r in new_resources}

        diffs: list[SnapshotDiff] = []
        added_count = 0
        removed_count = 0
        modified_count = 0

        # Find added and modified
        for resource_id, new_resource in new_map.items():
            if resource_id not in old_map:
                # Added
                diffs.append(
                    SnapshotDiff(
                        resource_id=resource_id,
                        resource_type=new_resource.resource_type,
                        change_type="added",
                        new_snapshot=new_resource,
                    )
                )
                added_count += 1
            else:
                old_resource = old_map[resource_id]
                if old_resource.config_hash != new_resource.config_hash:
                    # Modified
                    changed_fields = self._find_changed_fields(
                        old_resource.config, new_resource.config
                    )
                    diffs.append(
                        SnapshotDiff(
                            resource_id=resource_id,
                            resource_type=new_resource.resource_type,
                            change_type="modified",
                            old_snapshot=old_resource,
                            new_snapshot=new_resource,
                            changed_fields=changed_fields,
                        )
                    )
                    modified_count += 1

        # Find removed
        for resource_id, old_resource in old_map.items():
            if resource_id not in new_map:
                diffs.append(
                    SnapshotDiff(
                        resource_id=resource_id,
                        resource_type=old_resource.resource_type,
                        change_type="removed",
                        old_snapshot=old_resource,
                    )
                )
                removed_count += 1

        comparison = SnapshotComparison(
            old_snapshot_id=old_snapshot_id,
            new_snapshot_id=new_snapshot_id,
            old_timestamp=old_metadata.created_at,
            new_timestamp=new_metadata.created_at,
            diffs=diffs,
            added_count=added_count,
            removed_count=removed_count,
            modified_count=modified_count,
        )

        # Record audit event
        self._record_event(
            AuditEventType.SNAPSHOT_COMPARED,
            {
                "old_snapshot_id": old_snapshot_id,
                "new_snapshot_id": new_snapshot_id,
                "total_changes": comparison.total_changes,
            },
        )

        return comparison

    def _find_changed_fields(
        self,
        old_config: dict[str, Any],
        new_config: dict[str, Any],
    ) -> list[str]:
        """Find fields that changed between two configs."""
        changed = []
        all_keys = set(old_config.keys()) | set(new_config.keys())

        for key in all_keys:
            old_val = old_config.get(key)
            new_val = new_config.get(key)
            if old_val != new_val:
                changed.append(key)

        return changed

    def cleanup_old_snapshots(self) -> int:
        """
        Remove snapshots older than retention period.

        Returns:
            Number of snapshots deleted
        """
        cutoff = datetime.now(UTC) - timedelta(days=self.retention_days)
        snapshots = self.list_snapshots(end_date=cutoff)

        deleted = 0
        for snapshot in snapshots:
            if self.delete_snapshot(snapshot.snapshot_id):
                deleted += 1

        if deleted > 0:
            self._record_event(
                AuditEventType.RETENTION_CLEANUP,
                {"deleted_count": deleted, "retention_days": self.retention_days},
            )
            logger.info(f"Cleaned up {deleted} old snapshots")

        return deleted

    def _load_metadata_index(self) -> list[SnapshotMetadata]:
        """Load the metadata index."""
        index_path = self.base_dir / self.METADATA_FILE
        if not index_path.exists():
            return []

        try:
            with open(index_path) as f:
                data = json.load(f)
            return [SnapshotMetadata.from_dict(m) for m in data.get("snapshots", [])]
        except Exception as e:
            logger.warning(f"Failed to load metadata index: {e}")
            return []

    def _update_metadata_index(self, metadata: SnapshotMetadata) -> None:
        """Add or update metadata in the index."""
        index = self._load_metadata_index()

        # Remove existing entry for this snapshot_id
        index = [m for m in index if m.snapshot_id != metadata.snapshot_id]

        # Add new entry
        index.append(metadata)

        # Trim if over limit
        if len(index) > MAX_SNAPSHOTS:
            index.sort(key=lambda m: m.created_at)
            # Delete oldest
            for old in index[:-MAX_SNAPSHOTS]:
                self.delete_snapshot(old.snapshot_id)
            index = index[-MAX_SNAPSHOTS:]

        # Save
        self._save_metadata_index(index)

    def _remove_from_metadata_index(self, snapshot_id: str) -> None:
        """Remove a snapshot from the metadata index."""
        index = self._load_metadata_index()
        index = [m for m in index if m.snapshot_id != snapshot_id]
        self._save_metadata_index(index)

    def _save_metadata_index(self, index: list[SnapshotMetadata]) -> None:
        """Save the metadata index."""
        index_path = self.base_dir / self.METADATA_FILE
        data = {"snapshots": [m.to_dict() for m in index]}
        with open(index_path, "w") as f:
            json.dump(data, f, indent=2)


def create_snapshot_manager(
    base_dir: str | Path | None = None,
    retention_days: int = DEFAULT_RETENTION_DAYS,
) -> SnapshotManager:
    """
    Create a snapshot manager.

    Args:
        base_dir: Directory for snapshot storage
        retention_days: Number of days to retain snapshots

    Returns:
        Configured SnapshotManager
    """
    return SnapshotManager(base_dir, retention_days)


def compare_snapshots(
    manager: SnapshotManager,
    old_snapshot_id: str,
    new_snapshot_id: str,
) -> SnapshotComparison | None:
    """
    Compare two snapshots using a manager.

    Args:
        manager: SnapshotManager instance
        old_snapshot_id: ID of older snapshot
        new_snapshot_id: ID of newer snapshot

    Returns:
        SnapshotComparison or None if snapshots not found
    """
    return manager.compare_snapshots(old_snapshot_id, new_snapshot_id)
