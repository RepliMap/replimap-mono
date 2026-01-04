"""
Import Block Generator for RepliMap.

Generates Terraform import blocks to bridge AWS resources to generated code.
This is THE MISSING LINK that makes RepliMap actually useful.

Without import blocks, generated Terraform code cannot manage existing resources.
With import blocks, terraform plan shows "0 to add" - perfect state sync.

The Seven Laws of Sovereign Code:
5. Refactor, Don't Recreate - Use moved blocks, never destroy to rename.

Requires: Terraform 1.5+ for import blocks
         Terraform 1.1+ for moved blocks (handled by RefactoringEngine)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.core.config import RepliMapConfig

logger = logging.getLogger(__name__)


# Import ID format mappings by resource type
#
# Different AWS resources require different import ID formats:
# - {id}: Use the AWS resource ID (e.g., vpc-12345, i-abcdef)
# - {name}: Use the resource name (e.g., role name, bucket name)
# - {arn}: Use the full ARN
# - {identifier}: Use a specific identifier field
# - COMPLEX_SEE_DOCS: Complex format requiring manual intervention
#
# LEVEL 2 INSIGHT: This list WILL be incomplete!
# Complex resources have unpredictable formats.
# Solution: Allow user overrides via .replimap.yaml
#
# Reference: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
IMPORT_ID_FORMATS: dict[str, str] = {
    # ═══════════════════════════════════════════════════════════════════════════
    # VPC and Networking
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_vpc": "{id}",
    "aws_subnet": "{id}",
    "aws_security_group": "{id}",
    "aws_internet_gateway": "{id}",
    "aws_nat_gateway": "{id}",
    "aws_route_table": "{id}",
    "aws_vpc_endpoint": "{id}",
    "aws_network_interface": "{id}",
    "aws_network_acl": "{id}",
    "aws_eip": "{allocation_id}",
    "aws_vpn_gateway": "{id}",
    "aws_customer_gateway": "{id}",
    "aws_vpc_peering_connection": "{id}",
    "aws_egress_only_internet_gateway": "{id}",
    # Complex networking resources
    "aws_route_table_association": "COMPLEX_SEE_DOCS",  # {subnet_id}/{route_table_id}
    "aws_security_group_rule": "COMPLEX_SEE_DOCS",  # {sg_id}_{type}_{protocol}_{from}_{to}_{source}
    "aws_route": "COMPLEX_SEE_DOCS",  # {route_table_id}_{destination_cidr}
    "aws_vpc_endpoint_route_table_association": "COMPLEX_SEE_DOCS",
    # ═══════════════════════════════════════════════════════════════════════════
    # EC2 Compute
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_instance": "{id}",
    "aws_ebs_volume": "{id}",
    "aws_key_pair": "{key_name}",
    "aws_launch_template": "{id}",
    "aws_autoscaling_group": "{name}",
    "aws_placement_group": "{name}",
    "aws_ami": "{id}",
    "aws_ami_copy": "{id}",
    "aws_spot_instance_request": "{id}",
    "aws_volume_attachment": "COMPLEX_SEE_DOCS",  # {device_name}:{volume_id}:{instance_id}
    # ═══════════════════════════════════════════════════════════════════════════
    # Load Balancing
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_lb": "{arn}",
    "aws_alb": "{arn}",  # Alias for aws_lb
    "aws_lb_listener": "{arn}",
    "aws_alb_listener": "{arn}",
    "aws_lb_target_group": "{arn}",
    "aws_alb_target_group": "{arn}",
    "aws_lb_target_group_attachment": "COMPLEX_SEE_DOCS",
    "aws_lb_listener_rule": "{arn}",
    "aws_lb_listener_certificate": "COMPLEX_SEE_DOCS",
    # ═══════════════════════════════════════════════════════════════════════════
    # RDS / Database
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_db_instance": "{identifier}",
    "aws_db_subnet_group": "{name}",
    "aws_db_parameter_group": "{name}",
    "aws_db_option_group": "{name}",
    "aws_db_cluster": "{identifier}",
    "aws_db_cluster_parameter_group": "{name}",
    "aws_rds_cluster": "{identifier}",
    "aws_db_snapshot": "{identifier}",
    "aws_db_cluster_snapshot": "{identifier}",
    "aws_db_proxy": "{name}",
    "aws_db_event_subscription": "{name}",
    # ═══════════════════════════════════════════════════════════════════════════
    # ElastiCache
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_elasticache_cluster": "{id}",
    "aws_elasticache_subnet_group": "{name}",
    "aws_elasticache_parameter_group": "{name}",
    "aws_elasticache_replication_group": "{id}",
    "aws_elasticache_user": "{user_id}",
    "aws_elasticache_user_group": "{user_group_id}",
    # ═══════════════════════════════════════════════════════════════════════════
    # S3
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_s3_bucket": "{bucket}",
    "aws_s3_bucket_policy": "{bucket}",
    "aws_s3_bucket_versioning": "{bucket}",
    "aws_s3_bucket_acl": "{bucket}",
    "aws_s3_bucket_cors_configuration": "{bucket}",
    "aws_s3_bucket_lifecycle_configuration": "{bucket}",
    "aws_s3_bucket_logging": "{bucket}",
    "aws_s3_bucket_notification": "{bucket}",
    "aws_s3_bucket_public_access_block": "{bucket}",
    "aws_s3_bucket_replication_configuration": "{bucket}",
    "aws_s3_bucket_server_side_encryption_configuration": "{bucket}",
    "aws_s3_bucket_website_configuration": "{bucket}",
    "aws_s3_object": "COMPLEX_SEE_DOCS",  # {bucket}/{key}
    # ═══════════════════════════════════════════════════════════════════════════
    # IAM
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_iam_role": "{name}",
    "aws_iam_policy": "{arn}",
    "aws_iam_user": "{name}",
    "aws_iam_group": "{name}",
    "aws_iam_instance_profile": "{name}",
    "aws_iam_access_key": "{user_name}/{access_key_id}",
    "aws_iam_role_policy": "{role_name}:{policy_name}",
    "aws_iam_user_policy": "{user_name}:{policy_name}",
    "aws_iam_group_policy": "{group_name}:{policy_name}",
    "aws_iam_role_policy_attachment": "{role}/{policy_arn}",
    "aws_iam_user_policy_attachment": "{user}/{policy_arn}",
    "aws_iam_group_policy_attachment": "{group}/{policy_arn}",
    "aws_iam_group_membership": "{group_name}",
    "aws_iam_service_linked_role": "{arn}",
    "aws_iam_openid_connect_provider": "{arn}",
    "aws_iam_saml_provider": "{arn}",
    # ═══════════════════════════════════════════════════════════════════════════
    # Lambda
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_lambda_function": "{name}",
    "aws_lambda_alias": "{function_name}/{alias_name}",
    "aws_lambda_event_source_mapping": "{uuid}",
    "aws_lambda_layer_version": "{arn}",
    "aws_lambda_permission": "{function_name}/{statement_id}",
    "aws_lambda_provisioned_concurrency_config": "{function_name}:{qualifier}",
    "aws_lambda_function_url": "{function_name}",
    # ═══════════════════════════════════════════════════════════════════════════
    # CloudWatch
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_cloudwatch_log_group": "{name}",
    "aws_cloudwatch_log_stream": "{log_group_name}:{log_stream_name}",
    "aws_cloudwatch_metric_alarm": "{name}",
    "aws_cloudwatch_dashboard": "{name}",
    "aws_cloudwatch_event_rule": "{name}",
    "aws_cloudwatch_event_target": "{rule_name}/{target_id}",
    "aws_cloudwatch_log_metric_filter": "{log_group_name}:{name}",
    "aws_cloudwatch_log_subscription_filter": "{log_group_name}/{filter_name}",
    # ═══════════════════════════════════════════════════════════════════════════
    # SNS / SQS
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_sns_topic": "{arn}",
    "aws_sns_topic_policy": "{arn}",
    "aws_sns_topic_subscription": "{arn}",
    "aws_sqs_queue": "{url}",
    "aws_sqs_queue_policy": "{url}",
    "aws_sqs_queue_redrive_policy": "{url}",
    "aws_sqs_queue_redrive_allow_policy": "{url}",
    # ═══════════════════════════════════════════════════════════════════════════
    # KMS
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_kms_key": "{key_id}",
    "aws_kms_alias": "{name}",
    "aws_kms_grant": "{key_id}:{grant_id}",
    # ═══════════════════════════════════════════════════════════════════════════
    # Route53
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_route53_zone": "{zone_id}",
    "aws_route53_record": "{zone_id}_{name}_{type}",
    "aws_route53_health_check": "{health_check_id}",
    "aws_route53_resolver_endpoint": "{id}",
    "aws_route53_resolver_rule": "{id}",
    # ═══════════════════════════════════════════════════════════════════════════
    # EKS / ECS
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_eks_cluster": "{name}",
    "aws_eks_node_group": "{cluster_name}:{node_group_name}",
    "aws_eks_fargate_profile": "{cluster_name}:{fargate_profile_name}",
    "aws_eks_addon": "{cluster_name}:{addon_name}",
    "aws_ecs_cluster": "{arn}",
    "aws_ecs_service": "{cluster_arn}/{service_name}",
    "aws_ecs_task_definition": "{arn}",
    "aws_ecs_capacity_provider": "{name}",
    # ═══════════════════════════════════════════════════════════════════════════
    # ECR
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_ecr_repository": "{name}",
    "aws_ecr_repository_policy": "{name}",
    "aws_ecr_lifecycle_policy": "{name}",
    # ═══════════════════════════════════════════════════════════════════════════
    # Secrets Manager / Parameter Store
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_secretsmanager_secret": "{arn}",
    "aws_secretsmanager_secret_version": "{arn}|{version_id}",
    "aws_ssm_parameter": "{name}",
    # ═══════════════════════════════════════════════════════════════════════════
    # ACM / Certificate Manager
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_acm_certificate": "{arn}",
    "aws_acm_certificate_validation": "{arn}",
    # ═══════════════════════════════════════════════════════════════════════════
    # CloudFront
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_cloudfront_distribution": "{id}",
    "aws_cloudfront_origin_access_identity": "{id}",
    "aws_cloudfront_origin_access_control": "{id}",
    "aws_cloudfront_cache_policy": "{id}",
    "aws_cloudfront_function": "{name}",
    # ═══════════════════════════════════════════════════════════════════════════
    # API Gateway
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_api_gateway_rest_api": "{id}",
    "aws_api_gateway_stage": "{rest_api_id}/{stage_name}",
    "aws_api_gateway_deployment": "{rest_api_id}/{deployment_id}",
    "aws_api_gateway_domain_name": "{domain_name}",
    "aws_apigatewayv2_api": "{id}",
    "aws_apigatewayv2_stage": "{api_id}/{stage_name}",
    # ═══════════════════════════════════════════════════════════════════════════
    # WAF
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_wafv2_web_acl": "{id}/{name}/{scope}",
    "aws_wafv2_ip_set": "{id}/{name}/{scope}",
    "aws_wafv2_rule_group": "{id}/{name}/{scope}",
    # ═══════════════════════════════════════════════════════════════════════════
    # Step Functions / EventBridge
    # ═══════════════════════════════════════════════════════════════════════════
    "aws_sfn_state_machine": "{arn}",
    "aws_sfn_activity": "{arn}",
    "aws_scheduler_schedule": "{group_name}/{name}",
    "aws_scheduler_schedule_group": "{name}",
}


@dataclass
class ImportMapping:
    """Maps a Terraform resource address to an AWS resource ID."""

    terraform_address: str  # e.g., "aws_instance.web_server_a1B2c3D4"
    aws_id: str  # e.g., "i-0abc123def456"
    resource_type: str  # e.g., "aws_instance"
    # Additional attributes for complex import formats
    attributes: dict | None = None


class ImportBlockGenerator:
    """
    Generate Terraform 1.5+ import blocks.

    These blocks tell Terraform: "The resource at this address
    corresponds to this existing AWS resource. Don't create it,
    just start managing it."

    Usage:
        generator = ImportBlockGenerator()
        mappings = [
            ImportMapping(
                terraform_address="aws_instance.web_a1b2",
                aws_id="i-0abc123",
                resource_type="aws_instance",
            ),
        ]
        generator.generate_import_file(mappings, Path("./terraform/imports.tf"))
    """

    def __init__(self, config: RepliMapConfig | None = None) -> None:
        """
        Initialize the import block generator.

        Args:
            config: User configuration for format overrides
        """
        self.import_formats = IMPORT_ID_FORMATS.copy()

        # Load user overrides from config
        if config:
            user_formats = config.get_import_formats()
            if user_formats:
                self.import_formats.update(user_formats)
                logger.info(f"Applied user import formats: {list(user_formats.keys())}")

    def format_import_id(self, mapping: ImportMapping) -> str:
        """
        Format the import ID based on resource type.

        Different AWS resources have different import ID formats.
        Most use the resource ID, but some need ARN, name, or composite keys.

        Args:
            mapping: Import mapping with resource details

        Returns:
            Formatted import ID string
        """
        format_template = self.import_formats.get(mapping.resource_type, "{id}")

        if format_template == "COMPLEX_SEE_DOCS":
            logger.warning(
                f"Resource {mapping.resource_type} has complex import format. "
                f"You may need to add override in .replimap.yaml. "
                f"See: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/{mapping.resource_type.replace('aws_', '')}"
            )
            # Return the ID as-is with a TODO marker
            return f"TODO_COMPLEX_FORMAT:{mapping.aws_id}"

        # For simple templates, just return the ID
        if format_template == "{id}":
            return mapping.aws_id

        # For named resources, try to extract the name
        if format_template == "{name}":
            if mapping.attributes and "name" in mapping.attributes:
                return mapping.attributes["name"]
            # Fall back to extracting from ID or ARN
            return self._extract_name_from_id(mapping.aws_id)

        # For ARN format
        if format_template == "{arn}":
            if mapping.aws_id.startswith("arn:"):
                return mapping.aws_id
            if mapping.attributes and "arn" in mapping.attributes:
                return mapping.attributes["arn"]
            return mapping.aws_id

        # For bucket format
        if format_template == "{bucket}":
            if mapping.attributes and "bucket" in mapping.attributes:
                return mapping.attributes["bucket"]
            return mapping.aws_id

        # For identifier format (RDS)
        if format_template == "{identifier}":
            if mapping.attributes and "identifier" in mapping.attributes:
                return mapping.attributes["identifier"]
            if mapping.attributes and "db_instance_identifier" in mapping.attributes:
                return mapping.attributes["db_instance_identifier"]
            return mapping.aws_id

        # For URL format (SQS)
        if format_template == "{url}":
            if mapping.attributes and "url" in mapping.attributes:
                return mapping.attributes["url"]
            return mapping.aws_id

        # For allocation_id format (EIP)
        if format_template == "{allocation_id}":
            if mapping.aws_id.startswith("eipalloc-"):
                return mapping.aws_id
            if mapping.attributes and "allocation_id" in mapping.attributes:
                return mapping.attributes["allocation_id"]
            return mapping.aws_id

        # Default: return the ID
        return mapping.aws_id

    def _extract_name_from_id(self, resource_id: str) -> str:
        """
        Extract a name from an AWS ID or ARN.

        Args:
            resource_id: AWS resource ID or ARN

        Returns:
            Extracted name or original ID
        """
        if resource_id.startswith("arn:"):
            # ARN format: arn:partition:service:region:account:resource-type/resource-id
            parts = resource_id.split(":")
            if len(parts) >= 6:
                resource_part = parts[5]
                if "/" in resource_part:
                    return resource_part.split("/")[-1]
                return resource_part
        return resource_id

    def generate_import_file(
        self,
        mappings: list[ImportMapping],
        output_path: Path,
    ) -> None:
        """
        Generate imports.tf file with all import blocks.

        Example output:
        ```hcl
        # Auto-generated by RepliMap
        # These import blocks map existing AWS resources to Terraform addresses

        import {
          to = aws_instance.web_server_a1B2c3D4
          id = "i-0abc123def456"
        }
        ```

        Args:
            mappings: List of import mappings
            output_path: Path to write the imports.tf file
        """
        if not mappings:
            logger.info("No import mappings to generate")
            return

        lines = [
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# Auto-generated by RepliMap",
            "# These import blocks map existing AWS resources to Terraform addresses",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "#",
            "# Run 'terraform plan' to verify, then 'terraform apply' to sync state",
            "#",
            "# Terraform 1.5+ required for import blocks",
            "# See: https://developer.hashicorp.com/terraform/language/import",
            "#",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
        ]

        # Track complex imports that need manual attention
        complex_imports: list[ImportMapping] = []

        for mapping in mappings:
            import_id = self.format_import_id(mapping)

            if import_id.startswith("TODO_COMPLEX_FORMAT:"):
                complex_imports.append(mapping)
                # Still generate the block but commented out
                lines.extend(
                    [
                        f"# WARNING: Complex import format for {mapping.resource_type}",
                        "# You may need to manually determine the correct import ID",
                        "# See Terraform docs for this resource type",
                        "# import {",
                        f"#   to = {mapping.terraform_address}",
                        f'#   id = "TODO: Determine correct import ID for {mapping.aws_id}"',
                        "# }",
                        "",
                    ]
                )
            else:
                lines.extend(
                    [
                        "import {",
                        f"  to = {mapping.terraform_address}",
                        f'  id = "{import_id}"',
                        "}",
                        "",
                    ]
                )

        # Add summary of complex imports
        if complex_imports:
            lines.extend(
                [
                    "# ═══════════════════════════════════════════════════════════════════════════════",
                    "# ATTENTION: The following resources need manual import configuration",
                    "# ═══════════════════════════════════════════════════════════════════════════════",
                    "#",
                ]
            )
            for mapping in complex_imports:
                lines.append(f"# - {mapping.terraform_address} ({mapping.aws_id})")
            lines.extend(
                [
                    "#",
                    "# Consult the Terraform AWS provider documentation for correct import IDs:",
                    "# https://registry.terraform.io/providers/hashicorp/aws/latest/docs",
                    "",
                ]
            )

        output_path.write_text("\n".join(lines))
        logger.info(
            f"Wrote imports.tf: {len(mappings)} imports "
            f"({len(complex_imports)} need manual attention)"
        )

    def generate_import_commands(
        self,
        mappings: list[ImportMapping],
    ) -> list[str]:
        """
        Generate legacy import commands for Terraform < 1.5.

        For users on older Terraform versions, generate shell commands:
        terraform import aws_instance.web_server_a1B2c3D4 i-0abc123def456

        Args:
            mappings: List of import mappings

        Returns:
            List of shell commands
        """
        commands = [
            "#!/bin/bash",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "# RepliMap Import Script",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "#",
            "# Run this to import existing resources into Terraform state.",
            "# Requires: Terraform initialized (terraform init)",
            "#",
            "# For Terraform 1.5+, use imports.tf instead (recommended).",
            "#",
            "# ═══════════════════════════════════════════════════════════════════════════════",
            "",
            "set -e  # Exit on error",
            "",
            "echo 'Starting resource imports...'",
            "",
        ]

        for i, mapping in enumerate(mappings):
            import_id = self.format_import_id(mapping)

            if import_id.startswith("TODO_COMPLEX_FORMAT:"):
                commands.extend(
                    [
                        f"# WARNING: Complex import for {mapping.resource_type}",
                        f"# terraform import {mapping.terraform_address} 'TODO: Determine ID'",
                        "",
                    ]
                )
            else:
                # Escape special characters in import ID
                escaped_id = import_id.replace("'", "'\\''")
                commands.extend(
                    [
                        f"echo '[{i + 1}/{len(mappings)}] Importing {mapping.terraform_address}'",
                        f"terraform import {mapping.terraform_address} '{escaped_id}'",
                        "",
                    ]
                )

        commands.extend(
            [
                "echo ''",
                "echo 'All imports completed successfully!'",
                "echo 'Run terraform plan to verify state.'",
            ]
        )

        return commands

    def generate_import_script(
        self,
        mappings: list[ImportMapping],
        output_path: Path,
    ) -> None:
        """
        Generate import.sh script file.

        Args:
            mappings: List of import mappings
            output_path: Path to write the import.sh file
        """
        if not mappings:
            logger.info("No import mappings for script")
            return

        commands = self.generate_import_commands(mappings)
        output_path.write_text("\n".join(commands))
        output_path.chmod(0o755)  # Make executable
        logger.info(f"Wrote import.sh: {len(mappings)} imports")
