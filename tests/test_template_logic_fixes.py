"""
Tests for template logic fixes.

These tests verify the fixes for various template issues including:
- Launch Template network_interfaces, image_id, key_name variabilization
- EC2 Instance AMI and key_name variabilization
- RDS Instance lifecycle ignore_changes
- Route Table additional target types
- LB Listener certificate_arn variabilization
- Security Group self-reference and prefix_list_ids handling
- NetworkRemapper extended mappings
"""

import tempfile
from pathlib import Path

from replimap.core import GraphEngine
from replimap.core.models import ResourceNode, ResourceType
from replimap.renderers.terraform import TerraformRenderer
from replimap.transformers.network_remapper import NetworkRemapTransformer


class TestLaunchTemplateNetworkInterfaces:
    """Test Launch Template network_interfaces handling."""

    def test_network_interfaces_subnet_mapping(self):
        """Verify network_interfaces.subnet_id is properly mapped."""
        graph = GraphEngine()

        # Add subnet
        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            original_name="app-subnet",
            config={"cidr_block": "10.0.1.0/24", "vpc_id": "vpc-123"},
            tags={"Name": "app-subnet"},
        )
        graph.add_resource(subnet)

        # Add launch template with network_interfaces
        lt = ResourceNode(
            id="lt-123",
            resource_type=ResourceType.LAUNCH_TEMPLATE,
            region="us-east-1",
            original_name="app-lt",
            config={
                "name": "app-template",
                "instance_type": "t3.micro",
                "image_id": "ami-12345678",
                "network_interfaces": [
                    {
                        "device_index": 0,
                        "subnet_id": "subnet-123",
                        "security_groups": ["sg-123"],
                    }
                ],
                "monitoring": {"Enabled": True},
            },
            tags={"Name": "app-lt"},
        )
        graph.add_resource(lt)

        # Render
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            compute_file = Path(tmpdir) / "compute.tf"
            content = compute_file.read_text()

            # Should have network_interfaces block
            assert "network_interfaces {" in content
            # Subnet should be mapped
            assert "aws_subnet.app-subnet.id" in content

    def test_image_id_variabilization(self):
        """Verify image_id is variabilized, not hardcoded."""
        graph = GraphEngine()

        lt = ResourceNode(
            id="lt-456",
            resource_type=ResourceType.LAUNCH_TEMPLATE,
            region="us-east-1",
            original_name="app-lt",
            config={
                "name": "app-template",
                "instance_type": "t3.micro",
                "image_id": "ami-0123456789abcdef0",
                "monitoring": {"Enabled": False},
            },
            tags={"Name": "app-lt"},
        )
        graph.add_resource(lt)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            compute_file = Path(tmpdir) / "compute.tf"
            content = compute_file.read_text()

            # Should use variable for AMI
            assert "var.ami_id_" in content
            # Should have original AMI as comment
            assert "ami-0123456789abcdef0" in content

    def test_key_name_variabilization(self):
        """Verify key_name is variabilized."""
        graph = GraphEngine()

        lt = ResourceNode(
            id="lt-789",
            resource_type=ResourceType.LAUNCH_TEMPLATE,
            region="us-east-1",
            original_name="app-lt",
            config={
                "name": "app-template",
                "instance_type": "t3.micro",
                "key_name": "my-prod-key",
                "monitoring": {"Enabled": False},
            },
            tags={"Name": "app-lt"},
        )
        graph.add_resource(lt)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            compute_file = Path(tmpdir) / "compute.tf"
            content = compute_file.read_text()

            # Should use variable for key_name
            assert "var.key_name" in content


class TestEC2InstanceVariabilization:
    """Test EC2 Instance AMI and key_name variabilization."""

    def test_ami_variabilization(self):
        """Verify EC2 ami is variabilized."""
        graph = GraphEngine()

        ec2 = ResourceNode(
            id="i-123",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            original_name="app-server",
            config={
                "ami": "ami-0abcdef1234567890",
                "instance_type": "t3.medium",
            },
            tags={"Name": "app-server"},
        )
        graph.add_resource(ec2)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            ec2_file = Path(tmpdir) / "ec2.tf"
            content = ec2_file.read_text()

            # Should use variable for AMI
            assert "var.ami_id" in content
            # Should have original AMI as comment
            assert "ami-0abcdef1234567890" in content


