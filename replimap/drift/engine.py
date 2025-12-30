"""Main drift detection orchestration."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from replimap.drift.comparator import DriftComparator
from replimap.drift.models import DriftReport, DriftType
from replimap.drift.state_parser import TerraformStateParser

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

        # 3. Build lookup maps
        # Note: Scanner IDs use format {account}:{region}:{resource_id}
        # while TF state uses just {resource_id}
        # We need to extract the base resource ID for matching
        tf_by_id = {r.id: r for r in tf_state.resources}
        tf_ids = set(tf_by_id.keys())

        # Build map from base resource ID to scanner resource
        actual_by_base_id: dict[str, Any] = {}
        for r in actual_resources:
            base_id = self._extract_base_id(r.id)
            actual_by_base_id[base_id] = r
        actual_base_ids = set(actual_by_base_id.keys())

        logger.debug(f"TF IDs sample: {list(tf_ids)[:5]}")
        logger.debug(f"AWS IDs sample: {list(actual_base_ids)[:5]}")

        # 4. Compare resources
        logger.info("Comparing resources...")
        drifts = []

        # Check for modifications (resources in both TF and AWS)
        for resource_id in tf_ids & actual_base_ids:
            tf_resource = tf_by_id[resource_id]
            actual_resource = actual_by_base_id[resource_id]

            # Get actual attributes (convert from scanner format)
            actual_attrs = self._extract_attributes(actual_resource)

            drift = self.comparator.compare_resource(tf_resource, actual_attrs)
            if drift.is_drifted:
                drifts.append(drift)

        # Check for added resources (in AWS but not in TF)
        added = self.comparator.identify_added_resources(
            actual_resources, tf_ids, id_extractor=self._extract_base_id
        )
        drifts.extend(added)

        # Check for removed resources (in TF but not in AWS)
        removed = self.comparator.identify_removed_resources(
            tf_state.resources, actual_base_ids
        )
        drifts.extend(removed)

        # 5. Build report
        end_time = time.time()

        report = DriftReport(
            total_resources=len(tf_ids | actual_base_ids),
            drifted_resources=len(drifts),
            added_resources=len([d for d in drifts if d.drift_type == DriftType.ADDED]),
            removed_resources=len(
                [d for d in drifts if d.drift_type == DriftType.REMOVED]
            ),
            modified_resources=len(
                [d for d in drifts if d.drift_type == DriftType.MODIFIED]
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

    def _extract_base_id(self, full_id: str) -> str:
        """Extract base resource ID from scanner's prefixed format.

        Scanner IDs use format: {account_id}:{region}:{resource_id}
        TF state uses just: {resource_id}

        Examples:
            542859091916:ap-southeast-2:sg-072c65dfd31d69b92 -> sg-072c65dfd31d69b92
            sg-072c65dfd31d69b92 -> sg-072c65dfd31d69b92
            542859091916:ap-southeast-2:arn:aws:sqs:... -> arn:aws:sqs:...
        """
        if ":" not in full_id:
            return full_id

        parts = full_id.split(":")

        # Check if first part looks like account ID (12 digits)
        if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 12:
            # Format is account:region:resource_id
            # Resource ID is everything after the second colon
            return ":".join(parts[2:])

        # Check for ARN format (arn:aws:service:region:account:...)
        if full_id.startswith("arn:"):
            return full_id

        # Default: return as-is
        return full_id

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
