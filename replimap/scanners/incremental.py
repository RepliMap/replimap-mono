"""
Incremental Scanning for RepliMap.

Provides efficient scanning by:
- Using ResourceGroupsTaggingAPI for timestamp-based change detection
- Only updating resources that have changed since last scan
- Persisting scan state for resumable operations

This significantly reduces API calls and scan time for large infrastructures
by only querying resources that have changed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError

from replimap.core.aws_config import BOTO_CONFIG

if TYPE_CHECKING:
    from replimap.core import GraphEngine
    from replimap.core.models import ResourceNode

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Types of resource changes."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"

    def __str__(self) -> str:
        return self.value


@dataclass
class ResourceFingerprint:
    """
    Fingerprint of a resource for change detection.

    Stores metadata that can be used to detect changes
    without fetching the full resource configuration.
    """

    resource_id: str
    resource_type: str
    arn: str | None = None
    last_modified: datetime | None = None
    config_hash: str = ""
    tags_hash: str = ""
    version: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "arn": self.arn,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "config_hash": self.config_hash,
            "tags_hash": self.tags_hash,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceFingerprint:
        """Create from dictionary."""
        last_modified = None
        if data.get("last_modified"):
            last_modified = datetime.fromisoformat(data["last_modified"])

        return cls(
            resource_id=data["resource_id"],
            resource_type=data["resource_type"],
            arn=data.get("arn"),
            last_modified=last_modified,
            config_hash=data.get("config_hash", ""),
            tags_hash=data.get("tags_hash", ""),
            version=data.get("version", ""),
        )


@dataclass
class ResourceChange:
    """Represents a detected change to a resource."""

    resource_id: str
    resource_type: str
    change_type: ChangeType
    previous_fingerprint: ResourceFingerprint | None = None
    current_fingerprint: ResourceFingerprint | None = None
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "change_type": self.change_type.value,
            "previous_fingerprint": (
                self.previous_fingerprint.to_dict() if self.previous_fingerprint else None
            ),
            "current_fingerprint": (
                self.current_fingerprint.to_dict() if self.current_fingerprint else None
            ),
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class ScanState:
    """
    Persistent state for incremental scanning.

    Tracks the last scan time and resource fingerprints
    to enable efficient change detection.
    """

    region: str
    last_scan: datetime | None = None
    fingerprints: dict[str, ResourceFingerprint] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def resource_count(self) -> int:
        """Number of tracked resources."""
        return len(self.fingerprints)

    def get_fingerprint(self, resource_id: str) -> ResourceFingerprint | None:
        """Get fingerprint for a resource."""
        return self.fingerprints.get(resource_id)

    def update_fingerprint(self, fingerprint: ResourceFingerprint) -> None:
        """Update or add a fingerprint."""
        self.fingerprints[fingerprint.resource_id] = fingerprint

    def remove_fingerprint(self, resource_id: str) -> None:
        """Remove a fingerprint."""
        self.fingerprints.pop(resource_id, None)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "region": self.region,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "fingerprints": {
                k: v.to_dict() for k, v in self.fingerprints.items()
            },
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScanState:
        """Create from dictionary."""
        last_scan = None
        if data.get("last_scan"):
            last_scan = datetime.fromisoformat(data["last_scan"])

        fingerprints = {
            k: ResourceFingerprint.from_dict(v)
            for k, v in data.get("fingerprints", {}).items()
        }

        return cls(
            region=data["region"],
            last_scan=last_scan,
            fingerprints=fingerprints,
            metadata=data.get("metadata", {}),
        )


@dataclass
class IncrementalScanResult:
    """Result of an incremental scan."""

    region: str
    scan_start: datetime
    scan_end: datetime
    changes: list[ResourceChange] = field(default_factory=list)
    resources_checked: int = 0
    resources_updated: int = 0
    resources_deleted: int = 0
    resources_unchanged: int = 0
    full_scan: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Scan duration in seconds."""
        return (self.scan_end - self.scan_start).total_seconds()

    @property
    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return len(self.changes) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "region": self.region,
            "scan_start": self.scan_start.isoformat(),
            "scan_end": self.scan_end.isoformat(),
            "duration_seconds": self.duration_seconds,
            "changes": [c.to_dict() for c in self.changes],
            "summary": {
                "resources_checked": self.resources_checked,
                "resources_updated": self.resources_updated,
                "resources_deleted": self.resources_deleted,
                "resources_unchanged": self.resources_unchanged,
                "has_changes": self.has_changes,
            },
            "full_scan": self.full_scan,
            "errors": self.errors,
        }


