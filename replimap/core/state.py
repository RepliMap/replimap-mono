"""
State Management for RepliMap.

Separates runtime state from user configuration (replimap.yaml).

State includes:
- Scan metadata (timestamps, duration, errors)
- Resource hashes for incremental scanning
- Snapshot history
- Graph statistics

State is stored in .replimap/state.yaml (should be gitignored).
Configuration is stored in replimap.yaml (should be version controlled).

State Schema Version: 2
Location: .replimap/state.yaml

Usage:
    # Load or create state
    state_manager = StateManager()
    state = state_manager.load()

    # Update scan metadata
    state.record_scan_start("123456789012", "us-east-1")
    # ... perform scan ...
    state.record_scan_complete(node_count=1234, edge_count=5678)

    # Save state
    state_manager.save(state)

    # Check for changes
    if state.has_resource_changed("vpc-12345", new_hash):
        # Resource needs re-scanning
        pass
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# State schema version
STATE_VERSION = 2

# Default state directory (relative to working directory)
DEFAULT_STATE_DIR = Path(".replimap")
STATE_FILENAME = "state.yaml"


@dataclass
class ScanRecord:
    """Record of a completed scan."""

    account_id: str
    region: str | None
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    node_count: int = 0
    edge_count: int = 0
    error_count: int = 0
    status: str = "in_progress"  # in_progress, completed, failed

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "account_id": self.account_id,
            "region": self.region,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "error_count": self.error_count,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScanRecord:
        """Create from dictionary."""
        return cls(
            account_id=data["account_id"],
            region=data.get("region"),
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            duration_seconds=data.get("duration_seconds", 0.0),
            node_count=data.get("node_count", 0),
            edge_count=data.get("edge_count", 0),
            error_count=data.get("error_count", 0),
            status=data.get("status", "completed"),
        )


@dataclass
class SnapshotInfo:
    """Information about a saved graph snapshot."""

    snapshot_id: str
    timestamp: datetime
    db_file: str
    node_count: int
    edge_count: int
    account_id: str
    regions: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp.isoformat(),
            "db_file": self.db_file,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "account_id": self.account_id,
            "regions": self.regions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SnapshotInfo:
        """Create from dictionary."""
        return cls(
            snapshot_id=data["snapshot_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            db_file=data["db_file"],
            node_count=data["node_count"],
            edge_count=data["edge_count"],
            account_id=data["account_id"],
            regions=data.get("regions", []),
        )


@dataclass
class ErrorRecord:
    """Record of an error during scanning."""

    timestamp: datetime
    resource_type: str
    error_code: str
    error_message: str
    region: str | None = None
    retried: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "resource_type": self.resource_type,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "region": self.region,
            "retried": self.retried,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ErrorRecord:
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            resource_type=data["resource_type"],
            error_code=data.get("error_code", "UnknownError"),
            error_message=data["error_message"],
            region=data.get("region"),
            retried=data.get("retried", False),
        )


@dataclass
class RepliMapState:
    """
    Runtime state for RepliMap.

    This contains ephemeral data that should NOT be version controlled:
    - Scan history
    - Resource hashes
    - Snapshot registry
    - Error logs

    The state file (.replimap/state.yaml) should be in .gitignore.
    """

    version: int = STATE_VERSION

    # Current scan state
    current_scan: ScanRecord | None = None

    # Scan history (last N scans)
    scan_history: list[ScanRecord] = field(default_factory=list)

    # Resource hashes for incremental scanning
    # Format: {node_id: config_hash}
    resource_hashes: dict[str, str] = field(default_factory=dict)

    # Snapshot registry
    snapshots: list[SnapshotInfo] = field(default_factory=list)

    # Error log (last N errors)
    errors: list[ErrorRecord] = field(default_factory=list)

    # State file path
    state_path: Path | None = None

    # Constants
    MAX_SCAN_HISTORY: int = 10
    MAX_ERROR_LOG: int = 100

    def record_scan_start(
        self,
        account_id: str,
        region: str | None = None,
    ) -> None:
        """Record the start of a new scan."""
        self.current_scan = ScanRecord(
            account_id=account_id,
            region=region,
            started_at=datetime.now(),
            status="in_progress",
        )
        logger.debug(f"Scan started for {account_id}/{region}")

    def record_scan_complete(
        self,
        node_count: int = 0,
        edge_count: int = 0,
        error_count: int = 0,
    ) -> None:
        """Record scan completion."""
        if self.current_scan is None:
            logger.warning("No scan in progress")
            return

        now = datetime.now()
        self.current_scan.completed_at = now
        self.current_scan.duration_seconds = (
            now - self.current_scan.started_at
        ).total_seconds()
        self.current_scan.node_count = node_count
        self.current_scan.edge_count = edge_count
        self.current_scan.error_count = error_count
        self.current_scan.status = "completed"

        # Add to history
        self.scan_history.insert(0, self.current_scan)
        self.scan_history = self.scan_history[: self.MAX_SCAN_HISTORY]

        logger.info(
            f"Scan completed: {node_count} nodes, {edge_count} edges "
            f"in {self.current_scan.duration_seconds:.2f}s"
        )

        self.current_scan = None

    def record_scan_failed(self, error: str) -> None:
        """Record scan failure."""
        if self.current_scan is None:
            logger.warning("No scan in progress")
            return

        now = datetime.now()
        self.current_scan.completed_at = now
        self.current_scan.duration_seconds = (
            now - self.current_scan.started_at
        ).total_seconds()
        self.current_scan.status = "failed"

        # Add to history
        self.scan_history.insert(0, self.current_scan)
        self.scan_history = self.scan_history[: self.MAX_SCAN_HISTORY]

        # Record error
        self.record_error(
            resource_type="scan",
            error_code="ScanFailed",
            error_message=error,
        )

        self.current_scan = None

    def record_error(
        self,
        resource_type: str,
        error_code: str,
        error_message: str,
        region: str | None = None,
        retried: bool = False,
    ) -> None:
        """Record an error."""
        error = ErrorRecord(
            timestamp=datetime.now(),
            resource_type=resource_type,
            error_code=error_code,
            error_message=error_message,
            region=region,
            retried=retried,
        )
        self.errors.insert(0, error)
        self.errors = self.errors[: self.MAX_ERROR_LOG]

    def update_resource_hash(self, node_id: str, config_hash: str) -> None:
        """Update the hash for a resource."""
        self.resource_hashes[node_id] = config_hash

    def update_resource_hashes_batch(
        self,
        hashes: dict[str, str],
    ) -> None:
        """Batch update resource hashes."""
        self.resource_hashes.update(hashes)

    def has_resource_changed(self, node_id: str, new_hash: str) -> bool:
        """
        Check if a resource configuration has changed.

        Args:
            node_id: Resource node ID
            new_hash: New configuration hash

        Returns:
            True if resource is new or changed, False if unchanged
        """
        old_hash = self.resource_hashes.get(node_id)
        return old_hash != new_hash

    def get_unchanged_resources(self, new_hashes: dict[str, str]) -> set[str]:
        """
        Get resources that haven't changed.

        Args:
            new_hashes: Current resource hashes

        Returns:
            Set of node IDs that are unchanged
        """
        unchanged = set()
        for node_id, new_hash in new_hashes.items():
            if not self.has_resource_changed(node_id, new_hash):
                unchanged.add(node_id)
        return unchanged

    def get_changed_resources(self, new_hashes: dict[str, str]) -> set[str]:
        """
        Get resources that have changed.

        Args:
            new_hashes: Current resource hashes

        Returns:
            Set of node IDs that are new or changed
        """
        changed = set()
        for node_id, new_hash in new_hashes.items():
            if self.has_resource_changed(node_id, new_hash):
                changed.add(node_id)
        return changed

    def register_snapshot(
        self,
        snapshot_id: str,
        db_file: str,
        node_count: int,
        edge_count: int,
        account_id: str,
        regions: list[str],
    ) -> SnapshotInfo:
        """Register a new snapshot."""
        snapshot = SnapshotInfo(
            snapshot_id=snapshot_id,
            timestamp=datetime.now(),
            db_file=db_file,
            node_count=node_count,
            edge_count=edge_count,
            account_id=account_id,
            regions=regions,
        )
        self.snapshots.insert(0, snapshot)
        return snapshot

    def get_last_scan(self) -> ScanRecord | None:
        """Get the most recent completed scan."""
        if self.scan_history:
            return self.scan_history[0]
        return None

    def get_last_scan_time(self) -> datetime | None:
        """Get the timestamp of the last completed scan."""
        last = self.get_last_scan()
        return last.completed_at if last else None

    def get_scan_stats(self) -> dict[str, Any]:
        """Get scan statistics."""
        if not self.scan_history:
            return {
                "total_scans": 0,
                "successful_scans": 0,
                "failed_scans": 0,
                "avg_duration_seconds": 0,
                "avg_node_count": 0,
            }

        successful = [s for s in self.scan_history if s.status == "completed"]
        failed = [s for s in self.scan_history if s.status == "failed"]

        avg_duration = (
            sum(s.duration_seconds for s in successful) / len(successful)
            if successful
            else 0
        )
        avg_nodes = (
            sum(s.node_count for s in successful) / len(successful)
            if successful
            else 0
        )

        return {
            "total_scans": len(self.scan_history),
            "successful_scans": len(successful),
            "failed_scans": len(failed),
            "avg_duration_seconds": round(avg_duration, 2),
            "avg_node_count": round(avg_nodes),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert state to serializable dictionary."""
        return {
            "version": self.version,
            "current_scan": (
                self.current_scan.to_dict() if self.current_scan else None
            ),
            "scan_history": [s.to_dict() for s in self.scan_history],
            "resource_hashes": self.resource_hashes,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "errors": [e.to_dict() for e in self.errors],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RepliMapState:
        """Create state from dictionary."""
        version = data.get("version", 1)

        if version < STATE_VERSION:
            data = cls._migrate(data, version, STATE_VERSION)

        state = cls(version=STATE_VERSION)

        # Load current scan
        if data.get("current_scan"):
            state.current_scan = ScanRecord.from_dict(data["current_scan"])

        # Load scan history
        state.scan_history = [
            ScanRecord.from_dict(s) for s in data.get("scan_history", [])
        ]

        # Load resource hashes
        state.resource_hashes = data.get("resource_hashes", {})

        # Load snapshots
        state.snapshots = [
            SnapshotInfo.from_dict(s) for s in data.get("snapshots", [])
        ]

        # Load errors
        state.errors = [ErrorRecord.from_dict(e) for e in data.get("errors", [])]

        return state

    @classmethod
    def _migrate(
        cls,
        data: dict[str, Any],
        from_version: int,
        to_version: int,
    ) -> dict[str, Any]:
        """Migrate state from old version to new version."""
        logger.info(f"Migrating state from v{from_version} to v{to_version}")

        # Version 1 -> 2: Add error tracking
        if from_version < 2:
            data["errors"] = []
            data["version"] = 2

        return data


class StateManager:
    """
    Manages RepliMap state persistence.

    The state file is stored at .replimap/state.yaml in the working directory.
    This file should be added to .gitignore.

    Example:
        manager = StateManager()

        # Load existing state or create new
        state = manager.load()

        # Use state for incremental scanning
        if state.has_resource_changed("vpc-123", new_hash):
            # Re-scan this resource
            pass

        # Save state after operations
        manager.save(state)
    """

    def __init__(
        self,
        working_dir: str | Path | None = None,
        state_dir: str | Path | None = None,
    ) -> None:
        """
        Initialize the state manager.

        Args:
            working_dir: Working directory (default: current directory)
            state_dir: State directory (default: .replimap/ in working_dir)
        """
        self.working_dir = Path(working_dir or os.getcwd())

        if state_dir:
            self.state_dir = Path(state_dir)
        else:
            self.state_dir = self.working_dir / DEFAULT_STATE_DIR

        self.state_path = self.state_dir / STATE_FILENAME
        self._state: RepliMapState | None = None

    def ensure_state_dir(self) -> None:
        """Ensure state directory exists and has proper gitignore."""
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions
        os.chmod(self.state_dir, 0o700)

        # Ensure gitignore exists
        self._ensure_gitignore()

    def _ensure_gitignore(self) -> None:
        """Ensure .replimap/ is in .gitignore."""
        gitignore_path = self.working_dir / ".gitignore"

        if not gitignore_path.exists():
            return

        try:
            content = gitignore_path.read_text()
            replimap_pattern = ".replimap/"

            if replimap_pattern not in content:
                # Append to gitignore
                with open(gitignore_path, "a") as f:
                    f.write(f"\n# RepliMap state (auto-generated)\n{replimap_pattern}\n")
                logger.debug(f"Added {replimap_pattern} to .gitignore")
        except Exception as e:
            logger.warning(f"Could not update .gitignore: {e}")

    def load(self) -> RepliMapState:
        """
        Load state from file.

        Creates a new state if the file doesn't exist.

        Returns:
            Loaded or new RepliMapState
        """
        if self._state is not None:
            return self._state

        if not self.state_path.exists():
            logger.debug("No state file found, creating new state")
            self._state = RepliMapState(state_path=self.state_path)
            return self._state

        try:
            with open(self.state_path) as f:
                data = yaml.safe_load(f) or {}

            self._state = RepliMapState.from_dict(data)
            self._state.state_path = self.state_path

            logger.debug(f"Loaded state from {self.state_path}")

        except Exception as e:
            logger.warning(f"Failed to load state: {e}. Creating new state.")
            self._state = RepliMapState(state_path=self.state_path)

        return self._state

    def save(self, state: RepliMapState | None = None) -> Path:
        """
        Save state to file.

        Args:
            state: State to save (uses cached state if None)

        Returns:
            Path to saved state file
        """
        state = state or self._state

        if state is None:
            raise ValueError("No state to save")

        self.ensure_state_dir()

        try:
            with open(self.state_path, "w") as f:
                yaml.dump(
                    state.to_dict(),
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            # Set restrictive permissions
            os.chmod(self.state_path, 0o600)

            logger.debug(f"Saved state to {self.state_path}")

        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            raise

        return self.state_path

    def delete(self) -> bool:
        """
        Delete the state file.

        Returns:
            True if deleted, False if it didn't exist
        """
        if self.state_path.exists():
            os.remove(self.state_path)
            self._state = None
            logger.info(f"Deleted state file: {self.state_path}")
            return True
        return False

    def clear_resource_hashes(self) -> None:
        """Clear all resource hashes (forces full re-scan)."""
        state = self.load()
        state.resource_hashes.clear()
        self.save(state)
        logger.info("Cleared resource hashes")

    def clear_errors(self) -> None:
        """Clear error log."""
        state = self.load()
        state.errors.clear()
        self.save(state)

    @property
    def state(self) -> RepliMapState:
        """Get cached state (loads if necessary)."""
        if self._state is None:
            self._state = self.load()
        return self._state


def compute_config_hash(config: dict[str, Any]) -> str:
    """
    Compute a hash for a resource configuration.

    Ignores volatile fields that change frequently but don't
    indicate meaningful resource changes.

    Args:
        config: Resource configuration dictionary

    Returns:
        SHA256 hash of the configuration
    """
    # Fields to ignore (they change but don't indicate real changes)
    VOLATILE_FIELDS = {
        "LastModifiedTime",
        "LastActivityTime",
        "LastAccessTime",
        "LastUpdatedTime",
        "LaunchTime",
        "CreateTime",
        "ModifyTime",
        "UsageReportS3BucketName",  # Changes with reports
    }

    def clean_config(obj: Any) -> Any:
        """Recursively clean volatile fields."""
        if isinstance(obj, dict):
            return {
                k: clean_config(v)
                for k, v in obj.items()
                if k not in VOLATILE_FIELDS
            }
        elif isinstance(obj, list):
            return [clean_config(item) for item in obj]
        else:
            return obj

    cleaned = clean_config(config)
    json_str = json.dumps(cleaned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode()).hexdigest()