class TestRDSInstanceLifecycle:
    """Test RDS Instance lifecycle ignore_changes for password."""

    def test_lifecycle_ignore_password(self):
        """Verify RDS has lifecycle ignore_changes for password."""
        graph = GraphEngine()

        rds = ResourceNode(
            id="rds-123",
            resource_type=ResourceType.RDS_INSTANCE,
            region="us-east-1",
            original_name="app-db",
            config={
                "identifier": "app-db",
                "engine": "postgres",
                "engine_version": "14.9",
                "instance_class": "db.t3.micro",
                "master_username": "admin",
            },
            tags={"Name": "app-db"},
        )
        graph.add_resource(rds)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            rds_file = Path(tmpdir) / "rds.tf"
            content = rds_file.read_text()

            # Should have lifecycle block
            assert "lifecycle {" in content
            # Should ignore password changes
            assert "ignore_changes = [password]" in content


class TestRouteTableTargetTypes:
    """Test Route Table handles all target types."""

    def test_vpc_peering_route(self):
        """Verify VPC peering route is handled with boundary note."""
        graph = GraphEngine()

        # Add VPC
        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="main-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "main-vpc"},
        )
        graph.add_resource(vpc)

        rt = ResourceNode(
            id="rtb-123",
            resource_type=ResourceType.ROUTE_TABLE,
            region="us-east-1",
            original_name="main-rt",
            config={
                "vpc_id": "vpc-123",
                "routes": [
                    {
                        "destination_cidr_block": "10.1.0.0/16",
                        "vpc_peering_connection_id": "pcx-12345",
                    }
                ],
                "associations": [],
            },
            tags={"Name": "main-rt"},
        )
        graph.add_resource(rt)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            net_file = Path(tmpdir) / "networking.tf"
            content = net_file.read_text()

            # Should have VPC peering route
            assert "vpc_peering_connection_id" in content
            # Should have boundary note
            assert "boundary resource" in content.lower()

    def test_transit_gateway_route(self):
        """Verify Transit Gateway route is handled with boundary note."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-456",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="main-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "main-vpc"},
        )
        graph.add_resource(vpc)

        rt = ResourceNode(
            id="rtb-456",
            resource_type=ResourceType.ROUTE_TABLE,
            region="us-east-1",
            original_name="main-rt",
            config={
                "vpc_id": "vpc-456",
                "routes": [
                    {
                        "destination_cidr_block": "10.2.0.0/16",
                        "transit_gateway_id": "tgw-12345",
                    }
                ],
                "associations": [],
            },
            tags={"Name": "main-rt"},
        )
        graph.add_resource(rt)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            net_file = Path(tmpdir) / "networking.tf"
            content = net_file.read_text()

            # Should have transit gateway route
            assert "transit_gateway_id" in content
            # Should have boundary note
            assert "boundary resource" in content.lower()

    def test_instance_id_route_mapping(self):
        """Verify instance_id route is mapped to terraform reference."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-789",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="main-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "main-vpc"},
        )
        graph.add_resource(vpc)

        ec2 = ResourceNode(
            id="i-nat123",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            original_name="nat-instance",
            config={"ami": "ami-123", "instance_type": "t3.micro"},
            tags={"Name": "nat-instance"},
        )
        graph.add_resource(ec2)

        rt = ResourceNode(
            id="rtb-789",
            resource_type=ResourceType.ROUTE_TABLE,
            region="us-east-1",
            original_name="private-rt",
            config={
                "vpc_id": "vpc-789",
                "routes": [
                    {
                        "destination_cidr_block": "0.0.0.0/0",
                        "instance_id": "i-nat123",
                    }
                ],
                "associations": [],
            },
            tags={"Name": "private-rt"},
        )
        graph.add_resource(rt)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            net_file = Path(tmpdir) / "networking.tf"
            content = net_file.read_text()

            # Should have mapped instance_id
            assert "aws_instance.nat-instance.id" in content


