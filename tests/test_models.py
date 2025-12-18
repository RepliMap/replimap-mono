"""Tests for core models."""

from replimap.core.models import DependencyType, ResourceNode, ResourceType


class TestResourceNode:
    """Tests for ResourceNode dataclass."""

    def test_create_basic_node(self) -> None:
        """Test creating a basic ResourceNode."""
        node = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "my-vpc"},
        )

        assert node.id == "vpc-12345"
        assert node.resource_type == ResourceType.VPC
        assert node.region == "us-east-1"
        assert node.config["cidr_block"] == "10.0.0.0/16"
        assert node.tags["Name"] == "my-vpc"

    def test_terraform_name_generation(self) -> None:
        """Test automatic Terraform name generation."""
        node = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Name": "my-vpc-production"},
        )

        assert node.terraform_name == "my-vpc-production"

    def test_terraform_name_sanitization(self) -> None:
        """Test Terraform name sanitization for invalid characters."""
        node = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Name": "My VPC (production)"},
        )

        # Spaces and parentheses should be replaced with underscores
        assert "(" not in node.terraform_name
        assert ")" not in node.terraform_name
        assert " " not in node.terraform_name

    def test_terraform_name_numeric_prefix(self) -> None:
        """Test Terraform name with numeric prefix gets prefixed."""
        node = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Name": "123-vpc"},
        )

        # Should be prefixed with 'r_'
        assert node.terraform_name.startswith("r_")

    def test_node_hash_and_equality(self) -> None:
        """Test node hashing and equality based on ID."""
        node1 = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        node2 = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-west-2",  # Different region
        )
        node3 = ResourceNode(
            id="vpc-67890",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )

        # Same ID = equal
        assert node1 == node2
        assert hash(node1) == hash(node2)

        # Different ID = not equal
        assert node1 != node3

    def test_add_dependency(self) -> None:
        """Test adding dependencies to a node."""
        node = ResourceNode(
            id="subnet-12345",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
        )

        node.add_dependency("vpc-12345")
        assert "vpc-12345" in node.dependencies

        # Adding same dependency again should not duplicate
        node.add_dependency("vpc-12345")
        assert node.dependencies.count("vpc-12345") == 1

    def test_to_dict_and_from_dict(self) -> None:
        """Test serialization and deserialization."""
        original = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "my-vpc", "Environment": "prod"},
            dependencies=["some-dep"],
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = ResourceNode.from_dict(data)

        assert restored.id == original.id
        assert restored.resource_type == original.resource_type
        assert restored.region == original.region
        assert restored.config == original.config
        assert restored.tags == original.tags
        assert restored.dependencies == original.dependencies

    def test_get_tag(self) -> None:
        """Test getting tag values."""
        node = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Name": "my-vpc", "Environment": "prod"},
        )

        assert node.get_tag("Name") == "my-vpc"
        assert node.get_tag("Environment") == "prod"
        assert node.get_tag("Missing") is None
        assert node.get_tag("Missing", "default") == "default"


class TestResourceType:
    """Tests for ResourceType enum."""

    def test_string_representation(self) -> None:
        """Test that ResourceType converts to proper Terraform type."""
        assert str(ResourceType.VPC) == "aws_vpc"
        assert str(ResourceType.SUBNET) == "aws_subnet"
        assert str(ResourceType.EC2_INSTANCE) == "aws_instance"
        assert str(ResourceType.S3_BUCKET) == "aws_s3_bucket"
        assert str(ResourceType.RDS_INSTANCE) == "aws_db_instance"


class TestDependencyType:
    """Tests for DependencyType enum."""

    def test_string_representation(self) -> None:
        """Test that DependencyType converts to string."""
        assert str(DependencyType.BELONGS_TO) == "belongs_to"
        assert str(DependencyType.USES) == "uses"
        assert str(DependencyType.REFERENCES) == "references"
