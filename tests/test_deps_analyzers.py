"""
Tests for Dependency Analyzers.

Tests the new analyzer framework including:
- Models (RelationType, Severity, Dependency, DependencyAnalysis)
- Base analyzer
- EC2, Security Group, RDS, ASG, S3, Lambda analyzers
"""

from unittest.mock import MagicMock, patch

import pytest

from replimap.deps.models import (
    BlastRadiusScore,
    Dependency,
    DependencyAnalysis,
    RelationType,
    ResourceCriticality,
    Severity,
)
from replimap.deps.blast_radius import calculate_blast_radius


# =============================================================================
# MODEL TESTS
# =============================================================================


class TestRelationType:
    """Test RelationType enum."""

    def test_all_relation_types_exist(self):
        """All required relation types exist."""
        assert RelationType.MANAGER
        assert RelationType.CONSUMER
        assert RelationType.DEPENDENCY
        assert RelationType.NETWORK
        assert RelationType.IDENTITY
        assert RelationType.TRUST
        assert RelationType.MANAGED
        assert RelationType.REPLICATION
        assert RelationType.TRIGGER

    def test_relation_type_values(self):
        """Relation types have correct string values."""
        assert RelationType.MANAGER.value == "manager"
        assert RelationType.CONSUMER.value == "consumer"
        assert RelationType.DEPENDENCY.value == "dependency"


class TestSeverity:
    """Test Severity enum."""

    def test_severity_values(self):
        """Severity values are correct."""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.INFO.value == "info"


class TestDependency:
    """Test Dependency dataclass."""

    def test_create_dependency(self):
        """Create a basic dependency."""
        dep = Dependency(
            resource_type="aws_instance",
            resource_id="i-123",
            relation_type=RelationType.CONSUMER,
            severity=Severity.HIGH,
        )
        assert dep.resource_type == "aws_instance"
        assert dep.resource_id == "i-123"
        assert dep.relation_type == RelationType.CONSUMER
        assert dep.severity == Severity.HIGH
        assert dep.children == []
        assert dep.metadata == {}

    def test_dependency_with_all_fields(self):
        """Create dependency with all optional fields."""
        dep = Dependency(
            resource_type="aws_instance",
            resource_id="i-123",
            resource_name="web-server",
            relation_type=RelationType.CONSUMER,
            severity=Severity.HIGH,
            warning="This is a production instance",
            metadata={"state": "running"},
        )
        assert dep.resource_name == "web-server"
        assert dep.warning == "This is a production instance"
        assert dep.metadata["state"] == "running"

    def test_dependency_children(self):
        """Test nested dependencies."""
        child = Dependency(
            resource_type="aws_iam_role",
            resource_id="role-arn",
            relation_type=RelationType.IDENTITY,
            severity=Severity.HIGH,
        )
        parent = Dependency(
            resource_type="aws_iam_instance_profile",
            resource_id="profile-arn",
            relation_type=RelationType.IDENTITY,
            severity=Severity.HIGH,
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].resource_type == "aws_iam_role"


class TestDependencyAnalysis:
    """Test DependencyAnalysis dataclass."""

    def test_create_analysis(self):
        """Create a basic analysis."""
        center = Dependency(
            resource_type="aws_instance",
            resource_id="i-123",
            relation_type=RelationType.DEPENDENCY,
            severity=Severity.HIGH,
        )
        analysis = DependencyAnalysis(center_resource=center)
        assert analysis.center_resource == center
        assert analysis.dependencies == {}
        assert analysis.warnings == []

    def test_analysis_to_dict(self):
        """Analysis can be converted to dict."""
        center = Dependency(
            resource_type="aws_instance",
            resource_id="i-123",
            relation_type=RelationType.DEPENDENCY,
            severity=Severity.HIGH,
        )
        analysis = DependencyAnalysis(
            center_resource=center,
            context={"vpc_id": "vpc-123"},
        )
        data = analysis.to_dict()
        assert "center_resource" in data
        assert "context" in data
        assert data["context"]["vpc_id"] == "vpc-123"


