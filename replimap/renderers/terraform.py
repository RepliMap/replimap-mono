"""
Terraform Renderer for RepliMap.

Converts the resource graph to Terraform HCL files using Jinja2 templates.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape

from replimap.core.models import ResourceType

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)

# Template directory relative to this file (inside package)
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


class TerraformRenderer:
    """
    Renders the resource graph to Terraform HCL files.

    Output structure:
    - vpc.tf: VPCs and Subnets
    - security_groups.tf: Security Groups
    - ec2.tf: EC2 Instances
    - rds.tf: RDS Instances and DB Subnet Groups
    - s3.tf: S3 Buckets
    - variables.tf: Extracted variables
    - outputs.tf: Useful outputs
    """

    # Mapping of resource types to output files
    FILE_MAPPING = {
        # Phase 1 (MVP)
        ResourceType.VPC: "vpc.tf",
        ResourceType.SUBNET: "vpc.tf",
        ResourceType.SECURITY_GROUP: "security_groups.tf",
        ResourceType.EC2_INSTANCE: "ec2.tf",
        ResourceType.S3_BUCKET: "s3.tf",
        ResourceType.RDS_INSTANCE: "rds.tf",
        ResourceType.DB_SUBNET_GROUP: "rds.tf",
        # Phase 2 - Networking
        ResourceType.ROUTE_TABLE: "networking.tf",
        ResourceType.INTERNET_GATEWAY: "networking.tf",
        ResourceType.NAT_GATEWAY: "networking.tf",
        ResourceType.VPC_ENDPOINT: "networking.tf",
        # Phase 2 - Compute
        ResourceType.LAUNCH_TEMPLATE: "compute.tf",
        ResourceType.AUTOSCALING_GROUP: "compute.tf",
        ResourceType.LB: "alb.tf",
        ResourceType.LB_LISTENER: "alb.tf",
        ResourceType.LB_TARGET_GROUP: "alb.tf",
        # Phase 2 - Database
        ResourceType.DB_PARAMETER_GROUP: "rds.tf",
        ResourceType.ELASTICACHE_CLUSTER: "elasticache.tf",
        ResourceType.ELASTICACHE_SUBNET_GROUP: "elasticache.tf",
        # Phase 2 - Storage/Messaging
        ResourceType.EBS_VOLUME: "storage.tf",
        ResourceType.S3_BUCKET_POLICY: "s3.tf",
        ResourceType.SQS_QUEUE: "messaging.tf",
        ResourceType.SNS_TOPIC: "messaging.tf",
    }

    # Mapping of resource types to template files
    TEMPLATE_MAPPING = {
        # Phase 1 (MVP)
        ResourceType.VPC: "vpc.tf.j2",
        ResourceType.SUBNET: "subnet.tf.j2",
        ResourceType.SECURITY_GROUP: "security_group.tf.j2",
        ResourceType.EC2_INSTANCE: "ec2_instance.tf.j2",
        ResourceType.S3_BUCKET: "s3_bucket.tf.j2",
        ResourceType.RDS_INSTANCE: "rds_instance.tf.j2",
        ResourceType.DB_SUBNET_GROUP: "db_subnet_group.tf.j2",
        # Phase 2 - Networking
        ResourceType.ROUTE_TABLE: "route_table.tf.j2",
        ResourceType.INTERNET_GATEWAY: "internet_gateway.tf.j2",
        ResourceType.NAT_GATEWAY: "nat_gateway.tf.j2",
        ResourceType.VPC_ENDPOINT: "vpc_endpoint.tf.j2",
        # Phase 2 - Compute
        ResourceType.LAUNCH_TEMPLATE: "launch_template.tf.j2",
        ResourceType.AUTOSCALING_GROUP: "autoscaling_group.tf.j2",
        ResourceType.LB: "lb.tf.j2",
        ResourceType.LB_LISTENER: "lb_listener.tf.j2",
        ResourceType.LB_TARGET_GROUP: "lb_target_group.tf.j2",
        # Phase 2 - Database
        ResourceType.DB_PARAMETER_GROUP: "db_parameter_group.tf.j2",
        ResourceType.ELASTICACHE_CLUSTER: "elasticache_cluster.tf.j2",
        ResourceType.ELASTICACHE_SUBNET_GROUP: "elasticache_subnet_group.tf.j2",
        # Phase 2 - Storage/Messaging
        ResourceType.EBS_VOLUME: "ebs_volume.tf.j2",
        ResourceType.S3_BUCKET_POLICY: "s3_bucket_policy.tf.j2",
        ResourceType.SQS_QUEUE: "sqs_queue.tf.j2",
        ResourceType.SNS_TOPIC: "sns_topic.tf.j2",
    }

    def __init__(self, template_dir: Path | None = None) -> None:
        """
        Initialize the renderer.

        Args:
            template_dir: Path to Jinja2 templates (defaults to built-in)
        """
        self.template_dir = template_dir or TEMPLATE_DIR

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["terraform_name"] = self._terraform_name_filter
        self.env.filters["quote"] = self._quote_filter
        self.env.filters["quote_key"] = self._quote_key_filter
        self.env.filters["tf_ref"] = self._tf_ref_filter

        # Track used terraform names for uniqueness
        self._used_names: dict[str, set[str]] = {}

    def render(self, graph: GraphEngine, output_dir: Path) -> dict[str, Path]:
        """
        Render the graph to Terraform files.

        Args:
            graph: The GraphEngine containing resources
            output_dir: Directory to write .tf files

        Returns:
            Dictionary mapping filenames to their paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Rendering Terraform to {output_dir}")

        # Ensure unique terraform names before rendering
        self._ensure_unique_names(graph)

        # Group resources by output file
        file_contents: dict[str, list[str]] = {}

        for resource in graph.topological_sort():
            template_name = self.TEMPLATE_MAPPING.get(resource.resource_type)
            output_file = self.FILE_MAPPING.get(resource.resource_type)

            if not template_name or not output_file:
                logger.warning(
                    f"No template for resource type: {resource.resource_type}"
                )
                continue

            try:
                template = self.env.get_template(template_name)
                rendered = template.render(resource=resource, graph=graph)

                if output_file not in file_contents:
                    file_contents[output_file] = []
                file_contents[output_file].append(rendered)

            except Exception as e:
                logger.error(f"Error rendering {resource.id}: {e}")

        # Write files
        written_files: dict[str, Path] = {}
        for filename, contents in file_contents.items():
            file_path = output_dir / filename
            with open(file_path, "w") as f:
                f.write("\n\n".join(contents))
            written_files[filename] = file_path
            logger.info(f"Wrote {filename} ({len(contents)} resources)")

        # Generate variables.tf and outputs.tf
        self._generate_variables(graph, output_dir, written_files)
        self._generate_outputs(graph, output_dir, written_files)

        return written_files

    def _ensure_unique_names(self, graph: GraphEngine) -> None:
        """
        Ensure all resources have unique terraform names within their type.

        If multiple resources of the same type have the same terraform_name,
        append a numeric suffix to make them unique.
        """
        # Group resources by type and terraform_name
        type_names: dict[str, dict[str, list[object]]] = {}

        for resource in graph.iter_resources():
            resource_type = str(resource.resource_type)
            if resource_type not in type_names:
                type_names[resource_type] = {}

            name = resource.terraform_name or "unnamed"
            if name not in type_names[resource_type]:
                type_names[resource_type][name] = []
            type_names[resource_type][name].append(resource)

        # Resolve duplicates
        for resource_type, names in type_names.items():
            for name, resources in names.items():
                if len(resources) > 1:
                    logger.warning(
                        f"Found {len(resources)} {resource_type} resources "
                        f"with terraform_name '{name}', making unique"
                    )
                    for i, resource in enumerate(resources):
                        if i > 0:
                            # Append resource ID suffix to make unique
                            # Use last 8 chars of ID for brevity
                            suffix = resource.id.replace("-", "_")[-8:]
                            new_name = f"{name}_{suffix}"
                            resource.terraform_name = new_name
                            logger.debug(
                                f"Renamed {resource.id} from '{name}' to '{new_name}'"
                            )

    def preview(self, graph: GraphEngine) -> dict[str, list[str]]:
        """
        Preview what would be generated without writing files.

        Args:
            graph: The GraphEngine containing resources

        Returns:
            Dictionary mapping filenames to lists of resource IDs
        """
        preview: dict[str, list[str]] = {}

        for resource in graph.iter_resources():
            output_file = self.FILE_MAPPING.get(resource.resource_type)
            if output_file:
                if output_file not in preview:
                    preview[output_file] = []
                preview[output_file].append(resource.id)

        return preview

    def _generate_variables(
        self,
        graph: GraphEngine,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate variables.tf with common variables."""
        variables = """# Generated by RepliMap
# Common variables for the replicated environment

variable "environment" {
  description = "Environment name (e.g., staging, dev)"
  type        = string
  default     = "staging"
}

variable "aws_account_id" {
  description = "Target AWS account ID"
  type        = string
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
"""
        file_path = output_dir / "variables.tf"
        with open(file_path, "w") as f:
            f.write(variables)
        written_files["variables.tf"] = file_path
        logger.info("Wrote variables.tf")

    def _generate_outputs(
        self,
        graph: GraphEngine,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate outputs.tf with useful outputs."""
        outputs_lines = [
            "# Generated by RepliMap",
            "# Useful outputs for reference",
            "",
        ]

        # Add VPC outputs
        vpcs = graph.get_resources_by_type(ResourceType.VPC)
        for vpc in vpcs:
            outputs_lines.append(f'''output "{vpc.terraform_name}_id" {{
  description = "ID of VPC {vpc.original_name}"
  value       = aws_vpc.{vpc.terraform_name}.id
}}
''')

        file_path = output_dir / "outputs.tf"
        with open(file_path, "w") as f:
            f.write("\n".join(outputs_lines))
        written_files["outputs.tf"] = file_path
        logger.info("Wrote outputs.tf")

    @staticmethod
    def _terraform_name_filter(value: str) -> str:
        """Convert a string to a valid Terraform name."""
        result = ""
        for char in value:
            if char.isalnum() or char in "_-":
                result += char
            else:
                result += "_"
        if result and not (result[0].isalpha() or result[0] == "_"):
            result = f"r_{result}"
        return result or "unnamed"

    @staticmethod
    def _quote_filter(value: str) -> str:
        """Quote a string for Terraform."""
        if value is None:
            return '""'
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    @staticmethod
    def _quote_key_filter(key: str) -> str:
        """
        Quote a tag key for Terraform if necessary.

        Terraform keys must be valid identifiers or quoted strings.
        Keys with spaces, special characters, or starting with digits need quotes.
        """
        if not key:
            return '""'
        # Check if key is a valid Terraform identifier
        # Must start with letter or underscore, contain only alphanumeric, underscore, hyphen
        is_valid_identifier = (
            (key[0].isalpha() or key[0] == "_")
            and all(c.isalnum() or c in "_-" for c in key)
        )
        if is_valid_identifier:
            return key
        # Quote the key
        escaped = key.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    @staticmethod
    def _tf_ref_filter(resource_node: object, resource_type: str) -> str:
        """
        Generate a Terraform resource reference.

        Returns the reference (e.g., 'aws_vpc.my_vpc.id') or an empty string
        if the resource is not valid.
        """
        if resource_node is None:
            return ""
        terraform_name = getattr(resource_node, "terraform_name", None)
        if not terraform_name:
            return ""
        return f"{resource_type}.{terraform_name}.id"
