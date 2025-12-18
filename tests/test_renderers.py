"""Tests for the renderers module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from replimap.core import GraphEngine
from replimap.core.models import ResourceNode, ResourceType
from replimap.licensing.manager import LicenseManager, set_license_manager
from replimap.renderers import CloudFormationRenderer, PulumiRenderer, TerraformRenderer


@pytest.fixture
def sample_graph() -> GraphEngine:
    """Create a sample graph with resources."""
    graph = GraphEngine()

    # Add VPC
    vpc = ResourceNode(
        id="vpc-12345",
        resource_type=ResourceType.VPC,
        region="us-east-1",
        config={
            "cidr_block": "10.0.0.0/16",
            "enable_dns_hostnames": True,
            "enable_dns_support": True,
        },
        tags={"Name": "prod-vpc", "Environment": "production"},
    )
    graph.add_resource(vpc)

    # Add Subnet
    subnet = ResourceNode(
        id="subnet-12345",
        resource_type=ResourceType.SUBNET,
        region="us-east-1",
        config={
            "cidr_block": "10.0.1.0/24",
            "availability_zone": "us-east-1a",
            "map_public_ip_on_launch": True,
        },
        tags={"Name": "prod-subnet-1"},
    )
    subnet.add_dependency("vpc-12345")
    graph.add_resource(subnet)

    # Add Security Group
    sg = ResourceNode(
        id="sg-12345",
        resource_type=ResourceType.SECURITY_GROUP,
        region="us-east-1",
        config={
            "description": "Web server security group",
            "ingress": [
                {
                    "protocol": "tcp",
                    "from_port": 80,
                    "to_port": 80,
                    "cidr_blocks": ["0.0.0.0/0"],
                },
                {
                    "protocol": "tcp",
                    "from_port": 443,
                    "to_port": 443,
                    "cidr_blocks": ["0.0.0.0/0"],
                },
            ],
        },
        tags={"Name": "prod-web-sg"},
    )
    sg.add_dependency("vpc-12345")
    graph.add_resource(sg)

    # Add EC2 Instance
    ec2 = ResourceNode(
        id="i-12345",
        resource_type=ResourceType.EC2_INSTANCE,
        region="us-east-1",
        config={
            "instance_type": "t3.medium",
            "ami": "ami-0123456789abcdef0",
        },
        tags={"Name": "prod-web-server"},
    )
    ec2.add_dependency("subnet-12345")
    ec2.add_dependency("sg-12345")
    graph.add_resource(ec2)

    # Add S3 Bucket
    s3 = ResourceNode(
        id="prod-data-bucket",
        resource_type=ResourceType.S3_BUCKET,
        region="us-east-1",
        config={
            "bucket_name": "prod-data-bucket-12345",
            "versioning": True,
        },
        tags={"Name": "prod-data-bucket"},
    )
    graph.add_resource(s3)

    # Add dependencies
    graph.add_dependency("subnet-12345", "vpc-12345", "belongs_to")
    graph.add_dependency("sg-12345", "vpc-12345", "belongs_to")
    graph.add_dependency("i-12345", "subnet-12345", "belongs_to")
    graph.add_dependency("i-12345", "sg-12345", "uses")

    return graph


@pytest.fixture
def pro_license_manager():
    """Create a license manager with Pro plan for feature-gated tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = LicenseManager(cache_dir=Path(tmpdir))
        manager.activate("PRO0-1234-5678-ABCD")
        set_license_manager(manager)
        yield manager