# =============================================================================
# BLAST RADIUS TESTS
# =============================================================================


class TestBlastRadius:
    """Test blast radius calculation."""

    def test_empty_dependencies(self):
        """Empty dependencies gives zero blast radius."""
        result = calculate_blast_radius({})
        assert result.score == 0
        assert result.level == "LOW"
        assert result.affected_count == 0

    def test_consumer_impact(self):
        """Consumers increase blast radius."""
        deps = {
            RelationType.CONSUMER: [
                Dependency(
                    resource_type="aws_instance",
                    resource_id="i-123",
                    relation_type=RelationType.CONSUMER,
                    severity=Severity.HIGH,
                ),
                Dependency(
                    resource_type="aws_instance",
                    resource_id="i-456",
                    relation_type=RelationType.CONSUMER,
                    severity=Severity.HIGH,
                ),
            ]
        }
        result = calculate_blast_radius(deps)
        assert result.affected_count == 2
        assert result.score > 0

    def test_database_has_high_weight(self):
        """Databases have high impact weight."""
        deps = {
            RelationType.CONSUMER: [
                Dependency(
                    resource_type="aws_db_instance",
                    resource_id="db-123",
                    relation_type=RelationType.CONSUMER,
                    severity=Severity.CRITICAL,
                ),
            ]
        }
        result = calculate_blast_radius(deps)
        # Database weight is 10
        assert result.weighted_impact >= 10

    def test_managed_resources_count(self):
        """MANAGED resources count towards blast radius."""
        deps = {
            RelationType.MANAGED: [
                Dependency(
                    resource_type="aws_instance",
                    resource_id="i-123",
                    relation_type=RelationType.MANAGED,
                    severity=Severity.MEDIUM,
                ),
            ]
        }
        result = calculate_blast_radius(deps)
        assert result.affected_count == 1


# =============================================================================
# EC2 ANALYZER TESTS
# =============================================================================


