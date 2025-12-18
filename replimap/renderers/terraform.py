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

        # Add custom tests
        self.env.tests["tf_ref"] = self._is_tf_ref_test

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

        # Generate supporting Terraform files
        self._generate_versions(output_dir, written_files)
        self._generate_providers(output_dir, written_files)
        self._generate_data_sources(output_dir, written_files)
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

        # Resolve duplicates using numeric suffixes
        for resource_type, names in type_names.items():
            for name, resources in names.items():
                if len(resources) > 1:
                    logger.warning(
                        f"Found {len(resources)} {resource_type} resources "
                        f"with terraform_name '{name}', making unique"
                    )
                    # Track all names used to ensure uniqueness
                    used_names: set[str] = {name}
                    for i, resource in enumerate(resources):
                        if i > 0:
                            # Use numeric suffix to guarantee uniqueness
                            suffix_num = i
                            new_name = f"{name}_{suffix_num}"
                            # Ensure the new name isn't already used
                            while new_name in used_names:
                                suffix_num += 1
                                new_name = f"{name}_{suffix_num}"
                            used_names.add(new_name)
                            resource.terraform_name = new_name
                            logger.info(
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

    def _generate_versions(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate versions.tf with Terraform and provider version constraints."""
        versions = """# Generated by RepliMap
# Terraform and provider version constraints

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
}
"""
        file_path = output_dir / "versions.tf"
        with open(file_path, "w") as f:
            f.write(versions)
        written_files["versions.tf"] = file_path
        logger.info("Wrote versions.tf")

    def _generate_providers(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate providers.tf with AWS provider configuration."""
        providers = """# Generated by RepliMap
# AWS Provider Configuration

provider "aws" {
  region = var.aws_region

  # Assume role for cross-account access (optional)
  # assume_role {
  #   role_arn = "arn:aws:iam::${var.aws_account_id}:role/RepliMapDeployRole"
  # }

  default_tags {
    tags = merge(var.common_tags, {
      ManagedBy   = "replimap"
      Environment = var.environment
    })
  }
}
"""
        file_path = output_dir / "providers.tf"
        with open(file_path, "w") as f:
            f.write(providers)
        written_files["providers.tf"] = file_path
        logger.info("Wrote providers.tf")

    def _generate_data_sources(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate data.tf with useful data sources for dynamic values."""
        data_sources = """# Generated by RepliMap
# Data sources for dynamic values (account ID, region, availability zones, etc.)

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Get current AWS region
data "aws_region" "current" {}

# Get available availability zones in the target region
data "aws_availability_zones" "available" {
  state = "available"
}

# Locals for commonly used values
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.id

  # Availability zones - use these for cross-region cloning
  # Maps index to AZ: local.azs[0] = first AZ (e.g., us-east-1a -> ap-southeast-2a)
  azs = data.aws_availability_zones.available.names

  # Helper to map AZ suffix (a, b, c) to target region AZ
  # Usage: local.az_map["a"] returns first AZ in target region
  az_map = {
    "a" = local.azs[0]
    "b" = length(local.azs) > 1 ? local.azs[1] : local.azs[0]
    "c" = length(local.azs) > 2 ? local.azs[2] : local.azs[0]
    "d" = length(local.azs) > 3 ? local.azs[3] : local.azs[0]
    "e" = length(local.azs) > 4 ? local.azs[4] : local.azs[0]
    "f" = length(local.azs) > 5 ? local.azs[5] : local.azs[0]
  }
}

# Example usage in policies:
# "Resource": "arn:aws:sqs:${local.region}:${local.account_id}:queue-name"
#
# For availability zones, use local.az_map with the original AZ suffix:
# Original: us-east-1a -> Use: local.az_map["a"]
"""
        file_path = output_dir / "data.tf"
        with open(file_path, "w") as f:
            f.write(data_sources)
        written_files["data.tf"] = file_path
        logger.info("Wrote data.tf")

    def _generate_variables(
        self,
        graph: GraphEngine,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate variables.tf with common and resource-specific variables."""
        lines = [
            "# Generated by RepliMap",
            "# Common variables for the replicated environment",
            "",
            'variable "environment" {',
            '  description = "Environment name (e.g., staging, dev)"',
            "  type        = string",
            '  default     = "staging"',
            "}",
            "",
            'variable "aws_account_id" {',
            '  description = "Target AWS account ID"',
            "  type        = string",
            "}",
            "",
            'variable "aws_region" {',
            '  description = "AWS region for deployment"',
            "  type        = string",
            "}",
            "",
            'variable "common_tags" {',
            '  description = "Common tags to apply to all resources"',
            "  type        = map(string)",
            "  default     = {}",
            "}",
        ]

        # Add AMI variable for EC2 instances
        ec2_instances = graph.get_resources_by_type(ResourceType.EC2_INSTANCE)
        if ec2_instances:
            lines.extend([
                "",
                "# EC2 AMI Variable",
                "# NOTE: AMI IDs are region-specific. Update for your target region.",
            ])
            # Get original AMIs for reference
            original_amis = [ec2.config.get("ami", "unknown") for ec2 in ec2_instances]
            lines.extend([
                "",
                'variable "ami_id" {',
                '  description = "AMI ID for EC2 instances"',
                "  type        = string",
                f"  # Original AMIs: {', '.join(set(original_amis))}",
                "}",
            ])

        # Add AMI variables for Launch Templates
        launch_templates = graph.get_resources_by_type(ResourceType.LAUNCH_TEMPLATE)
        if launch_templates:
            lines.extend([
                "",
                "# Launch Template AMI Variables",
                "# NOTE: AMI IDs are region-specific. Update for your target region.",
            ])
            for lt in launch_templates:
                var_name = f"ami_id_{lt.terraform_name}"
                original_ami = lt.config.get("image_id", "unknown")
                lines.extend([
                    "",
                    f'variable "{var_name}" {{',
                    f'  description = "AMI ID for Launch Template {lt.original_name}"',
                    "  type        = string",
                    f"  # Original AMI: {original_ami}",
                    "}",
                ])

        # Add key_name variable if any EC2/Launch Templates use keys
        has_key_name = any(
            ec2.config.get("key_name") for ec2 in ec2_instances
        ) or any(
            lt.config.get("key_name") for lt in launch_templates
        )
        if has_key_name:
            lines.extend([
                "",
                "# SSH Key Pair Variable",
                'variable "key_name" {',
                '  description = "Name of the SSH key pair for EC2 instances"',
                "  type        = string",
                '  default     = ""',
                "}",
            ])

        # Add ACM certificate variable if any listeners use certificates
        lb_listeners = graph.get_resources_by_type(ResourceType.LB_LISTENER)
        has_certificate = any(
            listener.config.get("certificate_arn") for listener in lb_listeners
        )
        if has_certificate:
            original_certs = [
                listener.config.get("certificate_arn")
                for listener in lb_listeners
                if listener.config.get("certificate_arn")
            ]
            lines.extend([
                "",
                "# ACM Certificate Variable",
                "# NOTE: Certificate must match your staging domain",
                'variable "acm_certificate_arn" {',
                '  description = "ARN of ACM certificate for HTTPS listeners"',
                "  type        = string",
                f"  # Original certificate(s): {', '.join(set(original_certs))}",
                "}",
            ])

        # Add RDS password variables
        rds_instances = graph.get_resources_by_type(ResourceType.RDS_INSTANCE)
        if rds_instances:
            lines.extend([
                "",
                "# RDS Database Password Variables",
                "# IMPORTANT: Set these via terraform.tfvars or environment variables",
            ])
            for rds in rds_instances:
                var_name = f"db_password_{rds.terraform_name}"
                lines.extend([
                    "",
                    f'variable "{var_name}" {{',
                    f'  description = "Password for RDS instance {rds.id}"',
                    "  type        = string",
                    "  sensitive   = true",
                    "}",
                ])

        # Add RDS snapshot variables for instances that have snapshots
        rds_with_snapshots = [
            rds for rds in rds_instances
            if rds.config.get("snapshot_identifier")
        ]
        if rds_with_snapshots:
            lines.extend([
                "",
                "# RDS Snapshot Variables (optional - leave empty to create fresh DB)",
            ])
            for rds in rds_with_snapshots:
                var_name = f"db_snapshot_{rds.terraform_name}"
                original_snapshot = rds.config.get("snapshot_identifier", "")
                lines.extend([
                    "",
                    f'variable "{var_name}" {{',
                    f'  description = "Snapshot ID to restore RDS instance {rds.id} from (leave empty for fresh DB)"',
                    "  type        = string",
                    '  default     = ""',
                    f"  # Original snapshot: {original_snapshot}",
                    "}",
                ])

        lines.append("")  # Trailing newline
        file_path = output_dir / "variables.tf"
        with open(file_path, "w") as f:
            f.write("\n".join(lines))
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

        # Add RDS endpoint outputs
        rds_instances = graph.get_resources_by_type(ResourceType.RDS_INSTANCE)
        for rds in rds_instances:
            outputs_lines.append(f'''output "{rds.terraform_name}_endpoint" {{
  description = "Endpoint for RDS instance {rds.original_name}"
  value       = aws_db_instance.{rds.terraform_name}.endpoint
}}
''')

        # Add Load Balancer DNS outputs
        lbs = graph.get_resources_by_type(ResourceType.LB)
        for lb in lbs:
            outputs_lines.append(f'''output "{lb.terraform_name}_dns_name" {{
  description = "DNS name for Load Balancer {lb.original_name}"
  value       = aws_lb.{lb.terraform_name}.dns_name
}}
''')

        file_path = output_dir / "outputs.tf"
        with open(file_path, "w") as f:
            f.write("\n".join(outputs_lines))
        written_files["outputs.tf"] = file_path
        logger.info("Wrote outputs.tf")

        # Generate terraform.tfvars.example
        self._generate_tfvars_example(graph, output_dir, written_files)

    def _generate_tfvars_example(
        self,
        graph: GraphEngine,
        output_dir: Path,
        written_files: dict[str, Path],
    ) -> None:
        """Generate terraform.tfvars.example with sample variable values."""
        lines = [
            "# Generated by RepliMap",
            "# Copy this file to terraform.tfvars and fill in the values",
            "",
            "# Required variables",
            'environment    = "staging"',
            'aws_account_id = "123456789012"  # Replace with your account ID',
            'aws_region     = "ap-southeast-2"  # Replace with your region',
            "",
            "# Optional common tags",
            "common_tags = {",
            '  Project = "replimap-staging"',
            '  Team    = "platform"',
            "}",
        ]

        # Add RDS password placeholders
        rds_instances = graph.get_resources_by_type(ResourceType.RDS_INSTANCE)
        if rds_instances:
            lines.extend([
                "",
                "# RDS Database Passwords",
                "# WARNING: Do not commit actual passwords to version control!",
                "# Consider using environment variables: TF_VAR_db_password_xxx",
            ])
            for rds in rds_instances:
                var_name = f"db_password_{rds.terraform_name}"
                lines.append(f'{var_name} = "CHANGE_ME"')

        lines.append("")  # Trailing newline
        file_path = output_dir / "terraform.tfvars.example"
        with open(file_path, "w") as f:
            f.write("\n".join(lines))
        written_files["terraform.tfvars.example"] = file_path
        logger.info("Wrote terraform.tfvars.example")

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

    @staticmethod
    def _is_tf_ref_test(value: str) -> bool:
        """
        Test if a value is already a Terraform resource reference.

        Terraform references look like: aws_vpc.name.id, aws_subnet.name.id, etc.
        This is used to detect when NetworkRemapTransformer has already converted
        an ID to a Terraform reference, so templates should output it without quotes.

        Args:
            value: The string to test

        Returns:
            True if the value looks like a Terraform reference
        """
        if not isinstance(value, str):
            return False

        # Terraform references pattern: aws_<type>.<name>.<attribute>
        # Common patterns: aws_vpc.name.id, aws_subnet.name.id, aws_security_group.name.id
        tf_ref_prefixes = (
            "aws_vpc.",
            "aws_subnet.",
            "aws_security_group.",
            "aws_instance.",
            "aws_db_instance.",
            "aws_db_subnet_group.",
            "aws_lb.",
            "aws_lb_target_group.",
            "aws_s3_bucket.",
            "aws_elasticache_cluster.",
            "aws_internet_gateway.",
            "aws_nat_gateway.",
            "aws_route_table.",
            "aws_ebs_volume.",
            "aws_sqs_queue.",
            "aws_sns_topic.",
            "aws_launch_template.",
            "aws_autoscaling_group.",
        )

        return any(value.startswith(prefix) for prefix in tf_ref_prefixes)