class ScanStateStore:
    """
    Persistent storage for scan state.

    Saves and loads scan state to/from disk for
    resumable incremental scanning.
    """

    DEFAULT_DIR = ".replimap/scan_state"

    def __init__(self, base_dir: str | Path | None = None) -> None:
        """
        Initialize the state store.

        Args:
            base_dir: Directory for state files (default: .replimap/scan_state)
        """
        if base_dir is None:
            base_dir = Path.home() / self.DEFAULT_DIR
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_state_file(self, region: str, account_id: str = "default") -> Path:
        """Get path to state file for a region/account."""
        return self.base_dir / f"{account_id}_{region}.json"

    def load(self, region: str, account_id: str = "default") -> ScanState | None:
        """
        Load scan state for a region.

        Args:
            region: AWS region
            account_id: AWS account ID

        Returns:
            ScanState if found, None otherwise
        """
        state_file = self._get_state_file(region, account_id)

        if not state_file.exists():
            return None

        try:
            with open(state_file) as f:
                data = json.load(f)
            return ScanState.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load scan state: {e}")
            return None

    def save(self, state: ScanState, account_id: str = "default") -> None:
        """
        Save scan state for a region.

        Args:
            state: Scan state to save
            account_id: AWS account ID
        """
        state_file = self._get_state_file(state.region, account_id)

        try:
            with open(state_file, "w") as f:
                json.dump(state.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save scan state: {e}")

    def delete(self, region: str, account_id: str = "default") -> None:
        """Delete scan state for a region."""
        state_file = self._get_state_file(region, account_id)
        if state_file.exists():
            state_file.unlink()

    def list_regions(self, account_id: str = "default") -> list[str]:
        """List regions with saved state."""
        regions = []
        for f in self.base_dir.glob(f"{account_id}_*.json"):
            region = f.stem.replace(f"{account_id}_", "")
            regions.append(region)
        return regions


class IncrementalScanner:
    """
    Scanner that performs incremental updates.

    Uses ResourceGroupsTaggingAPI and other AWS APIs to detect
    changes efficiently and only update modified resources.
    """

    # Resource types that support tagging and can be detected via ResourceGroupsTaggingAPI
    TAGGABLE_TYPES: set[str] = {
        "ec2:instance",
        "ec2:volume",
        "ec2:vpc",
        "ec2:subnet",
        "ec2:security-group",
        "ec2:network-interface",
        "ec2:natgateway",
        "ec2:internet-gateway",
        "rds:db",
        "rds:cluster",
        "s3:bucket",  # Note: S3 is global
        "elasticache:cluster",
        "elasticloadbalancing:loadbalancer",
        "elasticloadbalancing:targetgroup",
        "lambda:function",
        "dynamodb:table",
        "sqs:queue",
        "sns:topic",
    }

    # Map from AWS resource type (as returned by tagging API) to Terraform type
    AWS_TO_TERRAFORM_TYPE: dict[str, str] = {
        "ec2:instance": "aws_instance",
        "ec2:volume": "aws_ebs_volume",
        "ec2:vpc": "aws_vpc",
        "ec2:subnet": "aws_subnet",
        "ec2:security-group": "aws_security_group",
        "ec2:network-interface": "aws_network_interface",
        "ec2:natgateway": "aws_nat_gateway",
        "ec2:internet-gateway": "aws_internet_gateway",
        "rds:db": "aws_db_instance",
        "rds:cluster": "aws_rds_cluster",
        "s3": "aws_s3_bucket",
        "elasticache:cluster": "aws_elasticache_cluster",
        "elasticloadbalancing:loadbalancer": "aws_lb",
        "elasticloadbalancing:targetgroup": "aws_lb_target_group",
        "lambda:function": "aws_lambda_function",
        "dynamodb:table": "aws_dynamodb_table",
        "sqs": "aws_sqs_queue",
        "sns": "aws_sns_topic",
    }

    def __init__(
        self,
        session: boto3.Session,
        region: str,
        state_store: ScanStateStore | None = None,
    ) -> None:
        """
        Initialize the incremental scanner.

        Args:
            session: Configured boto3 session
            region: AWS region to scan
            state_store: State store for persistence (default creates new)
        """
        self.session = session
        self.region = region
        self.state_store = state_store or ScanStateStore()
        self._clients: dict[str, Any] = {}

    def _get_client(self, service_name: str) -> Any:
        """Get or create a boto3 client."""
        if service_name not in self._clients:
            self._clients[service_name] = self.session.client(
                service_name,
                region_name=self.region,
                config=BOTO_CONFIG,
            )
        return self._clients[service_name]

    def _get_account_id(self) -> str:
        """Get the current AWS account ID."""
        try:
            sts = self._get_client("sts")
            return sts.get_caller_identity()["Account"]
        except Exception:
            return "default"

    def _compute_hash(self, data: Any) -> str:
        """Compute a hash for change detection."""
        if data is None:
            return ""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def _get_tagged_resources(self) -> list[dict[str, Any]]:
        """
        Get all tagged resources using ResourceGroupsTaggingAPI.

        This API is efficient for discovering resources across services.
        """
        client = self._get_client("resourcegroupstaggingapi")
        resources: list[dict[str, Any]] = []

        try:
            paginator = client.get_paginator("get_resources")

            for page in paginator.paginate():
                for resource in page.get("ResourceTagMappingList", []):
                    resources.append(resource)

        except ClientError as e:
            logger.warning(f"Failed to get tagged resources: {e}")

        return resources

    def _extract_resource_info(
        self,
        resource: dict[str, Any],
    ) -> tuple[str, str, str] | None:
        """
        Extract resource ID, type, and ARN from tagging API response.

        Returns:
            Tuple of (resource_id, resource_type, arn) or None if not parseable
        """
        arn = resource.get("ResourceARN", "")
        if not arn:
            return None

        # Parse ARN: arn:aws:service:region:account:resource-type/resource-id
        parts = arn.split(":")
        if len(parts) < 6:
            return None

        service = parts[2]
        resource_part = parts[5]

        # Handle different ARN formats
        if "/" in resource_part:
            resource_type, resource_id = resource_part.split("/", 1)
        elif ":" in resource_part:
            resource_type, resource_id = resource_part.split(":", 1)
        else:
            resource_type = ""
            resource_id = resource_part

        # Map to Terraform type
        aws_type = f"{service}:{resource_type}" if resource_type else service
        terraform_type = self.AWS_TO_TERRAFORM_TYPE.get(
            aws_type,
            f"aws_{service}_{resource_type}" if resource_type else f"aws_{service}",
        )

        return (resource_id, terraform_type, arn)

    def _create_fingerprint(
        self,
        resource_id: str,
        resource_type: str,
        arn: str,
        tags: dict[str, str],
        config: dict[str, Any] | None = None,
    ) -> ResourceFingerprint:
        """Create a fingerprint for a resource."""
        return ResourceFingerprint(
            resource_id=resource_id,
            resource_type=resource_type,
            arn=arn,
            last_modified=datetime.now(timezone.utc),
            config_hash=self._compute_hash(config) if config else "",
            tags_hash=self._compute_hash(tags),
        )

    def detect_changes(
        self,
        previous_state: ScanState | None = None,
    ) -> list[ResourceChange]:
        """
        Detect changes since the last scan.

        Args:
            previous_state: Previous scan state (loads from store if None)

        Returns:
            List of detected changes
        """
        account_id = self._get_account_id()

        if previous_state is None:
            previous_state = self.state_store.load(self.region, account_id)

        if previous_state is None:
            # No previous state, everything is new
            logger.info("No previous scan state found, performing full scan")
            return []

        changes: list[ResourceChange] = []
        current_resources: set[str] = set()

        # Get current resources via tagging API
        tagged_resources = self._get_tagged_resources()

        for resource in tagged_resources:
            info = self._extract_resource_info(resource)
            if not info:
                continue

            resource_id, resource_type, arn = info
            current_resources.add(resource_id)

            # Get tags
            tags = {t["Key"]: t["Value"] for t in resource.get("Tags", [])}

            # Create current fingerprint
            current_fp = self._create_fingerprint(
                resource_id, resource_type, arn, tags
            )

            # Check against previous state
            previous_fp = previous_state.get_fingerprint(resource_id)

            if previous_fp is None:
                # New resource
                changes.append(
                    ResourceChange(
                        resource_id=resource_id,
                        resource_type=resource_type,
                        change_type=ChangeType.CREATED,
                        current_fingerprint=current_fp,
                    )
                )
            elif previous_fp.tags_hash != current_fp.tags_hash:
                # Tags changed
                changes.append(
                    ResourceChange(
                        resource_id=resource_id,
                        resource_type=resource_type,
                        change_type=ChangeType.MODIFIED,
                        previous_fingerprint=previous_fp,
                        current_fingerprint=current_fp,
                    )
                )
            # Note: Config changes require fetching full config, done during full scan

        # Detect deleted resources
        for resource_id, fingerprint in previous_state.fingerprints.items():
            if resource_id not in current_resources:
                changes.append(
                    ResourceChange(
                        resource_id=resource_id,
                        resource_type=fingerprint.resource_type,
                        change_type=ChangeType.DELETED,
                        previous_fingerprint=fingerprint,
                    )
                )

        return changes

    def scan_incremental(
        self,
        graph: GraphEngine,
        force_full: bool = False,
    ) -> IncrementalScanResult:
        """
        Perform an incremental scan.

        Args:
            graph: GraphEngine to update
            force_full: Force a full scan even if state exists

        Returns:
            IncrementalScanResult with scan details
        """
        scan_start = datetime.now(timezone.utc)
        account_id = self._get_account_id()
        errors: list[str] = []

        # Load previous state
        previous_state = None if force_full else self.state_store.load(
            self.region, account_id
        )
        full_scan = previous_state is None or force_full

        # Detect changes
        changes: list[ResourceChange] = []
        resources_checked = 0
        resources_updated = 0
        resources_deleted = 0
        resources_unchanged = 0

        try:
            if full_scan:
                # Full scan: get all tagged resources
                logger.info(f"Performing full scan for {self.region}")
                changes = self._perform_full_scan(graph)
                resources_checked = len(graph.nodes)
                resources_updated = resources_checked
            else:
                # Incremental scan
                logger.info(f"Performing incremental scan for {self.region}")
                changes = self.detect_changes(previous_state)
                resources_checked = len(previous_state.fingerprints) if previous_state else 0

                for change in changes:
                    if change.change_type == ChangeType.CREATED:
                        resources_updated += 1
                        self._update_resource(graph, change)
                    elif change.change_type == ChangeType.MODIFIED:
                        resources_updated += 1
                        self._update_resource(graph, change)
                    elif change.change_type == ChangeType.DELETED:
                        resources_deleted += 1
                        self._remove_resource(graph, change)

                resources_unchanged = resources_checked - resources_updated - resources_deleted

        except Exception as e:
            logger.error(f"Error during incremental scan: {e}")
            errors.append(str(e))

        scan_end = datetime.now(timezone.utc)

        # Update and save state
        new_state = self._create_state_from_graph(graph)
        new_state.last_scan = scan_end
        self.state_store.save(new_state, account_id)

        return IncrementalScanResult(
            region=self.region,
            scan_start=scan_start,
            scan_end=scan_end,
            changes=changes,
            resources_checked=resources_checked,
            resources_updated=resources_updated,
            resources_deleted=resources_deleted,
            resources_unchanged=resources_unchanged,
            full_scan=full_scan,
            errors=errors,
        )

    def _perform_full_scan(self, graph: GraphEngine) -> list[ResourceChange]:
        """
        Perform a full scan and return all resources as 'created'.

        Note: This method triggers a full scan of all resources.
        The actual scanning is delegated to the existing scanners.
        """
        changes: list[ResourceChange] = []

        # Get all tagged resources
        tagged_resources = self._get_tagged_resources()

        for resource in tagged_resources:
            info = self._extract_resource_info(resource)
            if not info:
                continue

            resource_id, resource_type, arn = info
            tags = {t["Key"]: t["Value"] for t in resource.get("Tags", [])}

            fingerprint = self._create_fingerprint(
                resource_id, resource_type, arn, tags
            )

            changes.append(
                ResourceChange(
                    resource_id=resource_id,
                    resource_type=resource_type,
                    change_type=ChangeType.CREATED,
                    current_fingerprint=fingerprint,
                )
            )

        return changes

    def _update_resource(self, graph: GraphEngine, change: ResourceChange) -> None:
        """Update a resource in the graph based on a change."""
        # This would trigger a targeted scan for just this resource
        # Implementation depends on the scanner infrastructure
        logger.debug(
            f"Would update resource {change.resource_id} ({change.change_type})"
        )

    def _remove_resource(self, graph: GraphEngine, change: ResourceChange) -> None:
        """Remove a deleted resource from the graph."""
        # Remove node from graph
        # Implementation depends on GraphEngine API
        logger.debug(f"Would remove resource {change.resource_id}")

    def _create_state_from_graph(self, graph: GraphEngine) -> ScanState:
        """Create a scan state from the current graph."""
        fingerprints: dict[str, ResourceFingerprint] = {}

        for node in graph.nodes.values():
            fingerprint = ResourceFingerprint(
                resource_id=node.id,
                resource_type=node.resource_type,
                arn=node.arn,
                last_modified=datetime.now(timezone.utc),
                config_hash=self._compute_hash(node.config),
                tags_hash=self._compute_hash(node.tags),
            )
            fingerprints[node.id] = fingerprint

        return ScanState(
            region=self.region,
            fingerprints=fingerprints,
        )


def create_incremental_scanner(
    session: boto3.Session,
    region: str,
    state_dir: str | Path | None = None,
) -> IncrementalScanner:
    """
    Create an incremental scanner.

    Args:
        session: boto3 session
        region: AWS region
        state_dir: Directory for state persistence

    Returns:
        Configured IncrementalScanner
    """
    store = ScanStateStore(state_dir) if state_dir else ScanStateStore()
    return IncrementalScanner(session, region, store)


def get_change_summary(changes: list[ResourceChange]) -> dict[str, Any]:
    """
    Get a summary of changes by type.

    Args:
        changes: List of resource changes

    Returns:
        Summary dictionary
    """
    by_type: dict[str, int] = {}
    by_resource_type: dict[str, int] = {}

    for change in changes:
        # By change type
        change_type = change.change_type.value
        by_type[change_type] = by_type.get(change_type, 0) + 1

        # By resource type
        resource_type = change.resource_type
        by_resource_type[resource_type] = by_resource_type.get(resource_type, 0) + 1

    return {
        "total_changes": len(changes),
        "by_change_type": by_type,
        "by_resource_type": by_resource_type,
    }