class TestTerraformRenderer:
    """Tests for TerraformRenderer."""

    def test_render_creates_output_directory(self, sample_graph: GraphEngine) -> None:
        """Test that render creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            renderer.render(sample_graph, output_dir)
            assert output_dir.exists()

    def test_render_creates_vpc_file(self, sample_graph: GraphEngine) -> None:
        """Test that render creates vpc.tf."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "vpc.tf" in files
            assert files["vpc.tf"].exists()

    def test_render_creates_security_groups_file(
        self, sample_graph: GraphEngine
    ) -> None:
        """Test that render creates security_groups.tf."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "security_groups.tf" in files

    def test_render_creates_ec2_file(self, sample_graph: GraphEngine) -> None:
        """Test that render creates ec2.tf."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "ec2.tf" in files

    def test_render_creates_s3_file(self, sample_graph: GraphEngine) -> None:
        """Test that render creates s3.tf."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "s3.tf" in files

    def test_render_creates_variables_file(self, sample_graph: GraphEngine) -> None:
        """Test that render creates variables.tf."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "variables.tf" in files

    def test_render_creates_outputs_file(self, sample_graph: GraphEngine) -> None:
        """Test that render creates outputs.tf."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "outputs.tf" in files

    def test_preview_returns_file_mapping(self, sample_graph: GraphEngine) -> None:
        """Test that preview returns correct file mapping."""
        renderer = TerraformRenderer()
        preview = renderer.preview(sample_graph)

        assert "vpc.tf" in preview
        assert "security_groups.tf" in preview
        assert "ec2.tf" in preview
        assert "s3.tf" in preview

    def test_preview_groups_resources_correctly(
        self, sample_graph: GraphEngine
    ) -> None:
        """Test that preview groups resources by file."""
        renderer = TerraformRenderer()
        preview = renderer.preview(sample_graph)

        # VPC and Subnet should be in vpc.tf
        assert "vpc-12345" in preview["vpc.tf"]
        assert "subnet-12345" in preview["vpc.tf"]

        # Security Group should be in security_groups.tf
        assert "sg-12345" in preview["security_groups.tf"]


class TestCloudFormationRenderer:
    """Tests for CloudFormationRenderer."""

    def test_render_creates_output_directory(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "cloudformation"
            renderer = CloudFormationRenderer()
            renderer.render(sample_graph, output_dir)
            assert output_dir.exists()

    def test_render_creates_network_yaml(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates network.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "cloudformation"
            renderer = CloudFormationRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "network.yaml" in files
            assert files["network.yaml"].exists()

    def test_render_creates_compute_yaml(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates compute.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "cloudformation"
            renderer = CloudFormationRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "compute.yaml" in files

    def test_render_creates_storage_yaml(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates storage.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "cloudformation"
            renderer = CloudFormationRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "storage.yaml" in files

    def test_render_creates_main_yaml(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates main.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "cloudformation"
            renderer = CloudFormationRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "main.yaml" in files

    def test_render_produces_valid_yaml(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that rendered files are valid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "cloudformation"
            renderer = CloudFormationRenderer()
            files = renderer.render(sample_graph, output_dir)

            for filename, filepath in files.items():
                if filename.endswith(".yaml"):
                    with open(filepath) as f:
                        data = yaml.safe_load(f)
                    assert data is not None
                    assert "AWSTemplateFormatVersion" in data

    def test_render_includes_vpc_resource(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that VPC is included in network.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "cloudformation"
            renderer = CloudFormationRenderer()
            files = renderer.render(sample_graph, output_dir)

            with open(files["network.yaml"]) as f:
                data = yaml.safe_load(f)

            resources = data.get("Resources", {})
            vpc_resources = [
                k for k, v in resources.items() if v.get("Type") == "AWS::EC2::VPC"
            ]
            assert len(vpc_resources) > 0

    def test_preview_returns_file_mapping(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that preview returns correct file mapping."""
        renderer = CloudFormationRenderer()
        preview = renderer.preview(sample_graph)

        assert "network.yaml" in preview
        assert "compute.yaml" in preview
        assert "storage.yaml" in preview

    def test_renderer_name(self) -> None:
        """Test renderer name property."""
        renderer = CloudFormationRenderer()
        assert renderer.name == "CloudFormation"
        assert renderer.format_name == "cloudformation"