class TestEC2Analyzer:
    """Test EC2 Instance analyzer."""

    def test_analyzer_resource_type(self):
        """EC2 analyzer has correct resource type."""
        from replimap.deps.analyzers.ec2 import EC2Analyzer

        analyzer = EC2Analyzer()
        assert analyzer.resource_type == "aws_instance"

    def test_find_asg_manager(self):
        """Detects ASG manager from tags."""
        from replimap.deps.analyzers.ec2 import EC2Analyzer

        analyzer = EC2Analyzer()
        data = {"Tags": [{"Key": "aws:autoscaling:groupName", "Value": "my-asg"}]}
        tags = {t["Key"]: t["Value"] for t in data["Tags"]}

        managers = analyzer._find_managers(data, tags)

        assert len(managers) == 1
        assert managers[0].resource_type == "aws_autoscaling_group"
        assert managers[0].resource_id == "my-asg"
        assert managers[0].relation_type == RelationType.MANAGER

    def test_find_cloudformation_manager(self):
        """Detects CloudFormation manager from tags."""
        from replimap.deps.analyzers.ec2 import EC2Analyzer

        analyzer = EC2Analyzer()
        data = {"Tags": [{"Key": "aws:cloudformation:stack-name", "Value": "my-stack"}]}
        tags = {t["Key"]: t["Value"] for t in data["Tags"]}

        managers = analyzer._find_managers(data, tags)

        assert len(managers) == 1
        assert managers[0].resource_type == "aws_cloudformation_stack"
        assert managers[0].resource_id == "my-stack"

    def test_find_ami_dependency(self):
        """Finds AMI dependency."""
        from replimap.deps.analyzers.ec2 import EC2Analyzer

        analyzer = EC2Analyzer()
        data = {"ImageId": "ami-12345678"}

        deps = analyzer._find_dependencies(data)

        ami_deps = [d for d in deps if d.resource_type == "aws_ami"]
        assert len(ami_deps) == 1
        assert ami_deps[0].resource_id == "ami-12345678"

    def test_find_ebs_dependencies(self):
        """Finds EBS volume dependencies."""
        from replimap.deps.analyzers.ec2 import EC2Analyzer

        analyzer = EC2Analyzer()
        data = {
            "BlockDeviceMappings": [
                {"DeviceName": "/dev/sda1", "Ebs": {"VolumeId": "vol-123"}},
                {"DeviceName": "/dev/sdb", "Ebs": {"VolumeId": "vol-456"}},
            ]
        }

        deps = analyzer._find_dependencies(data)

        ebs_deps = [d for d in deps if d.resource_type == "aws_ebs_volume"]
        assert len(ebs_deps) == 2
        assert ebs_deps[0].resource_id == "vol-123"
        assert ebs_deps[1].resource_id == "vol-456"

    def test_find_network_dependencies(self):
        """Finds VPC, Subnet, Security Group dependencies."""
        from replimap.deps.analyzers.ec2 import EC2Analyzer

        analyzer = EC2Analyzer()
        data = {
            "VpcId": "vpc-123",
            "SubnetId": "subnet-456",
            "SecurityGroups": [{"GroupId": "sg-789", "GroupName": "default"}],
            "NetworkInterfaces": [],
        }

        network = analyzer._find_network(data)

        vpc = [n for n in network if n.resource_type == "aws_vpc"]
        subnet = [n for n in network if n.resource_type == "aws_subnet"]
        sg = [n for n in network if n.resource_type == "aws_security_group"]

        assert len(vpc) == 1
        assert vpc[0].resource_id == "vpc-123"
        assert len(subnet) == 1
        assert subnet[0].resource_id == "subnet-456"
        assert len(sg) == 1
        assert sg[0].resource_id == "sg-789"

    def test_find_iam_identity(self):
        """Finds IAM instance profile."""
        from replimap.deps.analyzers.ec2 import EC2Analyzer

        analyzer = EC2Analyzer()
        data = {
            "IamInstanceProfile": {
                "Arn": "arn:aws:iam::123456789012:instance-profile/my-profile"
            },
            "BlockDeviceMappings": [],
        }

        identity = analyzer._find_identity(data)

        profiles = [
            i for i in identity if i.resource_type == "aws_iam_instance_profile"
        ]
        assert len(profiles) == 1
        assert "my-profile" in profiles[0].resource_id


# =============================================================================
# SECURITY GROUP ANALYZER TESTS
# =============================================================================


class TestSecurityGroupAnalyzer:
    """Test Security Group analyzer."""

    def test_analyzer_resource_type(self):
        """SG analyzer has correct resource type."""
        from replimap.deps.analyzers.security_group import SecurityGroupAnalyzer

        analyzer = SecurityGroupAnalyzer()
        assert analyzer.resource_type == "aws_security_group"

    def test_find_vpc_network(self):
        """Finds VPC network dependency."""
        from replimap.deps.analyzers.security_group import SecurityGroupAnalyzer

        analyzer = SecurityGroupAnalyzer()
        data = {"VpcId": "vpc-123"}

        network = analyzer._find_network(data)

        assert len(network) == 1
        assert network[0].resource_type == "aws_vpc"
        assert network[0].resource_id == "vpc-123"

    def test_format_port_info(self):
        """Port info formatting works correctly."""
        from replimap.deps.analyzers.security_group import SecurityGroupAnalyzer

        analyzer = SecurityGroupAnalyzer()

        # All traffic
        assert analyzer._format_port_info({"IpProtocol": "-1"}) == "all traffic"

        # Single port
        assert (
            analyzer._format_port_info(
                {"FromPort": 443, "ToPort": 443, "IpProtocol": "tcp"}
            )
            == "port 443"
        )

        # All ports
        assert (
            analyzer._format_port_info(
                {"FromPort": 0, "ToPort": 65535, "IpProtocol": "tcp"}
            )
            == "all ports"
        )

        # Port range
        assert (
            analyzer._format_port_info(
                {"FromPort": 1024, "ToPort": 2048, "IpProtocol": "tcp"}
            )
            == "ports 1024-2048"
        )


