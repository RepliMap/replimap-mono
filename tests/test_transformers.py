"""Tests for Transformers."""

from replimap.core.graph_engine import GraphEngine
from replimap.core.models import ResourceNode, ResourceType
from replimap.transformers import (
    DownsizeTransformer,
    NetworkRemapTransformer,
    RenamingTransformer,
    SanitizationTransformer,
    TransformationPipeline,
    create_default_pipeline,
)


class TestSanitizationTransformer:
    """Tests for SanitizationTransformer."""

    def test_removes_sensitive_fields(self) -> None:
        """Test that sensitive fields are removed."""
        graph = GraphEngine()
        node = ResourceNode(
            id="test-1",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={
                "ami": "ami-12345",
                "password": "secret123",
                "api_key": "abc123",
                "normal_field": "keep this",
            },
        )
        graph.add_resource(node)

        transformer = SanitizationTransformer()
        transformer.transform(graph)

        result = graph.get_resource("test-1")
        assert "password" not in result.config
        assert "api_key" not in result.config
        assert result.config["normal_field"] == "keep this"
        assert result.config["ami"] == "ami-12345"

    def test_replaces_account_ids_in_arn(self) -> None:
        """Test that account IDs are replaced in ARNs."""
        graph = GraphEngine()
        node = ResourceNode(
            id="test-1",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            arn="arn:aws:ec2:us-east-1:123456789012:vpc/vpc-12345",
            config={},
        )
        graph.add_resource(node)

        transformer = SanitizationTransformer()
        transformer.transform(graph)

        result = graph.get_resource("test-1")
        assert "123456789012" not in result.arn
        assert "${var.aws_account_id}" in result.arn

    def test_preserves_non_sensitive_data(self) -> None:
        """Test that non-sensitive data is preserved."""
        graph = GraphEngine()
        node = ResourceNode(
            id="test-1",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={
                "instance_type": "t3.micro",
                "subnet_id": "subnet-12345",
            },
            tags={"Name": "my-instance", "Environment": "prod"},
        )
        graph.add_resource(node)

        transformer = SanitizationTransformer()
        transformer.transform(graph)

        result = graph.get_resource("test-1")
        assert result.config["instance_type"] == "t3.micro"
        assert result.tags["Name"] == "my-instance"


class TestDownsizeTransformer:
    """Tests for DownsizeTransformer."""

    def test_downsizes_ec2_instances(self) -> None:
        """Test EC2 instance downsizing."""
        graph = GraphEngine()
        node = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={"instance_type": "m5.xlarge"},
        )
        graph.add_resource(node)

        transformer = DownsizeTransformer()
        transformer.transform(graph)

        result = graph.get_resource("i-12345")
        assert result.config["instance_type"] == "t3.medium"
        assert result.config["_original_instance_type"] == "m5.xlarge"

    def test_downsizes_rds_instances(self) -> None:
        """Test RDS instance downsizing."""
        graph = GraphEngine()
        node = ResourceNode(
            id="db-prod",
            resource_type=ResourceType.RDS_INSTANCE,
            region="us-east-1",
            config={
                "instance_class": "db.m5.large",
                "multi_az": True,
                "allocated_storage": 500,
            },
        )
        graph.add_resource(node)

        transformer = DownsizeTransformer()
        transformer.transform(graph)

        result = graph.get_resource("db-prod")
        assert result.config["instance_class"] == "db.t3.medium"
        assert result.config["multi_az"] is False
        assert result.config["allocated_storage"] < 500

    def test_preserves_small_instances(self) -> None:
        """Test that already small instances are preserved or minimized."""
        graph = GraphEngine()
        node = ResourceNode(
            id="i-small",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={"instance_type": "t3.micro"},
        )
        graph.add_resource(node)

        transformer = DownsizeTransformer()
        transformer.transform(graph)

        result = graph.get_resource("i-small")
        assert result.config["instance_type"] == "t3.micro"


