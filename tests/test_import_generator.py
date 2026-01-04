"""Tests for Terraform import block generator."""

from __future__ import annotations

from pathlib import Path

import pytest

from replimap.renderers.import_generator import (
    IMPORT_ID_FORMATS,
    ImportBlockGenerator,
    ImportMapping,
)


class TestImportIDFormats:
    """Tests for import ID format mappings."""

    def test_common_resource_types_have_formats(self) -> None:
        """Ensure common resource types have import ID formats defined."""
        common_types = [
            # VPC/Networking
            "aws_vpc",
            "aws_subnet",
            "aws_security_group",
            "aws_internet_gateway",
            "aws_nat_gateway",
            "aws_route_table",
            # EC2
            "aws_instance",
            "aws_ebs_volume",
            "aws_launch_template",
            "aws_autoscaling_group",
            # Load Balancing
            "aws_lb",
            "aws_lb_listener",
            "aws_lb_target_group",
            # RDS
            "aws_db_instance",
            "aws_db_subnet_group",
            # ElastiCache
            "aws_elasticache_cluster",
            "aws_elasticache_subnet_group",
            # S3
            "aws_s3_bucket",
            "aws_s3_bucket_policy",
            # IAM
            "aws_iam_role",
            "aws_iam_policy",
            "aws_iam_instance_profile",
            # Lambda
            "aws_lambda_function",
            # CloudWatch
            "aws_cloudwatch_log_group",
            # SNS/SQS
            "aws_sns_topic",
            "aws_sqs_queue",
        ]

        for resource_type in common_types:
            assert resource_type in IMPORT_ID_FORMATS, (
                f"Missing format for {resource_type}"
            )

    def test_format_placeholders(self) -> None:
        """Verify format strings use valid placeholders."""
        # Known valid placeholders (for documentation)
        # {id}, {name}, {arn}, {bucket}, {identifier}, {url},
        # {allocation_id}, {key_name}, {key_id}, {user_id},
        # {zone_id}, {user_group_id}, COMPLEX_SEE_DOCS

        for resource_type, format_str in IMPORT_ID_FORMATS.items():
            if format_str == "COMPLEX_SEE_DOCS":
                continue
            # Check that format uses known placeholders
            assert (
                format_str.startswith("{") or "/" in format_str or ":" in format_str
            ), f"Invalid format for {resource_type}: {format_str}"


class TestImportMapping:
    """Tests for ImportMapping dataclass."""

    def test_basic_mapping(self) -> None:
        """Test basic import mapping creation."""
        mapping = ImportMapping(
            terraform_address="aws_instance.web_server",
            aws_id="i-1234567890abcdef0",
            resource_type="aws_instance",
        )

        assert mapping.terraform_address == "aws_instance.web_server"
        assert mapping.aws_id == "i-1234567890abcdef0"
        assert mapping.resource_type == "aws_instance"
        assert mapping.attributes is None

    def test_mapping_with_attributes(self) -> None:
        """Test import mapping with attributes."""
        mapping = ImportMapping(
            terraform_address="aws_s3_bucket.data",
            aws_id="my-bucket",
            resource_type="aws_s3_bucket",
            attributes={"bucket": "my-bucket", "arn": "arn:aws:s3:::my-bucket"},
        )

        assert mapping.attributes is not None
        assert mapping.attributes["bucket"] == "my-bucket"