class TestLBListenerCertificate:
    """Test LB Listener certificate_arn variabilization."""

    def test_certificate_arn_variabilization(self):
        """Verify certificate_arn is variabilized."""
        graph = GraphEngine()

        # Add LB first
        lb = ResourceNode(
            id="arn:aws:elasticloadbalancing:us-east-1:123456789:loadbalancer/app/main-lb/1234",
            resource_type=ResourceType.LB,
            region="us-east-1",
            original_name="main-lb",
            config={
                "name": "main-lb",
                "type": "application",
                "scheme": "internet-facing",
            },
            tags={"Name": "main-lb"},
        )
        graph.add_resource(lb)

        listener = ResourceNode(
            id="arn:aws:elasticloadbalancing:us-east-1:123456789:listener/app/main-lb/1234/5678",
            resource_type=ResourceType.LB_LISTENER,
            region="us-east-1",
            original_name="https-listener",
            config={
                "load_balancer_arn": lb.id,
                "port": 443,
                "protocol": "HTTPS",
                "ssl_policy": "ELBSecurityPolicy-2016-08",
                "certificate_arn": "arn:aws:acm:us-east-1:123456789:certificate/abc-123",
                "default_actions": [
                    {
                        "type": "forward",
                        "target_group_arn": "arn:aws:...",
                    }
                ],
            },
            tags={},
        )
        graph.add_resource(listener)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            alb_file = Path(tmpdir) / "alb.tf"
            content = alb_file.read_text()

            # Should use variable for certificate
            assert "var.acm_certificate_arn" in content
            # Should have original certificate as comment
            assert "arn:aws:acm:" in content


class TestSecurityGroupSelfReference:
    """Test Security Group self-reference handling."""

    def test_self_reference_detection(self):
        """Verify self-referencing SG rules use self=true."""
        graph = GraphEngine()

        sg = ResourceNode(
            id="sg-cluster123",
            resource_type=ResourceType.SECURITY_GROUP,
            region="us-east-1",
            original_name="cluster-sg",
            config={
                "name": "cluster-sg",
                "description": "Cluster SG",
                "vpc_id": "vpc-123",
                "ingress": [
                    {
                        "protocol": "-1",
                        "from_port": 0,
                        "to_port": 0,
                        "security_groups": [
                            {"security_group_id": "sg-cluster123"}  # Self-reference
                        ],
                    }
                ],
                "egress": [],
            },
            tags={"Name": "cluster-sg"},
        )
        graph.add_resource(sg)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            sg_file = Path(tmpdir) / "security_groups.tf"
            content = sg_file.read_text()

            # Should have self = true
            assert "self" in content and "true" in content

    def test_prefix_list_ids_handling(self):
        """Verify prefix_list_ids are included in output."""
        graph = GraphEngine()

        sg = ResourceNode(
            id="sg-with-pl",
            resource_type=ResourceType.SECURITY_GROUP,
            region="us-east-1",
            original_name="prefix-list-sg",
            config={
                "name": "prefix-list-sg",
                "description": "SG with prefix list",
                "vpc_id": "vpc-123",
                "ingress": [
                    {
                        "protocol": "tcp",
                        "from_port": 443,
                        "to_port": 443,
                        "prefix_list_ids": ["pl-12345678"],
                    }
                ],
                "egress": [],
            },
            tags={"Name": "prefix-list-sg"},
        )
        graph.add_resource(sg)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            sg_file = Path(tmpdir) / "security_groups.tf"
            content = sg_file.read_text()

            # Should have prefix_list_ids
            assert "prefix_list_ids" in content
            assert "pl-12345678" in content