# =============================================================================
# RDS ANALYZER TESTS
# =============================================================================


class TestRDSAnalyzer:
    """Test RDS Instance analyzer."""

    def test_analyzer_resource_type(self):
        """RDS analyzer has correct resource type."""
        from replimap.deps.analyzers.rds import RDSInstanceAnalyzer

        analyzer = RDSInstanceAnalyzer()
        assert analyzer.resource_type == "aws_db_instance"

    def test_find_read_replicas(self):
        """Finds read replica consumers."""
        from replimap.deps.analyzers.rds import RDSInstanceAnalyzer

        analyzer = RDSInstanceAnalyzer()
        data = {"ReadReplicaDBInstanceIdentifiers": ["replica-1", "replica-2"]}

        consumers = analyzer._find_consumers("source-db", data)

        assert len(consumers) == 2
        assert consumers[0].resource_id == "replica-1"
        assert consumers[0].relation_type == RelationType.CONSUMER

    def test_find_source_instance(self):
        """Finds source instance for replica."""
        from replimap.deps.analyzers.rds import RDSInstanceAnalyzer

        analyzer = RDSInstanceAnalyzer()
        data = {"ReadReplicaSourceDBInstanceIdentifier": "source-db"}

        deps = analyzer._find_dependencies(data)

        sources = [d for d in deps if d.metadata.get("type") == "source_instance"]
        assert len(sources) == 1
        assert sources[0].resource_id == "source-db"

    def test_find_kms_key(self):
        """Finds KMS encryption key."""
        from replimap.deps.analyzers.rds import RDSInstanceAnalyzer

        analyzer = RDSInstanceAnalyzer()
        data = {"KmsKeyId": "arn:aws:kms:us-east-1:123:key/abc-123"}

        identity = analyzer._find_identity(data)

        kms = [i for i in identity if i.resource_type == "aws_kms_key"]
        assert len(kms) == 1


# =============================================================================
# ASG ANALYZER TESTS
# =============================================================================


class TestASGAnalyzer:
    """Test Auto Scaling Group analyzer."""

    def test_analyzer_resource_type(self):
        """ASG analyzer has correct resource type."""
        from replimap.deps.analyzers.asg import ASGAnalyzer

        analyzer = ASGAnalyzer()
        assert analyzer.resource_type == "aws_autoscaling_group"

    def test_find_managed_instances(self):
        """Finds managed EC2 instances."""
        from replimap.deps.analyzers.asg import ASGAnalyzer

        analyzer = ASGAnalyzer()
        data = {
            "Instances": [
                {
                    "InstanceId": "i-123",
                    "LifecycleState": "InService",
                    "HealthStatus": "Healthy",
                    "AvailabilityZone": "us-east-1a",
                },
                {
                    "InstanceId": "i-456",
                    "LifecycleState": "Pending",
                    "HealthStatus": "Unhealthy",
                },
            ]
        }

        managed = analyzer._find_managed_instances(data)

        assert len(managed) == 2
        assert managed[0].resource_id == "i-123"
        assert managed[0].relation_type == RelationType.MANAGED
        assert managed[0].metadata["lifecycle_state"] == "InService"

    def test_find_target_groups(self):
        """Finds target group consumers."""
        from replimap.deps.analyzers.asg import ASGAnalyzer

        analyzer = ASGAnalyzer()
        data = {
            "TargetGroupARNs": [
                "arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/my-tg/abc"
            ]
        }

        consumers = analyzer._find_consumers(data)

        assert len(consumers) == 1
        assert consumers[0].resource_type == "aws_lb_target_group"

    def test_find_launch_template(self):
        """Finds launch template dependency."""
        from replimap.deps.analyzers.asg import ASGAnalyzer

        analyzer = ASGAnalyzer()
        data = {
            "LaunchTemplate": {
                "LaunchTemplateId": "lt-123",
                "LaunchTemplateName": "my-template",
                "Version": "$Latest",
            }
        }

        deps = analyzer._find_dependencies(data)

        lt = [d for d in deps if d.resource_type == "aws_launch_template"]
        assert len(lt) == 1
        assert lt[0].resource_id == "lt-123"