class TestPulumiRenderer:
    """Tests for PulumiRenderer."""

    def test_render_creates_output_directory(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pulumi"
            renderer = PulumiRenderer()
            renderer.render(sample_graph, output_dir)
            assert output_dir.exists()

    def test_render_creates_network_py(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates network.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pulumi"
            renderer = PulumiRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "network.py" in files
            assert files["network.py"].exists()

    def test_render_creates_compute_py(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates compute.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pulumi"
            renderer = PulumiRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "compute.py" in files

    def test_render_creates_storage_py(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates storage.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pulumi"
            renderer = PulumiRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "storage.py" in files

    def test_render_creates_main_py(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates __main__.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pulumi"
            renderer = PulumiRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "__main__.py" in files

    def test_render_creates_pulumi_yaml(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates Pulumi.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pulumi"
            renderer = PulumiRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "Pulumi.yaml" in files

    def test_render_creates_requirements_txt(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that render creates requirements.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pulumi"
            renderer = PulumiRenderer()
            files = renderer.render(sample_graph, output_dir)
            assert "requirements.txt" in files

    def test_render_produces_valid_python(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that rendered Python files have valid syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pulumi"
            renderer = PulumiRenderer()
            files = renderer.render(sample_graph, output_dir)

            for filename, filepath in files.items():
                if filename.endswith(".py"):
                    with open(filepath) as f:
                        code = f.read()
                    # This will raise SyntaxError if invalid
                    compile(code, filename, "exec")

    def test_render_includes_pulumi_imports(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that Python files include Pulumi imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pulumi"
            renderer = PulumiRenderer()
            files = renderer.render(sample_graph, output_dir)

            with open(files["network.py"]) as f:
                code = f.read()

            assert "import pulumi" in code
            assert "import pulumi_aws" in code

    def test_preview_returns_file_mapping(
        self, sample_graph: GraphEngine, pro_license_manager: LicenseManager
    ) -> None:
        """Test that preview returns correct file mapping."""
        renderer = PulumiRenderer()
        preview = renderer.preview(sample_graph)

        assert "network.py" in preview
        assert "compute.py" in preview
        assert "storage.py" in preview

    def test_renderer_name(self) -> None:
        """Test renderer name property."""
        renderer = PulumiRenderer()
        assert renderer.name == "Pulumi"
        assert renderer.format_name == "pulumi"


class TestRendererFeatureGating:
    """Tests for renderer feature gating."""

    def test_cloudformation_requires_license(self, sample_graph: GraphEngine) -> None:
        """Test that CloudFormation renderer requires Solo+ license."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up free tier license
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            output_dir = Path(tmpdir) / "cloudformation"
            renderer = CloudFormationRenderer()

            # Should raise FeatureNotAvailableError
            from replimap.licensing.gates import FeatureNotAvailableError

            with pytest.raises(FeatureNotAvailableError):
                renderer.render(sample_graph, output_dir)

    def test_pulumi_requires_license(self, sample_graph: GraphEngine) -> None:
        """Test that Pulumi renderer requires Pro+ license."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up free tier license
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            output_dir = Path(tmpdir) / "pulumi"
            renderer = PulumiRenderer()

            # Should raise FeatureNotAvailableError
            from replimap.licensing.gates import FeatureNotAvailableError

            with pytest.raises(FeatureNotAvailableError):
                renderer.render(sample_graph, output_dir)

    def test_terraform_works_on_free_tier(self, sample_graph: GraphEngine) -> None:
        """Test that Terraform renderer works on free tier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up free tier license
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()

            # Should work without raising
            files = renderer.render(sample_graph, output_dir)
            assert len(files) > 0


class TestTerraformRendererAdvanced:
    """Advanced tests for TerraformRenderer functionality."""

    def test_render_creates_versions_file(self, sample_graph: GraphEngine) -> None:
        """Test that render creates versions.tf with terraform requirements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(sample_graph, output_dir)

            assert "versions.tf" in files
            content = files["versions.tf"].read_text()
            assert "terraform {" in content
            assert "required_version" in content
            assert "required_providers" in content
            assert "hashicorp/aws" in content

    def test_render_creates_providers_file(self, sample_graph: GraphEngine) -> None:
        """Test that render creates providers.tf with AWS configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(sample_graph, output_dir)

            assert "providers.tf" in files
            content = files["providers.tf"].read_text()
            assert 'provider "aws"' in content
            assert "region = var.aws_region" in content
            assert "default_tags" in content

    def test_render_creates_tfvars_example(self, sample_graph: GraphEngine) -> None:
        """Test that render creates terraform.tfvars.example."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(sample_graph, output_dir)

            assert "terraform.tfvars.example" in files
            content = files["terraform.tfvars.example"].read_text()
            assert "environment" in content
            assert "aws_account_id" in content
            assert "aws_region" in content

    def test_render_generates_rds_password_variables(self) -> None:
        """Test that RDS instances get password variables generated."""
        graph = GraphEngine()

        # Add VPC
        vpc = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        # Add RDS Instance
        rds = ResourceNode(
            id="db-12345",
            resource_type=ResourceType.RDS_INSTANCE,
            region="us-east-1",
            config={
                "identifier": "test-db",
                "engine": "postgres",
                "engine_version": "14.7",
                "instance_class": "db.t3.micro",
            },
            tags={"Name": "test-db"},
        )
        graph.add_resource(rds)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(graph, output_dir)

            # Check variables.tf has RDS password variable
            variables_content = files["variables.tf"].read_text()
            assert "db_password_" in variables_content
            assert "sensitive   = true" in variables_content

            # Check tfvars example has placeholder
            tfvars_content = files["terraform.tfvars.example"].read_text()
            assert "db_password_" in tfvars_content

    def test_quote_key_filter_quotes_special_keys(self) -> None:
        """Test that quote_key filter properly quotes keys with spaces."""
        renderer = TerraformRenderer()

        # Valid identifier - should not be quoted
        assert renderer._quote_key_filter("Environment") == "Environment"
        assert renderer._quote_key_filter("Name") == "Name"
        assert renderer._quote_key_filter("my_tag") == "my_tag"

        # Keys with spaces - should be quoted
        assert renderer._quote_key_filter("Cost Center") == '"Cost Center"'
        assert renderer._quote_key_filter("My Tag Name") == '"My Tag Name"'

        # Keys starting with numbers - should be quoted
        assert renderer._quote_key_filter("123tag") == '"123tag"'

        # Empty key - should return empty quoted string
        assert renderer._quote_key_filter("") == '""'

    def test_unique_name_generation_for_duplicates(self) -> None:
        """Test that duplicate terraform names get unique suffixes."""
        graph = GraphEngine()

        # Add two VPCs with the same Name tag
        vpc1 = ResourceNode(
            id="vpc-11111111",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "shared-vpc"},
        )
        graph.add_resource(vpc1)

        vpc2 = ResourceNode(
            id="vpc-22222222",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"cidr_block": "10.1.0.0/16"},
            tags={"Name": "shared-vpc"},
        )
        graph.add_resource(vpc2)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            renderer.render(graph, output_dir)

            # After rendering, terraform_names should be unique
            names = [vpc1.terraform_name, vpc2.terraform_name]
            assert len(names) == len(set(names)), "Terraform names should be unique"

    def test_vpc_reference_resolution_in_subnet(self) -> None:
        """Test that subnet template properly resolves VPC reference."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "my-vpc"},
        )
        graph.add_resource(vpc)

        subnet = ResourceNode(
            id="subnet-12345",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            config={
                "vpc_id": "vpc-12345",
                "cidr_block": "10.0.1.0/24",
                "availability_zone": "us-east-1a",
            },
            tags={"Name": "my-subnet"},
        )
        graph.add_resource(subnet)
        graph.add_dependency("subnet-12345", "vpc-12345", "belongs_to")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(graph, output_dir)

            vpc_content = files["vpc.tf"].read_text()
            # Should have proper VPC reference, not aws_vpc..id
            assert "aws_vpc.my-vpc.id" in vpc_content
            assert "aws_vpc..id" not in vpc_content

    def test_tag_key_quoting_in_output(self) -> None:
        """Test that tags with special characters are properly quoted."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
            tags={
                "Name": "test-vpc",
                "Cost Center": "Platform",
                "Environment": "staging",
            },
        )
        graph.add_resource(vpc)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(graph, output_dir)

            vpc_content = files["vpc.tf"].read_text()
            # "Cost Center" should be quoted, Environment should not
            assert '"Cost Center"' in vpc_content
            assert 'Environment' in vpc_content  # Not quoted
            # Verify it's not double-quoted
            assert '""Cost Center""' not in vpc_content

    def test_outputs_include_rds_endpoints(self) -> None:
        """Test that outputs.tf includes RDS endpoint outputs."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        rds = ResourceNode(
            id="db-12345",
            resource_type=ResourceType.RDS_INSTANCE,
            region="us-east-1",
            config={
                "identifier": "mydb",
                "engine": "postgres",
                "engine_version": "14.7",
                "instance_class": "db.t3.micro",
            },
            tags={"Name": "mydb"},
        )
        graph.add_resource(rds)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(graph, output_dir)

            outputs_content = files["outputs.tf"].read_text()
            assert "_endpoint" in outputs_content
            assert "aws_db_instance" in outputs_content

    def test_outputs_include_lb_dns(self) -> None:
        """Test that outputs.tf includes LB DNS name outputs."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        lb = ResourceNode(
            id="arn:aws:elasticloadbalancing:us-east-1:123456789:loadbalancer/app/my-lb/123",
            resource_type=ResourceType.LB,
            region="us-east-1",
            config={
                "name": "my-lb",
                "type": "application",
                "scheme": "internet-facing",
                "subnet_ids": [],
                "security_group_ids": [],
            },
            tags={"Name": "my-lb"},
        )
        graph.add_resource(lb)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            renderer = TerraformRenderer()
            files = renderer.render(graph, output_dir)

            outputs_content = files["outputs.tf"].read_text()
            assert "_dns_name" in outputs_content
            assert "aws_lb" in outputs_content