class TestImportBlockGenerator:
    """Tests for ImportBlockGenerator."""

    @pytest.fixture
    def generator(self) -> ImportBlockGenerator:
        """Create a generator instance."""
        return ImportBlockGenerator()

    def test_format_import_id_simple(self, generator: ImportBlockGenerator) -> None:
        """Test simple ID format (uses resource ID directly)."""
        mapping = ImportMapping(
            terraform_address="aws_instance.web",
            aws_id="i-1234567890abcdef0",
            resource_type="aws_instance",
        )

        import_id = generator.format_import_id(mapping)
        assert import_id == "i-1234567890abcdef0"

    def test_format_import_id_bucket(self, generator: ImportBlockGenerator) -> None:
        """Test bucket format (uses bucket name)."""
        mapping = ImportMapping(
            terraform_address="aws_s3_bucket.data",
            aws_id="123456",
            resource_type="aws_s3_bucket",
            attributes={"bucket": "my-bucket-name"},
        )

        import_id = generator.format_import_id(mapping)
        assert import_id == "my-bucket-name"

    def test_format_import_id_name(self, generator: ImportBlockGenerator) -> None:
        """Test name format (uses resource name)."""
        mapping = ImportMapping(
            terraform_address="aws_iam_role.app_role",
            aws_id="AROAXXXXXXXXX",
            resource_type="aws_iam_role",
            attributes={"name": "app-execution-role"},
        )

        import_id = generator.format_import_id(mapping)
        assert import_id == "app-execution-role"

    def test_format_import_id_arn(self, generator: ImportBlockGenerator) -> None:
        """Test ARN format (uses full ARN)."""
        mapping = ImportMapping(
            terraform_address="aws_lb.main",
            aws_id="arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-lb/abc",
            resource_type="aws_lb",
            attributes={
                "arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-lb/abc"
            },
        )

        import_id = generator.format_import_id(mapping)
        assert import_id.startswith("arn:aws:elasticloadbalancing")

    def test_format_import_id_identifier(self, generator: ImportBlockGenerator) -> None:
        """Test identifier format (RDS instances)."""
        mapping = ImportMapping(
            terraform_address="aws_db_instance.postgres",
            aws_id="db-XXXX",
            resource_type="aws_db_instance",
            attributes={"identifier": "my-postgres-db"},
        )

        import_id = generator.format_import_id(mapping)
        assert import_id == "my-postgres-db"

    def test_format_import_id_complex(self, generator: ImportBlockGenerator) -> None:
        """Test complex format returns TODO marker."""
        mapping = ImportMapping(
            terraform_address="aws_route.main",
            aws_id="r-12345",
            resource_type="aws_route",
        )

        import_id = generator.format_import_id(mapping)
        assert import_id.startswith("TODO_COMPLEX_FORMAT:")

    def test_format_import_id_allocation(self, generator: ImportBlockGenerator) -> None:
        """Test allocation_id format (EIP)."""
        mapping = ImportMapping(
            terraform_address="aws_eip.nat",
            aws_id="eipalloc-12345678",
            resource_type="aws_eip",
            attributes={"allocation_id": "eipalloc-12345678"},
        )

        import_id = generator.format_import_id(mapping)
        assert import_id == "eipalloc-12345678"

    def test_generate_import_file(
        self, generator: ImportBlockGenerator, tmp_path: Path
    ) -> None:
        """Test import file generation."""
        mappings = [
            ImportMapping(
                terraform_address="aws_vpc.main",
                aws_id="vpc-12345678",
                resource_type="aws_vpc",
            ),
            ImportMapping(
                terraform_address="aws_instance.web",
                aws_id="i-abcdef1234567890",
                resource_type="aws_instance",
            ),
            ImportMapping(
                terraform_address="aws_s3_bucket.data",
                aws_id="123",
                resource_type="aws_s3_bucket",
                attributes={"bucket": "my-data-bucket"},
            ),
        ]

        output_file = tmp_path / "imports.tf"
        generator.generate_import_file(mappings, output_file)

        assert output_file.exists()
        content = output_file.read_text()

        # Check header
        assert "Auto-generated by RepliMap" in content
        assert "Terraform 1.5+" in content

        # Check import blocks
        assert "import {" in content
        assert "to = aws_vpc.main" in content
        assert 'id = "vpc-12345678"' in content
        assert "to = aws_instance.web" in content
        assert 'id = "i-abcdef1234567890"' in content
        assert "to = aws_s3_bucket.data" in content
        assert 'id = "my-data-bucket"' in content

    def test_generate_import_file_empty(
        self, generator: ImportBlockGenerator, tmp_path: Path
    ) -> None:
        """Test that empty mapping list doesn't create file."""
        output_file = tmp_path / "imports.tf"
        generator.generate_import_file([], output_file)

        assert not output_file.exists()

    def test_generate_import_file_with_complex(
        self, generator: ImportBlockGenerator, tmp_path: Path
    ) -> None:
        """Test that complex resources are commented out."""
        mappings = [
            ImportMapping(
                terraform_address="aws_security_group_rule.allow_http",
                aws_id="sgr-12345",
                resource_type="aws_security_group_rule",
            ),
        ]

        output_file = tmp_path / "imports.tf"
        generator.generate_import_file(mappings, output_file)

        content = output_file.read_text()

        # Complex imports should be commented out
        assert "# WARNING: Complex import format" in content
        assert "# import {" in content
        assert "ATTENTION:" in content

    def test_generate_import_commands(self, generator: ImportBlockGenerator) -> None:
        """Test legacy import command generation."""
        mappings = [
            ImportMapping(
                terraform_address="aws_vpc.main",
                aws_id="vpc-12345678",
                resource_type="aws_vpc",
            ),
            ImportMapping(
                terraform_address="aws_instance.web",
                aws_id="i-abcdef1234567890",
                resource_type="aws_instance",
            ),
        ]

        commands = generator.generate_import_commands(mappings)

        # Check script header
        assert "#!/bin/bash" in commands[0]
        assert "RepliMap Import Script" in "\n".join(commands)

        # Check import commands
        commands_str = "\n".join(commands)
        assert "terraform import aws_vpc.main 'vpc-12345678'" in commands_str
        assert "terraform import aws_instance.web 'i-abcdef1234567890'" in commands_str

    def test_generate_import_script(
        self, generator: ImportBlockGenerator, tmp_path: Path
    ) -> None:
        """Test import script file generation."""
        mappings = [
            ImportMapping(
                terraform_address="aws_vpc.main",
                aws_id="vpc-12345678",
                resource_type="aws_vpc",
            ),
        ]

        output_file = tmp_path / "import.sh"
        generator.generate_import_script(mappings, output_file)

        assert output_file.exists()

        # Check file is executable
        import os

        assert os.access(output_file, os.X_OK)

        content = output_file.read_text()
        assert "terraform import" in content

    def test_extract_name_from_arn(self, generator: ImportBlockGenerator) -> None:
        """Test ARN name extraction."""
        # Role ARN
        role_arn = "arn:aws:iam::123456789012:role/my-role-name"
        name = generator._extract_name_from_id(role_arn)
        assert name == "my-role-name"

        # Simple ID (not ARN)
        simple_id = "vpc-12345678"
        name = generator._extract_name_from_id(simple_id)
        assert name == "vpc-12345678"