# =============================================================================
# S3 ANALYZER TESTS
# =============================================================================


class TestS3Analyzer:
    """Test S3 Bucket analyzer."""

    def test_analyzer_resource_type(self):
        """S3 analyzer has correct resource type."""
        from replimap.deps.analyzers.s3 import S3BucketAnalyzer

        analyzer = S3BucketAnalyzer()
        assert analyzer.resource_type == "aws_s3_bucket"

    def test_find_lambda_triggers(self):
        """Finds Lambda function triggers."""
        from replimap.deps.analyzers.s3 import S3BucketAnalyzer

        analyzer = S3BucketAnalyzer()
        data = {
            "notifications": {
                "lambda_functions": [
                    {
                        "LambdaFunctionArn": "arn:aws:lambda:us-east-1:123:function:my-func",
                        "Events": ["s3:ObjectCreated:*"],
                    }
                ],
                "sqs_queues": [],
                "sns_topics": [],
            },
            "logging": {"enabled": False},
        }

        consumers = analyzer._find_consumers("my-bucket", data)

        lambdas = [c for c in consumers if c.resource_type == "aws_lambda_function"]
        assert len(lambdas) == 1
        assert lambdas[0].resource_name == "my-func"

    def test_find_replication_target(self):
        """Finds replication targets."""
        from replimap.deps.analyzers.s3 import S3BucketAnalyzer

        analyzer = S3BucketAnalyzer()
        data = {
            "replication": {
                "Rules": [
                    {
                        "Status": "Enabled",
                        "Destination": {
                            "Bucket": "arn:aws:s3:::backup-bucket",
                        },
                    }
                ]
            }
        }

        replication = analyzer._find_replication(data)

        assert len(replication) == 1
        assert replication[0].resource_type == "aws_s3_bucket"
        assert replication[0].relation_type == RelationType.REPLICATION


# =============================================================================
# LAMBDA ANALYZER TESTS
# =============================================================================


class TestLambdaAnalyzer:
    """Test Lambda Function analyzer."""

    def test_analyzer_resource_type(self):
        """Lambda analyzer has correct resource type."""
        from replimap.deps.analyzers.lambda_func import LambdaFunctionAnalyzer

        analyzer = LambdaFunctionAnalyzer()
        assert analyzer.resource_type == "aws_lambda_function"

    def test_find_layers(self):
        """Finds layer dependencies."""
        from replimap.deps.analyzers.lambda_func import LambdaFunctionAnalyzer

        analyzer = LambdaFunctionAnalyzer()
        data = {
            "Layers": [
                {
                    "Arn": "arn:aws:lambda:us-east-1:123:layer:my-layer:1",
                    "CodeSize": 1024,
                }
            ]
        }

        deps = analyzer._find_dependencies(data)

        layers = [d for d in deps if d.resource_type == "aws_lambda_layer_version"]
        assert len(layers) == 1
        assert "my-layer" in layers[0].resource_name

    def test_find_vpc_config(self):
        """Finds VPC configuration."""
        from replimap.deps.analyzers.lambda_func import LambdaFunctionAnalyzer

        analyzer = LambdaFunctionAnalyzer()
        data = {
            "VpcConfig": {
                "VpcId": "vpc-123",
                "SubnetIds": ["subnet-1", "subnet-2"],
                "SecurityGroupIds": ["sg-1"],
            }
        }

        network = analyzer._find_network(data)

        vpc = [n for n in network if n.resource_type == "aws_vpc"]
        subnets = [n for n in network if n.resource_type == "aws_subnet"]
        sgs = [n for n in network if n.resource_type == "aws_security_group"]

        assert len(vpc) == 1
        assert len(subnets) == 2
        assert len(sgs) == 1

    def test_find_execution_role(self):
        """Finds execution role."""
        from replimap.deps.analyzers.lambda_func import LambdaFunctionAnalyzer

        analyzer = LambdaFunctionAnalyzer()
        data = {"Role": "arn:aws:iam::123:role/my-lambda-role"}

        identity = analyzer._find_identity(data)

        roles = [i for i in identity if i.resource_type == "aws_iam_role"]
        assert len(roles) == 1
        assert roles[0].resource_name == "my-lambda-role"
        assert roles[0].severity == Severity.CRITICAL


