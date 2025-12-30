"""Main drift detection orchestration."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from replimap.core.identity_resolver import IdentityResolver, has_scanner_coverage
from replimap.drift.comparator import DriftComparator
from replimap.drift.models import DriftReport, DriftType
from replimap.drift.state_parser import TerraformStateParser, TFResource

if TYPE_CHECKING:
    import boto3

logger = logging.getLogger(__name__)


class DriftEngine:
    """Orchestrates drift detection workflow."""

    def __init__(
        self,
        session: boto3.Session,
        region: str,
        profile: str | None = None,
    ) -> None:
        """Initialize the drift engine.

        Args:
            session: Boto3 session for AWS access
            region: AWS region to scan
            profile: AWS profile name (for display)
        """
        self.session = session
        self.region = region
        self.profile = profile
        self.parser = TerraformStateParser()
        self.comparator = DriftComparator()

    def detect(
        self,
        state_path: Path | None = None,
        remote_backend: dict[str, str] | None = None,
        vpc_id: str | None = None,
    ) -> DriftReport:
        """Run drift detection.

        Args:
            state_path: Path to local terraform.tfstate
            remote_backend: Dict with bucket, key, region for S3 backend
            vpc_id: Optional VPC to scope the scan

        Returns:
            DriftReport with all detected drifts
        """
        from replimap.core import GraphEngine
        from replimap.scanners import run_all_scanners

        start_time = time.time()

        # 1. Parse Terraform state
        logger.info("Parsing Terraform state...")
        if state_path:
            tf_state = self.parser.parse(state_path)
            state_source = str(state_path)
        elif remote_backend:
            # Pass session to use profile credentials for S3 access
            tf_state = self.parser.parse_remote_state(
                remote_backend, session=self.session
            )
            state_source = f"s3://{remote_backend['bucket']}/{remote_backend['key']}"
        else:
            raise ValueError("Either state_path or remote_backend must be provided")

        logger.info(f"Found {len(tf_state.resources)} resources in Terraform state")

        # 2. Scan actual AWS resources using existing scanners
        logger.info("Scanning AWS resources...")
        graph = GraphEngine()
        run_all_scanners(self.session, self.region, graph, parallel=True)

        # Get all resources from the graph
        actual_resources = list(graph.get_all_resources())
        logger.info(f"Found {len(actual_resources)} resources in AWS")

        # Filter by VPC if specified
        if vpc_id:
            actual_resources = self._filter_by_vpc(actual_resources, vpc_id)
            logger.info(
                f"Filtered to {len(actual_resources)} resources in VPC {vpc_id}"
            )

        # 3. Build lookup maps with normalized IDs
        # Different resources use different ID formats:
        # - Scanner IDs may have account:region: prefix or use ARNs
        # - TF state may use URLs (SQS), names, or raw IDs
        # We normalize both sides to a common base ID for matching

        # Normalize TF state IDs
        tf_by_normalized_id: dict[str, TFResource] = {}
        for r in tf_state.resources:
            normalized_id = self._normalize_tf_id(r.id, r.type)
            tf_by_normalized_id[normalized_id] = r
        tf_normalized_ids = set(tf_by_normalized_id.keys())

        # Build map from base resource ID to scanner resource
        actual_by_base_id: dict[str, Any] = {}
        for r in actual_resources:
            resource_type = getattr(r, "terraform_type", str(r.resource_type))
            base_id = self._extract_base_id(r.id, resource_type)
            actual_by_base_id[base_id] = r
        actual_base_ids = set(actual_by_base_id.keys())

        logger.debug(f"TF IDs sample (normalized): {list(tf_normalized_ids)[:5]}")
        logger.debug(f"AWS IDs sample (normalized): {list(actual_base_ids)[:5]}")

        # 4. Compare resources
        logger.info("Comparing resources...")
        drifts = []

        # Check for modifications (resources in both TF and AWS)
        for resource_id in tf_normalized_ids & actual_base_ids:
            tf_resource = tf_by_normalized_id[resource_id]
            actual_resource = actual_by_base_id[resource_id]

            # Get actual attributes (convert from scanner format)
            actual_attrs = self._extract_attributes(actual_resource)

            drift = self.comparator.compare_resource(tf_resource, actual_attrs)
            if drift.is_drifted:
                drifts.append(drift)

        # Check for added resources (in AWS but not in TF)
        # Pass the normalized TF IDs so we can properly match
        added = self.comparator.identify_added_resources(
            actual_resources,
            tf_normalized_ids,
            id_extractor=lambda rid, rtype: self._extract_base_id(rid, rtype),
        )
        drifts.extend(added)

        # Check for removed/unscanned resources (in TF but not in AWS)
        # Split into two categories:
        # - REMOVED: Resource type has scanner but resource not found
        # - UNSCANNED: Resource type has no scanner coverage
        removed_or_unscanned = self.comparator.identify_removed_resources(
            tf_state.resources,
            actual_base_ids,
            id_normalizer=self._normalize_tf_id,
        )

        # Categorize: REMOVED vs UNSCANNED
        for drift in removed_or_unscanned:
            if not has_scanner_coverage(drift.resource_type):
                # No scanner for this type - mark as UNSCANNED, not REMOVED
                drift.drift_type = DriftType.UNSCANNED
        drifts.extend(removed_or_unscanned)

        # 5. Build report
        end_time = time.time()

        report = DriftReport(
            total_resources=len(tf_normalized_ids | actual_base_ids),
            drifted_resources=len(
                [d for d in drifts if d.drift_type != DriftType.UNSCANNED]
            ),
            added_resources=len([d for d in drifts if d.drift_type == DriftType.ADDED]),
            removed_resources=len(
                [d for d in drifts if d.drift_type == DriftType.REMOVED]
            ),
            modified_resources=len(
                [d for d in drifts if d.drift_type == DriftType.MODIFIED]
            ),
            unscanned_resources=len(
                [d for d in drifts if d.drift_type == DriftType.UNSCANNED]
            ),
            drifts=drifts,
            state_file=state_source,
            region=self.region,
            scan_duration_seconds=round(end_time - start_time, 2),
        )

        logger.info(
            f"Drift detection complete: {report.drifted_resources} drifts found"
        )

        return report

    def _extract_base_id(self, full_id: str, resource_type: str = "") -> str:
        """Extract base resource ID for matching with TF state.

        Delegates to IdentityResolver for metadata-driven normalization.
        This method is kept for backward compatibility.

        Args:
            full_id: Full resource ID from scanner (may have prefix or ARN)
            resource_type: Terraform resource type for strategy lookup

        Returns:
            Normalized canonical ID for matching
        """
        return IdentityResolver.normalize_scanner_id(full_id, resource_type)

    def _normalize_tf_id(self, resource_id: str, resource_type: str) -> str:
        """Normalize TF state ID to canonical form.

        Delegates to IdentityResolver for metadata-driven normalization.
        This method is kept for backward compatibility.

        Args:
            resource_id: Resource ID from Terraform state
            resource_type: Terraform resource type for strategy lookup

        Returns:
            Normalized canonical ID for matching
        """
        return IdentityResolver.normalize_tf_state_id(resource_id, resource_type)

    def _filter_by_vpc(self, resources: list[Any], vpc_id: str) -> list[Any]:
        """Filter resources to only include those in a specific VPC."""
        filtered = []
        for resource in resources:
            # Check if resource has vpc_id in config
            if hasattr(resource, "config") and isinstance(resource.config, dict):
                if resource.config.get("vpc_id") == vpc_id:
                    filtered.append(resource)
                    continue

            # Also check for the resource itself being the VPC
            if resource.id == vpc_id:
                filtered.append(resource)

        return filtered

    def _extract_attributes(self, resource: Any) -> dict[str, Any]:
        """Extract comparable attributes from scanner resource."""
        attrs: dict[str, Any] = {}

        # Copy all config attributes
        if hasattr(resource, "config") and isinstance(resource.config, dict):
            attrs.update(resource.config)

        # Add common attributes from resource object
        for attr in ["name", "id", "arn", "original_name"]:
            if hasattr(resource, attr):
                value = getattr(resource, attr)
                if value is not None:
                    attrs[attr] = value

        # Map terraform_name to name if not already set
        if "name" not in attrs and hasattr(resource, "terraform_name"):
            attrs["name"] = resource.terraform_name

        return attrs
