"""
AWS Console URL Generation.

Generates deep links to AWS Console for various resource types.
"""

from __future__ import annotations


def get_console_url(resource_type: str, resource_id: str, region: str) -> str:
    """
    Generate AWS Console URL for a resource.

    Args:
        resource_type: Terraform resource type (e.g., "aws_instance", "db_instance")
        resource_id: AWS resource ID (e.g., "i-1234567890abcdef0", "vpc-12345678")
        region: AWS region (e.g., "us-east-1", "ap-southeast-2")

    Returns:
        AWS Console URL for the resource, or empty string if unsupported.

    Examples:
        >>> get_console_url("instance", "i-1234567890abcdef0", "us-east-1")
        'https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#InstanceDetails:instanceId=i-1234567890abcdef0'
    """
    base = f"https://{region}.console.aws.amazon.com"

    # Normalize resource type (handle both terraform and short names)
    rt = resource_type.lower().replace("aws_", "")

    # URL templates for common resource types
    url_templates: dict[str, str] = {
        # EC2
        "instance": f"{base}/ec2/home?region={region}#InstanceDetails:instanceId={resource_id}",
        "security_group": f"{base}/ec2/home?region={region}#SecurityGroup:groupId={resource_id}",
        "eip": f"{base}/ec2/home?region={region}#ElasticIpDetails:AllocationId={resource_id}",
        "launch_template": f"{base}/ec2/home?region={region}#LaunchTemplates:launchTemplateId={resource_id}",
        "ebs_volume": f"{base}/ec2/home?region={region}#VolumeDetails:volumeId={resource_id}",
        # VPC
        "vpc": f"{base}/vpc/home?region={region}#VpcDetails:VpcId={resource_id}",
        "subnet": f"{base}/vpc/home?region={region}#SubnetDetails:subnetId={resource_id}",
        "route_table": f"{base}/vpc/home?region={region}#RouteTableDetails:RouteTableId={resource_id}",
        "internet_gateway": f"{base}/vpc/home?region={region}#InternetGateway:internetGatewayId={resource_id}",
        "nat_gateway": f"{base}/vpc/home?region={region}#NatGatewayDetails:natGatewayId={resource_id}",
        "vpc_endpoint": f"{base}/vpc/home?region={region}#Endpoints:vpcEndpointId={resource_id}",
        "network_acl": f"{base}/vpc/home?region={region}#NetworkAclDetails:networkAclId={resource_id}",
        # RDS
        "db_instance": f"{base}/rds/home?region={region}#database:id={resource_id}",
        "rds_cluster": f"{base}/rds/home?region={region}#database:id={resource_id}",
        "db_subnet_group": f"{base}/rds/home?region={region}#db-subnet-group:id={resource_id}",
        # ElastiCache
        "elasticache_cluster": f"{base}/elasticache/home?region={region}#/redis/{resource_id}",
        "elasticache_replication_group": f"{base}/elasticache/home?region={region}#/redis/{resource_id}",
        "elasticache_subnet_group": f"{base}/elasticache/home?region={region}#/subnet-groups/{resource_id}",
        # S3 (global, no region in URL)
        "s3_bucket": f"https://s3.console.aws.amazon.com/s3/buckets/{resource_id}?region={region}",
        # Lambda
        "lambda_function": f"{base}/lambda/home?region={region}#/functions/{resource_id}",
        # Load Balancers (using ARN-based lookups)
        "lb": f"{base}/ec2/home?region={region}#LoadBalancers:search={resource_id}",
        "lb_target_group": f"{base}/ec2/home?region={region}#TargetGroups:search={resource_id}",
        "alb": f"{base}/ec2/home?region={region}#LoadBalancers:search={resource_id}",
        "nlb": f"{base}/ec2/home?region={region}#LoadBalancers:search={resource_id}",
        # Auto Scaling
        "autoscaling_group": f"{base}/ec2/home?region={region}#AutoScalingGroupDetails:id={resource_id}",
        # EKS
        "eks_cluster": f"{base}/eks/home?region={region}#/clusters/{resource_id}",
        # IAM (global)
        "iam_role": f"https://console.aws.amazon.com/iam/home#/roles/{resource_id}",
        "iam_policy": f"https://console.aws.amazon.com/iam/home#/policies/{resource_id}",
        "iam_user": f"https://console.aws.amazon.com/iam/home#/users/{resource_id}",
        # CloudWatch
        "cloudwatch_log_group": f"{base}/cloudwatch/home?region={region}#logsV2:log-groups/log-group/{resource_id.replace('/', '$252F')}",
        "cloudwatch_metric_alarm": f"{base}/cloudwatch/home?region={region}#alarmsV2:alarm/{resource_id}",
        # SQS
        "sqs_queue": f"{base}/sqs/v2/home?region={region}#/queues/{resource_id}",
        # SNS
        "sns_topic": f"{base}/sns/v3/home?region={region}#/topic/{resource_id}",
    }

    return url_templates.get(rt, "")


def get_console_url_from_id(resource_id: str, region: str) -> str:
    """
    Infer resource type from ID and generate console URL.

    Args:
        resource_id: AWS resource ID with prefix (e.g., "i-xxx", "vpc-xxx")
        region: AWS region

    Returns:
        AWS Console URL or empty string if type cannot be inferred.
    """
    # Map ID prefixes to resource types
    prefix_map: dict[str, str] = {
        "i-": "instance",
        "sg-": "security_group",
        "vpc-": "vpc",
        "subnet-": "subnet",
        "rtb-": "route_table",
        "igw-": "internet_gateway",
        "nat-": "nat_gateway",
        "vpce-": "vpc_endpoint",
        "acl-": "network_acl",
        "eipalloc-": "eip",
        "lt-": "launch_template",
        "vol-": "ebs_volume",
        "asg-": "autoscaling_group",
    }

    for prefix, resource_type in prefix_map.items():
        if resource_id.startswith(prefix):
            return get_console_url(resource_type, resource_id, region)

    return ""