class TestNetworkRemapperExtendedMappings:
    """Test NetworkRemapper handles additional resource types."""

    def test_route_table_mapping(self):
        """Verify route tables are mapped."""
        graph = GraphEngine()

        rt = ResourceNode(
            id="rtb-123",
            resource_type=ResourceType.ROUTE_TABLE,
            region="us-east-1",
            original_name="main-rt",
            config={},
            tags={"Name": "main-rt"},
        )
        graph.add_resource(rt)

        remapper = NetworkRemapTransformer(use_terraform_refs=True)
        remapper._build_id_map(graph)

        assert "rtb-123" in remapper._id_map
        assert "aws_route_table.main-rt.id" in remapper._id_map["rtb-123"]

    def test_internet_gateway_mapping(self):
        """Verify internet gateways are mapped."""
        graph = GraphEngine()

        igw = ResourceNode(
            id="igw-123",
            resource_type=ResourceType.INTERNET_GATEWAY,
            region="us-east-1",
            original_name="main-igw",
            config={},
            tags={"Name": "main-igw"},
        )
        graph.add_resource(igw)

        remapper = NetworkRemapTransformer(use_terraform_refs=True)
        remapper._build_id_map(graph)

        assert "igw-123" in remapper._id_map
        assert "aws_internet_gateway.main-igw.id" in remapper._id_map["igw-123"]

    def test_nat_gateway_mapping(self):
        """Verify NAT gateways are mapped."""
        graph = GraphEngine()

        nat = ResourceNode(
            id="nat-123",
            resource_type=ResourceType.NAT_GATEWAY,
            region="us-east-1",
            original_name="main-nat",
            config={},
            tags={"Name": "main-nat"},
        )
        graph.add_resource(nat)

        remapper = NetworkRemapTransformer(use_terraform_refs=True)
        remapper._build_id_map(graph)

        assert "nat-123" in remapper._id_map
        assert "aws_nat_gateway.main-nat.id" in remapper._id_map["nat-123"]

    def test_launch_template_mapping(self):
        """Verify launch templates are mapped."""
        graph = GraphEngine()

        lt = ResourceNode(
            id="lt-123",
            resource_type=ResourceType.LAUNCH_TEMPLATE,
            region="us-east-1",
            original_name="app-lt",
            config={},
            tags={"Name": "app-lt"},
        )
        graph.add_resource(lt)

        remapper = NetworkRemapTransformer(use_terraform_refs=True)
        remapper._build_id_map(graph)

        assert "lt-123" in remapper._id_map
        assert "aws_launch_template.app-lt.id" in remapper._id_map["lt-123"]

    def test_looks_like_network_id_extended(self):
        """Verify _looks_like_network_id detects new prefixes."""
        remapper = NetworkRemapTransformer()

        # Original prefixes
        assert remapper._looks_like_network_id("vpc-123")
        assert remapper._looks_like_network_id("subnet-456")
        assert remapper._looks_like_network_id("sg-789")
        assert remapper._looks_like_network_id("i-abc")

        # New prefixes
        assert remapper._looks_like_network_id("rtb-123")
        assert remapper._looks_like_network_id("igw-456")
        assert remapper._looks_like_network_id("nat-789")
        assert remapper._looks_like_network_id("eni-abc")
        assert remapper._looks_like_network_id("lt-def")

        # Non-network IDs
        assert not remapper._looks_like_network_id("vol-123")
        assert not remapper._looks_like_network_id("snap-456")
        assert not remapper._looks_like_network_id("ami-789")