class TestRenamingTransformer:
    """Tests for RenamingTransformer."""

    def test_renames_prod_to_stage(self) -> None:
        """Test renaming prod to stage."""
        graph = GraphEngine()
        node = ResourceNode(
            id="vpc-prod",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Name": "my-production-vpc"},
            config={"name": "production-network"},
        )
        graph.add_resource(node)

        transformer = RenamingTransformer()
        transformer.transform(graph)

        result = graph.get_resource("vpc-prod")
        assert "staging" in result.tags["Name"]
        assert "production" not in result.tags["Name"]

    def test_from_pattern_factory(self) -> None:
        """Test creating transformer from pattern string."""
        transformer = RenamingTransformer.from_pattern("foo:bar,prod:dev")

        assert "foo" in transformer.replacements
        assert transformer.replacements["foo"] == "bar"
        assert transformer.replacements["prod"] == "dev"

    def test_case_insensitive_matching(self) -> None:
        """Test case-insensitive pattern matching."""
        graph = GraphEngine()
        node = ResourceNode(
            id="test-1",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Name": "PRODUCTION-vpc"},
            config={},
        )
        graph.add_resource(node)

        transformer = RenamingTransformer(case_insensitive=True)
        transformer.transform(graph)

        result = graph.get_resource("test-1")
        assert "PRODUCTION" not in result.tags["Name"]


class TestNetworkRemapTransformer:
    """Tests for NetworkRemapTransformer."""

    def test_builds_id_map(self) -> None:
        """Test that ID map is built correctly."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={},
        )
        subnet = ResourceNode(
            id="subnet-12345",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            config={"vpc_id": "vpc-12345"},
        )

        graph.add_resource(vpc)
        graph.add_resource(subnet)
        graph.add_dependency("subnet-12345", "vpc-12345")

        transformer = NetworkRemapTransformer()
        transformer.transform(graph)

        # Check that IDs are mapped to Terraform references
        assert "vpc-12345" in transformer._id_map
        assert "aws_vpc" in transformer._id_map["vpc-12345"]

    def test_remaps_subnet_vpc_reference(self) -> None:
        """Test that subnet VPC reference is remapped."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={},
        )
        vpc.terraform_name = "main_vpc"

        subnet = ResourceNode(
            id="subnet-12345",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            config={"vpc_id": "vpc-12345"},
        )

        graph.add_resource(vpc)
        graph.add_resource(subnet)

        transformer = NetworkRemapTransformer()
        transformer.transform(graph)

        result = graph.get_resource("subnet-12345")
        assert "aws_vpc.main_vpc.id" in result.config["vpc_id"]


class TestTransformationPipeline:
    """Tests for TransformationPipeline."""

    def test_executes_multiple_transformers(self) -> None:
        """Test that pipeline executes transformers in order."""
        graph = GraphEngine()
        node = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={
                "instance_type": "m5.xlarge",
                "password": "secret",
            },
            tags={"Name": "production-server"},
        )
        graph.add_resource(node)

        pipeline = TransformationPipeline()
        pipeline.add(SanitizationTransformer())
        pipeline.add(DownsizeTransformer())
        pipeline.add(RenamingTransformer())

        pipeline.execute(graph)

        result = graph.get_resource("i-12345")

        # Sanitization: password removed
        assert "password" not in result.config

        # Downsize: instance type changed
        assert result.config["instance_type"] == "t3.medium"

        # Rename: production -> staging
        assert "staging" in result.tags["Name"]

    def test_method_chaining(self) -> None:
        """Test that add() returns self for chaining."""
        pipeline = (
            TransformationPipeline()
            .add(SanitizationTransformer())
            .add(DownsizeTransformer())
        )

        assert len(pipeline) == 2


class TestCreateDefaultPipeline:
    """Tests for create_default_pipeline function."""

    def test_creates_pipeline_with_all_transformers(self) -> None:
        """Test default pipeline includes all transformers."""
        pipeline = create_default_pipeline()
        assert len(pipeline) == 4  # Sanitize, Rename, Downsize, NetworkRemap

    def test_respects_downsize_flag(self) -> None:
        """Test that downsize flag is respected."""
        pipeline = create_default_pipeline(downsize=False)
        assert len(pipeline) == 3  # No DownsizeTransformer

    def test_respects_sanitize_flag(self) -> None:
        """Test that sanitize flag is respected."""
        pipeline = create_default_pipeline(sanitize=False)
        assert len(pipeline) == 3  # No SanitizationTransformer