# =============================================================================
# ANALYZER REGISTRY TESTS
# =============================================================================


class TestAnalyzerRegistry:
    """Test analyzer registration and lookup."""

    def test_get_ec2_analyzer(self):
        """Can get EC2 analyzer by resource ID."""
        from replimap.deps.analyzers import get_analyzer

        analyzer = get_analyzer("i-12345678")
        assert analyzer.resource_type == "aws_instance"

    def test_get_sg_analyzer(self):
        """Can get SG analyzer by resource ID."""
        from replimap.deps.analyzers import get_analyzer

        analyzer = get_analyzer("sg-12345678")
        assert analyzer.resource_type == "aws_security_group"

    def test_get_analyzer_by_type(self):
        """Can get analyzer by resource type."""
        from replimap.deps.analyzers import get_analyzer

        analyzer = get_analyzer("aws_db_instance")
        assert analyzer.resource_type == "aws_db_instance"

    def test_unsupported_resource(self):
        """Raises error for unsupported resource."""
        from replimap.deps.analyzers import get_analyzer

        with pytest.raises(ValueError, match="Unsupported resource"):
            get_analyzer("unsupported-resource-xyz")

    def test_all_analyzers_registered(self):
        """All analyzers are properly registered."""
        from replimap.deps.analyzers import ANALYZERS

        # P0 analyzers
        assert "aws_instance" in ANALYZERS
        assert "aws_security_group" in ANALYZERS
        assert "aws_iam_role" in ANALYZERS

        # P1 analyzers
        assert "aws_db_instance" in ANALYZERS
        assert "aws_autoscaling_group" in ANALYZERS
        assert "aws_s3_bucket" in ANALYZERS
        assert "aws_lambda_function" in ANALYZERS

        # P2 analyzers
        assert "aws_lb" in ANALYZERS
        assert "aws_elasticache_cluster" in ANALYZERS


# =============================================================================
# ELB ANALYZER TESTS (P2)
# =============================================================================


class TestELBAnalyzer:
    """Test ELB/ALB analyzer."""

    def test_analyzer_resource_type(self):
        """ELB analyzer has correct resource type."""
        from replimap.deps.analyzers.elb import ELBAnalyzer

        analyzer = ELBAnalyzer()
        assert analyzer.resource_type == "aws_lb"

    def test_find_vpc_network(self):
        """Finds VPC network dependency."""
        from replimap.deps.analyzers.elb import ELBAnalyzer

        analyzer = ELBAnalyzer()
        data = {
            "VpcId": "vpc-123",
            "AvailabilityZones": [
                {"SubnetId": "subnet-1", "ZoneName": "us-east-1a"},
                {"SubnetId": "subnet-2", "ZoneName": "us-east-1b"},
            ],
            "SecurityGroups": ["sg-123"],
        }

        network = analyzer._find_network(data, "application")

        vpc = [n for n in network if n.resource_type == "aws_vpc"]
        subnets = [n for n in network if n.resource_type == "aws_subnet"]
        sgs = [n for n in network if n.resource_type == "aws_security_group"]

        assert len(vpc) == 1
        assert len(subnets) == 2
        assert len(sgs) == 1  # ALB has SGs

    def test_nlb_no_security_groups(self):
        """NLB doesn't have security groups in network deps."""
        from replimap.deps.analyzers.elb import ELBAnalyzer

        analyzer = ELBAnalyzer()
        data = {
            "VpcId": "vpc-123",
            "AvailabilityZones": [],
            "SecurityGroups": ["sg-123"],
        }

        network = analyzer._find_network(data, "network")

        sgs = [n for n in network if n.resource_type == "aws_security_group"]
        assert len(sgs) == 0  # NLB doesn't use SGs

    def test_create_target_group_dep(self):
        """Creates target group dependency correctly."""
        from replimap.deps.analyzers.elb import ELBAnalyzer

        analyzer = ELBAnalyzer()
        listener = {"Port": 443, "Protocol": "HTTPS"}
        tg_arn = "arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/my-tg/abc"

        dep = analyzer._create_target_group_dep(tg_arn, listener)

        assert dep.resource_type == "aws_lb_target_group"
        assert dep.resource_name == "my-tg"
        assert dep.relation_type == RelationType.CONSUMER
        assert "HTTPS:443" in dep.warning