class TestImportIDResolution:
    """Tests for import ID resolution logic."""

    @pytest.fixture
    def generator(self) -> ImportBlockGenerator:
        return ImportBlockGenerator()

    def test_url_format(self, generator: ImportBlockGenerator) -> None:
        """Test SQS queue URL format."""
        mapping = ImportMapping(
            terraform_address="aws_sqs_queue.events",
            aws_id="sqs-123",
            resource_type="aws_sqs_queue",
            attributes={
                "url": "https://sqs.us-east-1.amazonaws.com/123456789012/events-queue"
            },
        )

        import_id = generator.format_import_id(mapping)
        assert "amazonaws.com" in import_id

    def test_fallback_to_id(self, generator: ImportBlockGenerator) -> None:
        """Test fallback to AWS ID when attributes missing."""
        mapping = ImportMapping(
            terraform_address="aws_s3_bucket.data",
            aws_id="my-bucket-id",
            resource_type="aws_s3_bucket",
            # No attributes - should fall back to aws_id
        )

        import_id = generator.format_import_id(mapping)
        assert import_id == "my-bucket-id"

    def test_unknown_resource_type(self, generator: ImportBlockGenerator) -> None:
        """Test handling of unknown resource types."""
        mapping = ImportMapping(
            terraform_address="aws_unknown_resource.test",
            aws_id="unknown-123",
            resource_type="aws_unknown_resource",
        )

        # Should fall back to using the ID
        import_id = generator.format_import_id(mapping)
        assert import_id == "unknown-123"
