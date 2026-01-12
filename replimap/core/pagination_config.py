"""
Pagination Configuration for AWS APIs.

AWS APIs use inconsistent pagination patterns:
- EC2: NextToken
- RDS: Marker
- S3: ContinuationToken
- CloudWatch Logs: nextToken (lowercase!)
- Route53: Compound tokens (StartRecordName + StartRecordType)

This module provides a unified configuration system for all pagination patterns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class PaginationConfig:
    """
    Configuration for paginating a specific AWS API operation.

    Attributes:
        input_token: Request parameter name for pagination token (e.g., 'NextToken')
        output_token: Response field name for next page token (e.g., 'NextToken')
        result_key: Response field containing the data list (e.g., 'Vpcs')
        limit_key: Parameter name for page size (e.g., 'MaxResults')
        default_page_size: Default number of items per page
        is_nested: True if results are nested (e.g., EC2 Reservations -> Instances)
        nested_key: Child key for nested extraction (e.g., 'Instances')
        is_compound_token: True for multi-field tokens (e.g., Route53)
        compound_input_keys: Input parameter names for compound tokens
        compound_output_keys: Output field names for compound tokens
    """

    input_token: str
    output_token: str
    result_key: str
    limit_key: str = "MaxResults"
    default_page_size: int = 100
    is_nested: bool = False
    nested_key: Optional[str] = None
    is_compound_token: bool = False
    compound_input_keys: tuple[str, ...] = field(default_factory=tuple)
    compound_output_keys: tuple[str, ...] = field(default_factory=tuple)


# =============================================================================
# PAGINATION CONFIGURATIONS BY SERVICE
# =============================================================================

PAGINATION_CONFIGS: dict[str, dict[str, PaginationConfig]] = {
    # =========================================================================
    # EC2 Service - NextToken pattern
    # =========================================================================
    "ec2": {
        # NESTED: Reservations contain Instances
        "describe_instances": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Reservations",
            limit_key="MaxResults",
            default_page_size=100,
            is_nested=True,
            nested_key="Instances",
        ),
        "describe_vpcs": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Vpcs",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_subnets": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Subnets",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_security_groups": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="SecurityGroups",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_volumes": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Volumes",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_snapshots": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Snapshots",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_network_interfaces": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="NetworkInterfaces",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_route_tables": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="RouteTables",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_nat_gateways": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="NatGateways",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_internet_gateways": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="InternetGateways",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_vpc_endpoints": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="VpcEndpoints",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_flow_logs": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="FlowLogs",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_launch_templates": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="LaunchTemplates",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_network_acls": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="NetworkAcls",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_addresses": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Addresses",
            limit_key="MaxResults",
            default_page_size=100,
        ),
        "describe_key_pairs": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="KeyPairs",
            limit_key="MaxResults",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # RDS Service - Marker pattern with MaxRecords
    # =========================================================================
    "rds": {
        "describe_db_instances": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="DBInstances",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
        "describe_db_clusters": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="DBClusters",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
        "describe_db_subnet_groups": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="DBSubnetGroups",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
        "describe_db_parameter_groups": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="DBParameterGroups",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
        "describe_db_snapshots": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="DBSnapshots",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # S3 Service - ContinuationToken pattern
    # =========================================================================
    "s3": {
        "list_objects_v2": PaginationConfig(
            input_token="ContinuationToken",
            output_token="NextContinuationToken",
            result_key="Contents",
            limit_key="MaxKeys",
            default_page_size=1000,
        ),
        "list_object_versions": PaginationConfig(
            input_token="KeyMarker",
            output_token="NextKeyMarker",
            result_key="Versions",
            limit_key="MaxKeys",
            default_page_size=1000,
        ),
    },
    # =========================================================================
    # IAM Service - Marker pattern with MaxItems
    # =========================================================================
    "iam": {
        "list_roles": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="Roles",
            limit_key="MaxItems",
            default_page_size=100,
        ),
        "list_users": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="Users",
            limit_key="MaxItems",
            default_page_size=100,
        ),
        "list_policies": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="Policies",
            limit_key="MaxItems",
            default_page_size=100,
        ),
        "list_instance_profiles": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="InstanceProfiles",
            limit_key="MaxItems",
            default_page_size=100,
        ),
        "list_attached_role_policies": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="AttachedPolicies",
            limit_key="MaxItems",
            default_page_size=100,
        ),
        "list_groups": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="Groups",
            limit_key="MaxItems",
            default_page_size=100,
        ),
        "list_attached_user_policies": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="AttachedPolicies",
            limit_key="MaxItems",
            default_page_size=100,
        ),
        "list_attached_group_policies": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="AttachedPolicies",
            limit_key="MaxItems",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # ELBv2 Service - Marker -> NextMarker
    # =========================================================================
    "elbv2": {
        "describe_load_balancers": PaginationConfig(
            input_token="Marker",
            output_token="NextMarker",
            result_key="LoadBalancers",
            limit_key="PageSize",
            default_page_size=100,
        ),
        "describe_target_groups": PaginationConfig(
            input_token="Marker",
            output_token="NextMarker",
            result_key="TargetGroups",
            limit_key="PageSize",
            default_page_size=100,
        ),
        "describe_listeners": PaginationConfig(
            input_token="Marker",
            output_token="NextMarker",
            result_key="Listeners",
            limit_key="PageSize",
            default_page_size=100,
        ),
        "describe_rules": PaginationConfig(
            input_token="Marker",
            output_token="NextMarker",
            result_key="Rules",
            limit_key="PageSize",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # CloudWatch Logs - LOWERCASE tokens!
    # =========================================================================
    "logs": {
        "describe_log_groups": PaginationConfig(
            input_token="nextToken",  # LOWERCASE - this is critical
            output_token="nextToken",
            result_key="logGroups",  # Also lowercase
            limit_key="limit",
            default_page_size=50,
        ),
        "describe_log_streams": PaginationConfig(
            input_token="nextToken",
            output_token="nextToken",
            result_key="logStreams",
            limit_key="limit",
            default_page_size=50,
        ),
        "filter_log_events": PaginationConfig(
            input_token="nextToken",
            output_token="nextToken",
            result_key="events",
            limit_key="limit",
            default_page_size=10000,
        ),
    },
    # =========================================================================
    # CloudWatch
    # =========================================================================
    "cloudwatch": {
        "describe_alarms": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="MetricAlarms",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
        "list_metrics": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Metrics",
            limit_key="MaxRecords",
            default_page_size=500,
        ),
    },
    # =========================================================================
    # AutoScaling
    # =========================================================================
    "autoscaling": {
        "describe_auto_scaling_groups": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="AutoScalingGroups",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
        "describe_launch_configurations": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="LaunchConfigurations",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
        "describe_scaling_policies": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="ScalingPolicies",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # Lambda - Marker -> NextMarker
    # =========================================================================
    "lambda": {
        "list_functions": PaginationConfig(
            input_token="Marker",
            output_token="NextMarker",
            result_key="Functions",
            limit_key="MaxItems",
            default_page_size=50,
        ),
        "list_layers": PaginationConfig(
            input_token="Marker",
            output_token="NextMarker",
            result_key="Layers",
            limit_key="MaxItems",
            default_page_size=50,
        ),
        "list_event_source_mappings": PaginationConfig(
            input_token="Marker",
            output_token="NextMarker",
            result_key="EventSourceMappings",
            limit_key="MaxItems",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # SQS
    # =========================================================================
    "sqs": {
        "list_queues": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="QueueUrls",
            limit_key="MaxResults",
            default_page_size=1000,
        ),
    },
    # =========================================================================
    # SNS
    # =========================================================================
    "sns": {
        "list_topics": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Topics",
            limit_key="MaxItems",
            default_page_size=100,
        ),
        "list_subscriptions": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Subscriptions",
            limit_key="MaxItems",
            default_page_size=100,
        ),
        "list_subscriptions_by_topic": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Subscriptions",
            limit_key="MaxItems",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # ElastiCache - Marker pattern
    # =========================================================================
    "elasticache": {
        "describe_cache_clusters": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="CacheClusters",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
        "describe_cache_subnet_groups": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="CacheSubnetGroups",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
        "describe_replication_groups": PaginationConfig(
            input_token="Marker",
            output_token="Marker",
            result_key="ReplicationGroups",
            limit_key="MaxRecords",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # Route53 - COMPOUND tokens
    # =========================================================================
    "route53": {
        "list_resource_record_sets": PaginationConfig(
            input_token="",  # Not used for compound
            output_token="",  # Not used for compound
            result_key="ResourceRecordSets",
            limit_key="MaxItems",
            default_page_size=100,
            is_compound_token=True,
            compound_input_keys=("StartRecordName", "StartRecordType"),
            compound_output_keys=("NextRecordName", "NextRecordType"),
        ),
        "list_hosted_zones": PaginationConfig(
            input_token="Marker",
            output_token="NextMarker",
            result_key="HostedZones",
            limit_key="MaxItems",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # ECS
    # =========================================================================
    "ecs": {
        "list_clusters": PaginationConfig(
            input_token="nextToken",
            output_token="nextToken",
            result_key="clusterArns",
            limit_key="maxResults",
            default_page_size=100,
        ),
        "list_services": PaginationConfig(
            input_token="nextToken",
            output_token="nextToken",
            result_key="serviceArns",
            limit_key="maxResults",
            default_page_size=100,
        ),
        "list_tasks": PaginationConfig(
            input_token="nextToken",
            output_token="nextToken",
            result_key="taskArns",
            limit_key="maxResults",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # EKS
    # =========================================================================
    "eks": {
        "list_clusters": PaginationConfig(
            input_token="nextToken",
            output_token="nextToken",
            result_key="clusters",
            limit_key="maxResults",
            default_page_size=100,
        ),
        "list_nodegroups": PaginationConfig(
            input_token="nextToken",
            output_token="nextToken",
            result_key="nodegroups",
            limit_key="maxResults",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # DynamoDB
    # =========================================================================
    "dynamodb": {
        "list_tables": PaginationConfig(
            input_token="ExclusiveStartTableName",
            output_token="LastEvaluatedTableName",
            result_key="TableNames",
            limit_key="Limit",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # Secrets Manager
    # =========================================================================
    "secretsmanager": {
        "list_secrets": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="SecretList",
            limit_key="MaxResults",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # SSM (Systems Manager)
    # =========================================================================
    "ssm": {
        "describe_parameters": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Parameters",
            limit_key="MaxResults",
            default_page_size=50,
        ),
        "describe_instance_information": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="InstanceInformationList",
            limit_key="MaxResults",
            default_page_size=50,
        ),
    },
    # =========================================================================
    # KMS
    # =========================================================================
    "kms": {
        "list_keys": PaginationConfig(
            input_token="Marker",
            output_token="NextMarker",
            result_key="Keys",
            limit_key="Limit",
            default_page_size=100,
        ),
        "list_aliases": PaginationConfig(
            input_token="Marker",
            output_token="NextMarker",
            result_key="Aliases",
            limit_key="Limit",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # ECR
    # =========================================================================
    "ecr": {
        "describe_repositories": PaginationConfig(
            input_token="nextToken",
            output_token="nextToken",
            result_key="repositories",
            limit_key="maxResults",
            default_page_size=100,
        ),
        "list_images": PaginationConfig(
            input_token="nextToken",
            output_token="nextToken",
            result_key="imageIds",
            limit_key="maxResults",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # API Gateway
    # =========================================================================
    "apigateway": {
        "get_rest_apis": PaginationConfig(
            input_token="position",
            output_token="position",
            result_key="items",
            limit_key="limit",
            default_page_size=100,
        ),
    },
    # =========================================================================
    # API Gateway V2 (HTTP/WebSocket)
    # =========================================================================
    "apigatewayv2": {
        "get_apis": PaginationConfig(
            input_token="NextToken",
            output_token="NextToken",
            result_key="Items",
            limit_key="MaxResults",
            default_page_size=100,
        ),
    },
}


def get_pagination_config(service: str, method: str) -> Optional[PaginationConfig]:
    """
    Get pagination config for a service method.

    Args:
        service: AWS service name (e.g., 'ec2', 'rds')
        method: API method name (e.g., 'describe_instances')

    Returns:
        PaginationConfig if found, None otherwise

    Example:
        >>> config = get_pagination_config('ec2', 'describe_instances')
        >>> config.input_token
        'NextToken'
        >>> config.is_nested
        True
    """
    service_configs = PAGINATION_CONFIGS.get(service.lower())
    if service_configs is None:
        return None
    return service_configs.get(method.lower())


def get_all_services() -> list[str]:
    """Get list of all configured services."""
    return list(PAGINATION_CONFIGS.keys())


def get_service_methods(service: str) -> list[str]:
    """Get list of all configured methods for a service."""
    service_configs = PAGINATION_CONFIGS.get(service.lower())
    if service_configs is None:
        return []
    return list(service_configs.keys())
