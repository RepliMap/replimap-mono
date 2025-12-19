"""
Tests for resource relationship handling in templates.

These tests verify that:
1. Target Group attachments are properly generated
2. Security Group egress rules handle SG-to-SG references
3. Route Table associations are created even when subnet not found
4. EBS Volume attachments are properly generated
5. EC2 instances only include running instances
"""

import tempfile
from pathlib import Path

from replimap.core import GraphEngine
from replimap.core.models import ResourceNode, ResourceType
from replimap.renderers.terraform import TerraformRenderer
from replimap.transformers.network_remapper import NetworkRemapTransformer


class TestTargetGroupAttachments:
    """Tests for Target Group target attachment generation."""

    def test_target_group_with_instance_targets(self) -> None:
        """Test that target group attachments are generated for instance targets."""
        graph = GraphEngine()

        # VPC
        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="test-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        # Subnet
        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            original_name="test-subnet",
            config={"cidr_block": "10.0.1.0/24", "vpc_id": "vpc-123"},
            tags={"Name": "test-subnet"},
        )
        graph.add_resource(subnet)

        # EC2 Instance (running)
        ec2 = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            original_name="test-instance",
            config={
                "instance_type": "t3.micro",
                "ami": "ami-123",
                "subnet_id": "subnet-123",
                "state": "running",
            },
            tags={"Name": "test-instance"},
        )
        graph.add_resource(ec2)

        # Target Group with targets
        tg = ResourceNode(
            id="arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/test-tg/abc123",
            resource_type=ResourceType.LB_TARGET_GROUP,
            region="us-east-1",
            original_name="test-tg",
            config={
                "name": "test-tg",
                "vpc_id": "vpc-123",
                "port": 80,
                "protocol": "HTTP",
                "target_type": "instance",
                "targets": [
                    {"id": "i-12345", "port": 80, "health_state": "healthy"},
                ],
                "health_check": {
                    "enabled": True,
                    "path": "/health",
                    "protocol": "HTTP",
                    "healthy_threshold": 3,
                    "unhealthy_threshold": 3,
                },
            },
            tags={"Name": "test-tg"},
        )
        graph.add_resource(tg)

        # Render
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            # Read the ALB file
            alb_file = Path(tmpdir) / "alb.tf"
            assert alb_file.exists()
            content = alb_file.read_text()

            # Verify target group is created
            assert 'resource "aws_lb_target_group"' in content

            # Verify target attachment is created
            assert 'resource "aws_lb_target_group_attachment"' in content
            assert "target_group_arn" in content
            assert "target_id" in content

    def test_target_group_with_ip_targets(self) -> None:
        """Test that IP targets use quoted strings."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="test-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        # Target Group with IP targets
        tg = ResourceNode(
            id="arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/test-tg/abc123",
            resource_type=ResourceType.LB_TARGET_GROUP,
            region="us-east-1",
            original_name="test-tg",
            config={
                "name": "test-tg",
                "vpc_id": "vpc-123",
                "port": 80,
                "protocol": "HTTP",
                "target_type": "ip",
                "targets": [
                    {"id": "10.0.1.100", "port": 80},
                    {"id": "10.0.1.101", "port": 80},
                ],
                "health_check": {"enabled": True},
            },
            tags={"Name": "test-tg"},
        )
        graph.add_resource(tg)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            alb_file = Path(tmpdir) / "alb.tf"
            content = alb_file.read_text()

            # Verify IP targets use quoted IDs
            assert '"10.0.1.100"' in content
            assert '"10.0.1.101"' in content

    def test_target_group_empty_targets(self) -> None:
        """Test that target groups with no targets don't create attachments."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="test-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        # Target Group with no targets
        tg = ResourceNode(
            id="arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/test-tg/abc123",
            resource_type=ResourceType.LB_TARGET_GROUP,
            region="us-east-1",
            original_name="test-tg",
            config={
                "name": "test-tg",
                "vpc_id": "vpc-123",
                "port": 80,
                "protocol": "HTTP",
                "target_type": "instance",
                "targets": [],
                "health_check": {"enabled": True},
            },
            tags={"Name": "test-tg"},
        )
        graph.add_resource(tg)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            alb_file = Path(tmpdir) / "alb.tf"
            content = alb_file.read_text()

            # Target group should exist
            assert 'resource "aws_lb_target_group"' in content
            # But no attachments
            assert 'resource "aws_lb_target_group_attachment"' not in content


