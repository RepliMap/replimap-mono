"""
Downsize Transformer for RepliMap.

Reduces instance sizes for cost savings in staging environments.
Maps production instance types to smaller, cheaper alternatives.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from replimap.core.models import ResourceType

from .base import BaseTransformer

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


# Default instance type mappings for EC2
EC2_DOWNSIZE_MAP: dict[str, str] = {
    # M5 family -> T3
    "m5.large": "t3.small",
    "m5.xlarge": "t3.medium",
    "m5.2xlarge": "t3.medium",
    "m5.4xlarge": "t3.large",
    "m5.8xlarge": "t3.large",
    "m5.12xlarge": "t3.xlarge",
    "m5.16xlarge": "t3.xlarge",
    "m5.24xlarge": "t3.2xlarge",
    # M6i family -> T3
    "m6i.large": "t3.small",
    "m6i.xlarge": "t3.medium",
    "m6i.2xlarge": "t3.medium",
    "m6i.4xlarge": "t3.large",
    # R5 family (memory-optimized) -> T3
    "r5.large": "t3.medium",
    "r5.xlarge": "t3.large",
    "r5.2xlarge": "t3.large",
    "r5.4xlarge": "t3.xlarge",
    # R6i family -> T3
    "r6i.large": "t3.medium",
    "r6i.xlarge": "t3.large",
    "r6i.2xlarge": "t3.large",
    # C5 family (compute-optimized) -> T3
    "c5.large": "t3.small",
    "c5.xlarge": "t3.medium",
    "c5.2xlarge": "t3.medium",
    "c5.4xlarge": "t3.large",
    # C6i family -> T3
    "c6i.large": "t3.small",
    "c6i.xlarge": "t3.medium",
    "c6i.2xlarge": "t3.medium",
    # T3 stays T3 (already cost-effective)
    "t3.micro": "t3.micro",
    "t3.small": "t3.micro",
    "t3.medium": "t3.small",
    "t3.large": "t3.medium",
    "t3.xlarge": "t3.medium",
    "t3.2xlarge": "t3.large",
    # T2 -> T3
    "t2.micro": "t3.micro",
    "t2.small": "t3.micro",
    "t2.medium": "t3.small",
    "t2.large": "t3.medium",
}

# Default instance type mappings for RDS
RDS_DOWNSIZE_MAP: dict[str, str] = {
    # db.m5 family -> db.t3
    "db.m5.large": "db.t3.medium",
    "db.m5.xlarge": "db.t3.medium",
    "db.m5.2xlarge": "db.t3.large",
    "db.m5.4xlarge": "db.t3.large",
    "db.m5.8xlarge": "db.t3.xlarge",
    "db.m5.12xlarge": "db.t3.2xlarge",
    # db.m6g family -> db.t3
    "db.m6g.large": "db.t3.medium",
    "db.m6g.xlarge": "db.t3.medium",
    "db.m6g.2xlarge": "db.t3.large",
    # db.r5 family (memory-optimized) -> db.t3
    "db.r5.large": "db.t3.medium",
    "db.r5.xlarge": "db.t3.large",
    "db.r5.2xlarge": "db.t3.large",
    "db.r5.4xlarge": "db.t3.xlarge",
    # db.r6g family -> db.t3
    "db.r6g.large": "db.t3.medium",
    "db.r6g.xlarge": "db.t3.large",
    # db.t3 stays db.t3
    "db.t3.micro": "db.t3.micro",
    "db.t3.small": "db.t3.micro",
    "db.t3.medium": "db.t3.small",
    "db.t3.large": "db.t3.medium",
    "db.t3.xlarge": "db.t3.medium",
    "db.t3.2xlarge": "db.t3.large",
    # db.t2 -> db.t3
    "db.t2.micro": "db.t3.micro",
    "db.t2.small": "db.t3.micro",
    "db.t2.medium": "db.t3.small",
    "db.t2.large": "db.t3.medium",
}


class DownsizeTransformer(BaseTransformer):
    """
    Reduces instance sizes for cost savings.

    This transformer:
    1. Maps EC2 instance types to smaller alternatives
    2. Maps RDS instance classes to smaller alternatives
    3. Optionally disables Multi-AZ for RDS (single staging DB)

    The mappings are designed to maintain functionality while
    significantly reducing costs for non-production environments.
    """

    name = "DownsizeTransformer"

    def __init__(
        self,
        ec2_map: dict[str, str] | None = None,
        rds_map: dict[str, str] | None = None,
        disable_multi_az: bool = True,
        min_storage: int = 20,
    ) -> None:
        """
        Initialize the downsizer.

        Args:
            ec2_map: Custom EC2 instance type mapping (or use default)
            rds_map: Custom RDS instance class mapping (or use default)
            disable_multi_az: Whether to disable Multi-AZ for RDS
            min_storage: Minimum storage size (GB) for RDS
        """
        self.ec2_map = ec2_map or EC2_DOWNSIZE_MAP
        self.rds_map = rds_map or RDS_DOWNSIZE_MAP
        self.disable_multi_az = disable_multi_az
        self.min_storage = min_storage
        self._ec2_downsized = 0
        self._rds_downsized = 0

    def transform(self, graph: GraphEngine) -> GraphEngine:
        """
        Downsize all applicable resources in the graph.

        Args:
            graph: The GraphEngine to transform

        Returns:
            The same GraphEngine with downsized configurations
        """
        self._ec2_downsized = 0
        self._rds_downsized = 0

        for resource in graph.iter_resources():
            if resource.resource_type == ResourceType.EC2_INSTANCE:
                self._downsize_ec2(resource)
            elif resource.resource_type == ResourceType.RDS_INSTANCE:
                self._downsize_rds(resource)

        logger.info(
            f"Downsized {self._ec2_downsized} EC2 instances, "
            f"{self._rds_downsized} RDS instances"
        )

        return graph

    def _downsize_ec2(self, resource) -> None:
        """
        Downsize an EC2 instance.

        Args:
            resource: The ResourceNode to modify
        """
        current_type = resource.config.get("instance_type", "")

        if current_type in self.ec2_map:
            new_type = self.ec2_map[current_type]
            if new_type != current_type:
                logger.debug(
                    f"Downsizing EC2 {resource.id}: {current_type} -> {new_type}"
                )
                resource.config["instance_type"] = new_type
                resource.config["_original_instance_type"] = current_type
                self._ec2_downsized += 1
        else:
            # Unknown instance type - try to find a reasonable default
            if current_type.startswith(("m5.", "m6i.", "r5.", "r6i.", "c5.", "c6i.")):
                # Large production instance without mapping - use t3.medium
                logger.warning(
                    f"Unknown instance type {current_type} for {resource.id}, "
                    "defaulting to t3.medium"
                )
                resource.config["instance_type"] = "t3.medium"
                resource.config["_original_instance_type"] = current_type
                self._ec2_downsized += 1

    def _downsize_rds(self, resource) -> None:
        """
        Downsize an RDS instance.

        Args:
            resource: The ResourceNode to modify
        """
        current_class = resource.config.get("instance_class", "")

        # Downsize instance class
        if current_class in self.rds_map:
            new_class = self.rds_map[current_class]
            if new_class != current_class:
                logger.debug(
                    f"Downsizing RDS {resource.id}: {current_class} -> {new_class}"
                )
                resource.config["instance_class"] = new_class
                resource.config["_original_instance_class"] = current_class
                self._rds_downsized += 1
        else:
            # Unknown instance class - try to find a reasonable default
            if current_class.startswith(("db.m5.", "db.m6", "db.r5.", "db.r6")):
                logger.warning(
                    f"Unknown RDS class {current_class} for {resource.id}, "
                    "defaulting to db.t3.medium"
                )
                resource.config["instance_class"] = "db.t3.medium"
                resource.config["_original_instance_class"] = current_class
                self._rds_downsized += 1

        # Disable Multi-AZ
        if self.disable_multi_az and resource.config.get("multi_az"):
            logger.debug(f"Disabling Multi-AZ for {resource.id}")
            resource.config["multi_az"] = False
            resource.config["_original_multi_az"] = True

        # Reduce storage if too large
        current_storage = resource.config.get("allocated_storage", 0)
        if current_storage > 100:
            # Reduce large storage allocations
            new_storage = max(self.min_storage, current_storage // 4)
            if new_storage != current_storage:
                logger.debug(
                    f"Reducing storage for {resource.id}: "
                    f"{current_storage}GB -> {new_storage}GB"
                )
                resource.config["allocated_storage"] = new_storage
                resource.config["_original_allocated_storage"] = current_storage