# =============================================================================
# ELASTICACHE ANALYZER TESTS (P2)
# =============================================================================


class TestElastiCacheAnalyzer:
    """Test ElastiCache analyzer."""

    def test_analyzer_resource_type(self):
        """ElastiCache analyzer has correct resource type."""
        from replimap.deps.analyzers.elasticache import ElastiCacheAnalyzer

        analyzer = ElastiCacheAnalyzer()
        assert analyzer.resource_type == "aws_elasticache_cluster"

    def test_find_replication_group(self):
        """Finds replication group membership."""
        from replimap.deps.analyzers.elasticache import ElastiCacheAnalyzer

        analyzer = ElastiCacheAnalyzer()
        data = {"ReplicationGroupId": "my-repl-group"}

        replication = analyzer._find_replication(data)

        assert len(replication) == 1
        assert replication[0].resource_type == "aws_elasticache_replication_group"
        assert replication[0].relation_type == RelationType.REPLICATION

    def test_find_parameter_group(self):
        """Finds parameter group dependency."""
        from replimap.deps.analyzers.elasticache import ElastiCacheAnalyzer

        analyzer = ElastiCacheAnalyzer()
        data = {
            "CacheParameterGroup": {
                "CacheParameterGroupName": "my-param-group",
                "ParameterApplyStatus": "in-sync",
            }
        }

        deps = analyzer._find_dependencies(data)

        pg = [d for d in deps if d.resource_type == "aws_elasticache_parameter_group"]
        assert len(pg) == 1
        assert pg[0].resource_id == "my-param-group"

    def test_find_security_groups(self):
        """Finds security group network deps."""
        from replimap.deps.analyzers.elasticache import ElastiCacheAnalyzer

        analyzer = ElastiCacheAnalyzer()
        data = {
            "SecurityGroups": [
                {"SecurityGroupId": "sg-123", "Status": "active"},
                {"SecurityGroupId": "sg-456", "Status": "active"},
            ]
        }

        network = analyzer._find_network(data)

        sgs = [n for n in network if n.resource_type == "aws_security_group"]
        assert len(sgs) == 2

    def test_get_endpoint_redis(self):
        """Gets Redis configuration endpoint."""
        from replimap.deps.analyzers.elasticache import ElastiCacheAnalyzer

        analyzer = ElastiCacheAnalyzer()
        data = {
            "ConfigurationEndpoint": {
                "Address": "my-cluster.abc123.clustercfg.use1.cache.amazonaws.com",
                "Port": 6379,
            }
        }

        endpoint = analyzer._get_endpoint(data)

        assert "my-cluster" in endpoint
        assert "6379" in endpoint

    def test_get_endpoint_memcached(self):
        """Gets Memcached node endpoint."""
        from replimap.deps.analyzers.elasticache import ElastiCacheAnalyzer

        analyzer = ElastiCacheAnalyzer()
        data = {
            "CacheNodes": [
                {
                    "Endpoint": {
                        "Address": "my-node.abc123.0001.use1.cache.amazonaws.com",
                        "Port": 11211,
                    }
                }
            ]
        }

        endpoint = analyzer._get_endpoint(data)

        assert "my-node" in endpoint
        assert "11211" in endpoint