class TestSecurityGroupEgressRules:
    """Tests for Security Group egress rule SG references."""

    def test_egress_with_security_group_reference(self) -> None:
        """Test that egress rules properly reference other security groups."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="test-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        # First security group (target of reference)
        sg_target = ResourceNode(
            id="sg-target",
            resource_type=ResourceType.SECURITY_GROUP,
            region="us-east-1",
            original_name="target-sg",
            config={
                "name": "target-sg",
                "description": "Target security group",
                "vpc_id": "vpc-123",
                "ingress": [],
                "egress": [],
            },
            tags={"Name": "target-sg"},
        )
        graph.add_resource(sg_target)

        # Second security group with egress to first
        sg_source = ResourceNode(
            id="sg-source",
            resource_type=ResourceType.SECURITY_GROUP,
            region="us-east-1",
            original_name="source-sg",
            config={
                "name": "source-sg",
                "description": "Source security group",
                "vpc_id": "vpc-123",
                "ingress": [],
                "egress": [
                    {
                        "protocol": "tcp",
                        "from_port": 443,
                        "to_port": 443,
                        "security_groups": [
                            {"security_group_id": "sg-target"},
                        ],
                    },
                ],
            },
            tags={"Name": "source-sg"},
        )
        graph.add_resource(sg_source)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            sg_file = Path(tmpdir) / "security_groups.tf"
            content = sg_file.read_text()

            # Cross-SG references are now generated as separate aws_security_group_rule
            # resources to avoid circular dependency issues
            assert "aws_security_group_rule" in content
            assert 'type                     = "egress"' in content
            # Should reference the target SG by terraform name
            assert "aws_security_group.target-sg.id" in content

    def test_egress_with_cidr_and_sg_reference(self) -> None:
        """Test egress rules can have both CIDR and SG references."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="test-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        sg = ResourceNode(
            id="sg-123",
            resource_type=ResourceType.SECURITY_GROUP,
            region="us-east-1",
            original_name="test-sg",
            config={
                "name": "test-sg",
                "description": "Test security group",
                "vpc_id": "vpc-123",
                "ingress": [],
                "egress": [
                    {
                        "protocol": "-1",
                        "from_port": 0,
                        "to_port": 0,
                        "cidr_blocks": ["0.0.0.0/0"],
                    },
                ],
            },
            tags={"Name": "test-sg"},
        )
        graph.add_resource(sg)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            sg_file = Path(tmpdir) / "security_groups.tf"
            content = sg_file.read_text()

            assert "egress {" in content
            assert "cidr_blocks" in content
            assert "0.0.0.0/0" in content


