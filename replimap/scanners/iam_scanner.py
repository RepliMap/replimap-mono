"""
IAM Scanner for RepliMap.

Scans IAM roles, policies, and instance profiles.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from botocore.exceptions import ClientError

from replimap.core.models import DependencyType, ResourceNode, ResourceType
from replimap.core.rate_limiter import rate_limited_paginate
from replimap.scanners.base import BaseScanner, ScannerRegistry, parallel_process_items

if TYPE_CHECKING:
    from replimap.core import GraphEngine

logger = logging.getLogger(__name__)


@ScannerRegistry.register
class IAMRoleScanner(BaseScanner):
    """
    Scanner for IAM Roles.

    Captures:
    - Role name (used as ID in TF state)
    - ARN
    - Assume role policy
    - Path
    - Description
    - Tags
    """

    resource_types: ClassVar[list[str]] = ["aws_iam_role"]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all IAM Roles."""
        # IAM is a global service
        logger.info("Scanning IAM Roles (global)...")

        iam = self.get_client("iam")

        try:
            # First, collect all roles from pagination
            roles_to_process: list[dict[str, Any]] = []
            paginator = iam.get_paginator("list_roles")
            for page in rate_limited_paginate("iam")(paginator.paginate()):
                for role in page.get("Roles", []):
                    # Skip AWS service-linked roles early
                    path = role.get("Path", "/")
                    if not path.startswith("/aws-service-role/"):
                        roles_to_process.append(role)
                    else:
                        logger.debug(f"Skipping service-linked role: {role.get('RoleName')}")

            # Process roles in parallel (tag fetching is the bottleneck)
            results, failures = parallel_process_items(
                items=roles_to_process,
                processor=lambda role: self._process_role(role, iam, graph),
                description="IAM Roles",
            )

            role_count = sum(1 for r in results if r)
            logger.info(f"Scanned {role_count} IAM Roles")

            if failures:
                for role, error in failures:
                    logger.warning(f"Failed to process role {role.get('RoleName')}: {error}")

        except ClientError as e:
            self._handle_aws_error(e, "list_roles")

    def _process_role(
        self,
        role: dict[str, Any],
        iam_client: Any,
        graph: GraphEngine,
    ) -> bool:
        """Process a single IAM Role."""
        role_name = role.get("RoleName", "")
        role_arn = role.get("Arn", "")
        path = role.get("Path", "/")

        if not role_name:
            return False

        # Get the assume role policy document
        assume_role_policy = role.get("AssumeRolePolicyDocument")
        if isinstance(assume_role_policy, dict):
            assume_role_policy = json.dumps(assume_role_policy, sort_keys=True)

        # Get tags
        tags = {}
        try:
            tags_response = iam_client.list_role_tags(RoleName=role_name)
            for tag in tags_response.get("Tags", []):
                tags[tag["Key"]] = tag["Value"]
        except ClientError as e:
            logger.debug(f"Could not get tags for role {role_name}: {e}")

        # Build config
        config = {
            "name": role_name,
            "path": path,
            "description": role.get("Description", ""),
            "assume_role_policy": assume_role_policy,
            "max_session_duration": role.get("MaxSessionDuration"),
            "create_date": str(role.get("CreateDate", "")),
            "permissions_boundary": role.get("PermissionsBoundary", {}).get(
                "PermissionsBoundaryArn"
            ),
        }

        # Use role name as ID (matches TF state format)
        node = ResourceNode(
            id=role_name,
            resource_type=ResourceType.IAM_ROLE,
            region="global",  # IAM is global
            config=config,
            arn=role_arn,
            tags=tags,
        )

        graph.add_resource(node)
        logger.debug(f"Added IAM Role: {role_name}")
        return True


@ScannerRegistry.register
class IAMInstanceProfileScanner(BaseScanner):
    """
    Scanner for IAM Instance Profiles.

    Captures:
    - Instance profile name (used as ID in TF state)
    - ARN
    - Associated roles
    - Path
    """

    resource_types: ClassVar[list[str]] = ["aws_iam_instance_profile"]

    # Instance profiles depend on roles
    depends_on_types: ClassVar[list[str]] = ["aws_iam_role"]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all IAM Instance Profiles."""
        logger.info("Scanning IAM Instance Profiles (global)...")

        iam = self.get_client("iam")
        profile_count = 0

        try:
            paginator = iam.get_paginator("list_instance_profiles")
            # IAM is a global service - no region parameter
            for page in rate_limited_paginate("iam")(paginator.paginate()):
                for profile in page.get("InstanceProfiles", []):
                    if self._process_instance_profile(profile, graph):
                        profile_count += 1

            logger.info(f"Scanned {profile_count} IAM Instance Profiles")

        except ClientError as e:
            self._handle_aws_error(e, "list_instance_profiles")

    def _process_instance_profile(
        self,
        profile: dict[str, Any],
        graph: GraphEngine,
    ) -> bool:
        """Process a single IAM Instance Profile."""
        profile_name = profile.get("InstanceProfileName", "")
        profile_arn = profile.get("Arn", "")

        if not profile_name:
            return False

        # Get associated roles
        roles = []
        for role in profile.get("Roles", []):
            roles.append(role.get("RoleName", ""))

        # Build config
        config = {
            "name": profile_name,
            "path": profile.get("Path", "/"),
            "roles": roles,
            "create_date": str(profile.get("CreateDate", "")),
        }

        # Use profile name as ID (matches TF state format)
        node = ResourceNode(
            id=profile_name,
            resource_type=ResourceType.IAM_INSTANCE_PROFILE,
            region="global",  # IAM is global
            config=config,
            arn=profile_arn,
            tags={},  # Instance profiles don't have tags in API
        )

        graph.add_resource(node)

        # Add dependency edges to associated IAM roles
        for role_name in roles:
            if role_name and graph.get_resource(role_name):
                graph.add_dependency(profile_name, role_name, DependencyType.USES)

        logger.debug(f"Added IAM Instance Profile: {profile_name}")
        return True