class TestLaunchTemplateBlockDeviceMappings:
    """Test Launch Template block_device_mappings handling."""

    def test_block_device_mappings_rendered(self):
        """Verify block_device_mappings are rendered."""
        graph = GraphEngine()

        lt = ResourceNode(
            id="lt-bdm",
            resource_type=ResourceType.LAUNCH_TEMPLATE,
            region="us-east-1",
            original_name="app-lt",
            config={
                "name": "app-template",
                "instance_type": "t3.micro",
                "monitoring": {"Enabled": False},
                "block_device_mappings": [
                    {
                        "device_name": "/dev/xvda",
                        "ebs": {
                            "volume_size": 100,
                            "volume_type": "gp3",
                            "encrypted": True,
                            "delete_on_termination": True,
                        },
                    }
                ],
            },
            tags={"Name": "app-lt"},
        )
        graph.add_resource(lt)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            compute_file = Path(tmpdir) / "compute.tf"
            content = compute_file.read_text()

            # Should have block_device_mappings
            assert "block_device_mappings {" in content
            assert "device_name" in content
            assert "/dev/xvda" in content
            # Check for volume_size = 100 with flexible whitespace (terraform fmt aligns)
            import re

            assert re.search(r"volume_size\s+=\s+100", content), (
                "volume_size = 100 not found"
            )
            assert "volume_type" in content
            assert "gp3" in content


class TestVariablesGeneration:
    """Test variables.tf generation includes all new variables."""

    def test_ami_variable_generated(self):
        """Verify ami_id variable is generated for EC2 instances."""
        graph = GraphEngine()

        ec2 = ResourceNode(
            id="i-123",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            original_name="app-server",
            config={"ami": "ami-0123456", "instance_type": "t3.micro"},
            tags={"Name": "app-server"},
        )
        graph.add_resource(ec2)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            vars_file = Path(tmpdir) / "variables.tf"
            content = vars_file.read_text()

            assert 'variable "ami_id"' in content
            assert "ami-0123456" in content  # Original AMI in comment

    def test_key_name_variable_generated(self):
        """Verify key_name variable is generated when EC2 has key."""
        graph = GraphEngine()

        ec2 = ResourceNode(
            id="i-123",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            original_name="app-server",
            config={
                "ami": "ami-123",
                "instance_type": "t3.micro",
                "key_name": "my-key",
            },
            tags={"Name": "app-server"},
        )
        graph.add_resource(ec2)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            vars_file = Path(tmpdir) / "variables.tf"
            content = vars_file.read_text()

            assert 'variable "key_name"' in content

    def test_acm_certificate_variable_generated(self):
        """Verify acm_certificate_arn variable is generated for HTTPS listeners."""
        graph = GraphEngine()

        lb = ResourceNode(
            id="arn:aws:elasticloadbalancing:us-east-1:123:lb/app/my-lb/123",
            resource_type=ResourceType.LB,
            region="us-east-1",
            original_name="my-lb",
            config={"name": "my-lb", "type": "application"},
            tags={"Name": "my-lb"},
        )
        graph.add_resource(lb)

        listener = ResourceNode(
            id="arn:aws:elasticloadbalancing:us-east-1:123:listener/app/my-lb/123/456",
            resource_type=ResourceType.LB_LISTENER,
            region="us-east-1",
            original_name="https-listener",
            config={
                "load_balancer_arn": lb.id,
                "port": 443,
                "protocol": "HTTPS",
                "certificate_arn": "arn:aws:acm:us-east-1:123:certificate/abc",
                "default_actions": [],
            },
            tags={},
        )
        graph.add_resource(listener)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            vars_file = Path(tmpdir) / "variables.tf"
            content = vars_file.read_text()

            assert 'variable "acm_certificate_arn"' in content
            assert "arn:aws:acm" in content  # Original cert in comment


class TestDataSourcesGeneration:
    """Test data.tf generation for dynamic values."""

    def test_data_sources_generated(self):
        """Verify data.tf is generated with account_id and region."""
        graph = GraphEngine()

        # Add minimal resource
        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="main-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "main-vpc"},
        )
        graph.add_resource(vpc)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            data_file = Path(tmpdir) / "data.tf"
            assert data_file.exists()

            content = data_file.read_text()
            assert 'data "aws_caller_identity" "current"' in content
            assert 'data "aws_region" "current"' in content
            assert "local.account_id" in content
            assert "local.region" in content