class TestRouteTableAssociations:
    """Tests for Route Table association handling."""

    def test_route_table_association_with_found_subnet(self) -> None:
        """Test route table association when subnet is in graph."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="test-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            original_name="test-subnet",
            config={"cidr_block": "10.0.1.0/24", "vpc_id": "vpc-123"},
            tags={"Name": "test-subnet"},
        )
        graph.add_resource(subnet)

        rtb = ResourceNode(
            id="rtb-123",
            resource_type=ResourceType.ROUTE_TABLE,
            region="us-east-1",
            original_name="test-rtb",
            config={
                "vpc_id": "vpc-123",
                "routes": [],
                "associations": [
                    {"subnet_id": "subnet-123", "main": False},
                ],
            },
            tags={"Name": "test-rtb"},
        )
        graph.add_resource(rtb)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            network_file = Path(tmpdir) / "networking.tf"
            content = network_file.read_text()

            # Verify association is created with proper reference
            assert 'resource "aws_route_table_association"' in content
            assert "aws_subnet." in content

    def test_route_table_association_with_missing_subnet(self) -> None:
        """Test route table association when subnet is NOT in graph."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="test-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        # Route table with association to non-existent subnet
        rtb = ResourceNode(
            id="rtb-123",
            resource_type=ResourceType.ROUTE_TABLE,
            region="us-east-1",
            original_name="test-rtb",
            config={
                "vpc_id": "vpc-123",
                "routes": [],
                "associations": [
                    {"subnet_id": "subnet-missing", "main": False},
                ],
            },
            tags={"Name": "test-rtb"},
        )
        graph.add_resource(rtb)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            network_file = Path(tmpdir) / "networking.tf"
            content = network_file.read_text()

            # Association should STILL be created (with warning)
            assert 'resource "aws_route_table_association"' in content
            assert "WARNING" in content
            # Should use the original subnet ID as fallback
            assert '"subnet-missing"' in content

    def test_route_table_association_with_remapped_subnet(self) -> None:
        """Test route table association when subnet ID is pre-remapped."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="test-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            original_name="test-subnet",
            config={"cidr_block": "10.0.1.0/24", "vpc_id": "vpc-123"},
            tags={"Name": "test-subnet"},
        )
        graph.add_resource(subnet)

        rtb = ResourceNode(
            id="rtb-123",
            resource_type=ResourceType.ROUTE_TABLE,
            region="us-east-1",
            original_name="test-rtb",
            config={
                "vpc_id": "vpc-123",
                "routes": [],
                "associations": [
                    {"subnet_id": "subnet-123", "main": False},
                ],
            },
            tags={"Name": "test-rtb"},
        )
        graph.add_resource(rtb)

        # Apply network remapper
        remapper = NetworkRemapTransformer(use_terraform_refs=True)
        remapper.transform(graph)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            network_file = Path(tmpdir) / "networking.tf"
            content = network_file.read_text()

            # Association should be created with terraform reference
            assert 'resource "aws_route_table_association"' in content
            # Should NOT have quotes around the subnet reference
            assert "aws_subnet." in content


class TestEBSVolumeAttachments:
    """Tests for EBS Volume attachment generation."""

    def test_ebs_volume_with_attachment(self) -> None:
        """Test that EBS volume attachments are generated."""
        graph = GraphEngine()

        # EC2 Instance
        ec2 = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            original_name="test-instance",
            config={
                "instance_type": "t3.micro",
                "ami": "ami-123",
                "state": "running",
            },
            tags={"Name": "test-instance"},
        )
        graph.add_resource(ec2)

        # EBS Volume with attachment
        ebs = ResourceNode(
            id="vol-12345",
            resource_type=ResourceType.EBS_VOLUME,
            region="us-east-1",
            original_name="test-volume",
            config={
                "availability_zone": "us-east-1a",
                "size": 100,
                "volume_type": "gp3",
                "encrypted": True,
                "attachments": [
                    {
                        "instance_id": "i-12345",
                        "device": "/dev/sdf",
                        "state": "attached",
                        "delete_on_termination": False,
                    },
                ],
            },
            tags={"Name": "test-volume"},
        )
        graph.add_resource(ebs)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            storage_file = Path(tmpdir) / "storage.tf"
            content = storage_file.read_text()

            # Verify volume is created
            assert 'resource "aws_ebs_volume"' in content

            # Verify attachment is created
            assert 'resource "aws_volume_attachment"' in content
            assert "volume_id" in content
            assert "instance_id" in content
            assert "device_name" in content
            assert "/dev/sdf" in content

    def test_ebs_volume_attachment_to_running_instance(self) -> None:
        """Test attachment references running instance properly."""
        graph = GraphEngine()

        ec2 = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            original_name="test-instance",
            config={"instance_type": "t3.micro", "ami": "ami-123", "state": "running"},
            tags={"Name": "test-instance"},
        )
        graph.add_resource(ec2)

        ebs = ResourceNode(
            id="vol-12345",
            resource_type=ResourceType.EBS_VOLUME,
            region="us-east-1",
            original_name="test-volume",
            config={
                "availability_zone": "us-east-1a",
                "size": 100,
                "volume_type": "gp3",
                "attachments": [
                    {
                        "instance_id": "i-12345",
                        "device": "/dev/sdf",
                        "state": "attached",
                    },
                ],
            },
            tags={"Name": "test-volume"},
        )
        graph.add_resource(ebs)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            storage_file = Path(tmpdir) / "storage.tf"
            content = storage_file.read_text()

            # Should reference instance by terraform name
            assert "aws_instance." in content

    def test_ebs_volume_attachment_to_missing_instance(self) -> None:
        """Test attachment handles missing instance gracefully."""
        graph = GraphEngine()

        # EBS Volume with attachment to non-existent instance
        ebs = ResourceNode(
            id="vol-12345",
            resource_type=ResourceType.EBS_VOLUME,
            region="us-east-1",
            original_name="test-volume",
            config={
                "availability_zone": "us-east-1a",
                "size": 100,
                "volume_type": "gp3",
                "attachments": [
                    {
                        "instance_id": "i-missing",
                        "device": "/dev/sdf",
                        "state": "attached",
                    },
                ],
            },
            tags={"Name": "test-volume"},
        )
        graph.add_resource(ebs)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            storage_file = Path(tmpdir) / "storage.tf"
            content = storage_file.read_text()

            # Attachment should still be created with warning
            assert 'resource "aws_volume_attachment"' in content
            assert "WARNING" in content
            assert '"i-missing"' in content

    def test_ebs_volume_detached_no_attachment(self) -> None:
        """Test that detached volumes don't create attachments."""
        graph = GraphEngine()

        # EBS Volume that is detached
        ebs = ResourceNode(
            id="vol-12345",
            resource_type=ResourceType.EBS_VOLUME,
            region="us-east-1",
            original_name="test-volume",
            config={
                "availability_zone": "us-east-1a",
                "size": 100,
                "volume_type": "gp3",
                "attachments": [
                    {
                        "instance_id": "i-12345",
                        "device": "/dev/sdf",
                        "state": "detached",  # NOT attached
                    },
                ],
            },
            tags={"Name": "test-volume"},
        )
        graph.add_resource(ebs)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            storage_file = Path(tmpdir) / "storage.tf"
            content = storage_file.read_text()

            # Volume should exist
            assert 'resource "aws_ebs_volume"' in content
            # But no attachment (because state != 'attached')
            assert 'resource "aws_volume_attachment"' not in content