class TestRDSSnapshotHandling:
    """Test RDS snapshot_identifier variabilization."""

    def test_snapshot_variable_generated(self):
        """Verify snapshot variable is generated when RDS has snapshot."""
        graph = GraphEngine()

        rds = ResourceNode(
            id="rds-123",
            resource_type=ResourceType.RDS_INSTANCE,
            region="us-east-1",
            original_name="app-db",
            config={
                "identifier": "app-db",
                "engine": "postgres",
                "engine_version": "14.9",
                "instance_class": "db.t3.micro",
                "master_username": "admin",
                "snapshot_identifier": "rds:app-db-2024-01-01",
            },
            tags={"Name": "app-db"},
        )
        graph.add_resource(rds)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            # Check variables.tf has snapshot variable
            vars_file = Path(tmpdir) / "variables.tf"
            vars_content = vars_file.read_text()
            assert 'variable "db_snapshot_' in vars_content
            assert "rds:app-db-2024-01-01" in vars_content  # Original snapshot

            # Check rds.tf has conditional snapshot
            rds_file = Path(tmpdir) / "rds.tf"
            rds_content = rds_file.read_text()
            assert "snapshot_identifier" in rds_content


class TestNoneValueHandling:
    """Test that None values from AWS API are properly handled."""

    def test_rds_port_none_uses_default(self):
        """Verify RDS port=None uses default value instead of literal 'None'."""
        graph = GraphEngine()

        rds = ResourceNode(
            id="rds-none-port",
            resource_type=ResourceType.RDS_INSTANCE,
            region="us-east-1",
            original_name="app-db",
            config={
                "identifier": "app-db",
                "engine": "postgres",
                "engine_version": "14.9",
                "instance_class": "db.t3.micro",
                "master_username": "admin",
                "port": None,  # Explicitly None
                "allocated_storage": None,
                "backup_retention_period": None,
            },
            tags={"Name": "app-db"},
        )
        graph.add_resource(rds)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            rds_file = Path(tmpdir) / "rds.tf"
            content = rds_file.read_text()

            # Should NOT have literal "None"
            assert "= None" not in content
            # Should have proper default values
            assert "port     = 5432" in content or "port" not in content

    def test_sqs_none_values_use_defaults(self):
        """Verify SQS None values use defaults."""
        graph = GraphEngine()

        sqs = ResourceNode(
            id="sqs-none",
            resource_type=ResourceType.SQS_QUEUE,
            region="us-east-1",
            original_name="test-queue",
            config={
                "name": "test-queue",
                "visibility_timeout_seconds": None,
                "message_retention_seconds": None,
                "max_message_size": None,
                "delay_seconds": None,
                "receive_wait_time_seconds": None,
            },
            tags={"Name": "test-queue"},
        )
        graph.add_resource(sqs)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            sqs_file = Path(tmpdir) / "messaging.tf"
            content = sqs_file.read_text()

            # Should NOT have literal "None"
            assert "= None" not in content
            # Should have proper numeric defaults (flexible whitespace for terraform fmt)
            import re

            assert re.search(r"visibility_timeout_seconds\s+=\s+30", content), (
                "visibility_timeout_seconds = 30 not found"
            )

    def test_lb_target_group_none_port_uses_default(self):
        """Verify LB Target Group port=None uses default."""
        graph = GraphEngine()

        tg = ResourceNode(
            id="tg-none-port",
            resource_type=ResourceType.LB_TARGET_GROUP,
            region="us-east-1",
            original_name="test-tg",
            config={
                "name": "test-tg",
                "port": None,  # Explicitly None
                "protocol": None,
                "vpc_id": "vpc-123",
                "target_type": None,
                "health_check": {
                    "enabled": None,
                    "healthy_threshold": None,
                    "unhealthy_threshold": None,
                    "timeout_seconds": None,
                    "interval_seconds": None,
                },
                "targets": [],
            },
            tags={"Name": "test-tg"},
        )
        graph.add_resource(tg)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            alb_file = Path(tmpdir) / "alb.tf"
            content = alb_file.read_text()

            # Should NOT have literal "None"
            assert "= None" not in content
            # Should have proper defaults (flexible whitespace for terraform fmt)
            import re

            assert re.search(r"port\s+=\s+80", content), "port = 80 not found"