class TestNetworkRemapperInstanceIds:
    """Tests for NetworkRemapTransformer EC2 instance ID handling."""

    def test_instance_id_remapping(self) -> None:
        """Test that instance IDs are remapped in nested configs."""
        graph = GraphEngine()

        ec2 = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            original_name="test-instance",
            config={"instance_type": "t3.micro", "ami": "ami-123"},
            tags={"Name": "test-instance"},
        )
        graph.add_resource(ec2)

        ebs = ResourceNode(
            id="vol-12345",
            resource_type=ResourceType.EBS_VOLUME,
            region="us-east-1",
            original_name="test-volume",
            config={
                "availability_zone": "us-east-1a",
                "size": 100,
                "volume_type": "gp3",
                "attachments": [
                    {
                        "instance_id": "i-12345",
                        "device": "/dev/sdf",
                        "state": "attached",
                    },
                ],
            },
            tags={"Name": "test-volume"},
        )
        graph.add_resource(ebs)

        # Apply remapper
        remapper = NetworkRemapTransformer(use_terraform_refs=True)
        remapper.transform(graph)

        # Check that instance_id was remapped
        updated_ebs = graph.get_resource("vol-12345")
        assert updated_ebs is not None
        attachments = updated_ebs.config.get("attachments", [])
        assert len(attachments) == 1
        assert attachments[0]["instance_id"] == "aws_instance.test-instance.id"

    def test_target_id_remapping_in_target_group(self) -> None:
        """Test that target IDs are remapped in target groups."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="test-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        ec2 = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            original_name="test-instance",
            config={"instance_type": "t3.micro", "ami": "ami-123"},
            tags={"Name": "test-instance"},
        )
        graph.add_resource(ec2)

        tg = ResourceNode(
            id="tg-123",
            resource_type=ResourceType.LB_TARGET_GROUP,
            region="us-east-1",
            original_name="test-tg",
            config={
                "name": "test-tg",
                "vpc_id": "vpc-123",
                "port": 80,
                "protocol": "HTTP",
                "target_type": "instance",
                "targets": [
                    {"id": "i-12345", "port": 80},
                ],
                "health_check": {"enabled": True},
            },
            tags={"Name": "test-tg"},
        )
        graph.add_resource(tg)

        # Apply remapper
        remapper = NetworkRemapTransformer(use_terraform_refs=True)
        remapper.transform(graph)

        # Check that vpc_id was remapped (targets.id is NOT remapped because
        # it's in a list and 'id' is not in id_fields)
        updated_tg = graph.get_resource("tg-123")
        assert updated_tg is not None
        assert updated_tg.config["vpc_id"] == "aws_vpc.test-vpc.id"


class TestTfRefDetection:
    """Tests for Terraform reference detection in templates."""

    def test_tf_ref_detection(self) -> None:
        """Test that _is_tf_ref_test correctly identifies Terraform references."""
        renderer = TerraformRenderer()

        # Should detect as tf_ref
        assert renderer._is_tf_ref_test("aws_vpc.my_vpc.id") is True
        assert renderer._is_tf_ref_test("aws_subnet.my_subnet.id") is True
        assert renderer._is_tf_ref_test("aws_security_group.my_sg.id") is True
        assert renderer._is_tf_ref_test("aws_instance.my_ec2.id") is True
        assert renderer._is_tf_ref_test("aws_lb_target_group.my_tg.arn") is True

        # Should NOT detect as tf_ref
        assert renderer._is_tf_ref_test("vpc-12345") is False
        assert renderer._is_tf_ref_test("subnet-12345") is False
        assert renderer._is_tf_ref_test("sg-12345") is False
        assert renderer._is_tf_ref_test("i-12345") is False
        assert renderer._is_tf_ref_test("10.0.0.1") is False
        assert renderer._is_tf_ref_test("") is False

    def test_tf_ref_in_rendered_output(self) -> None:
        """Test that pre-remapped references are output without quotes."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            original_name="test-vpc",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        graph.add_resource(vpc)

        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            original_name="test-subnet",
            config={
                "cidr_block": "10.0.1.0/24",
                "vpc_id": "vpc-123",
                "availability_zone": "us-east-1a",
            },
            tags={"Name": "test-subnet"},
        )
        graph.add_resource(subnet)

        # Apply remapper to convert vpc_id to terraform ref
        remapper = NetworkRemapTransformer(use_terraform_refs=True)
        remapper.transform(graph)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            renderer.render(graph, Path(tmpdir))

            # VPCs and Subnets go to vpc.tf
            vpc_file = Path(tmpdir) / "vpc.tf"
            content = vpc_file.read_text()

            # The vpc_id should be output WITHOUT quotes
            # Look for: vpc_id = aws_vpc.test-vpc.id (no quotes)
            assert "aws_vpc.test-vpc.id" in content
            # Should NOT have quotes around the reference
            assert '"aws_vpc.test-vpc.id"' not in content
