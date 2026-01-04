"""Tests for Terraform backend configuration generator."""

from __future__ import annotations

from pathlib import Path

import pytest

from replimap.renderers.backend import (
    BackendGenerator,
    LocalBackendConfig,
    S3BackendConfig,
)


class TestS3BackendConfig:
    """Tests for S3BackendConfig dataclass."""

    def test_basic_config(self) -> None:
        """Test basic S3 backend configuration."""
        config = S3BackendConfig(
            bucket="my-terraform-state",
            key="prod/terraform.tfstate",
            region="us-east-1",
        )

        assert config.bucket == "my-terraform-state"
        assert config.key == "prod/terraform.tfstate"
        assert config.region == "us-east-1"
        assert config.encrypt is True  # Default
        assert config.dynamodb_table is None

    def test_full_config(self) -> None:
        """Test S3 backend with all options."""
        config = S3BackendConfig(
            bucket="my-state",
            key="state.tfstate",
            region="eu-west-1",
            encrypt=True,
            dynamodb_table="terraform-locks",
            workspace_key_prefix="workspaces",
            role_arn="arn:aws:iam::123456789012:role/TerraformRole",
            profile="terraform",
        )

        assert config.dynamodb_table == "terraform-locks"
        assert config.workspace_key_prefix == "workspaces"
        assert config.role_arn == "arn:aws:iam::123456789012:role/TerraformRole"
        assert config.profile == "terraform"

    def test_validate_missing_bucket(self) -> None:
        """Test validation fails when bucket is missing."""
        config = S3BackendConfig(bucket="", key="state.tfstate")

        with pytest.raises(ValueError, match="bucket name is required"):
            config.validate()

    def test_validate_missing_key(self) -> None:
        """Test validation fails when key is missing."""
        config = S3BackendConfig(bucket="my-bucket", key="")

        with pytest.raises(ValueError, match="key.*is required"):
            config.validate()

    def test_validate_bucket_too_short(self) -> None:
        """Test validation fails when bucket name is too short."""
        config = S3BackendConfig(bucket="ab", key="state.tfstate")

        with pytest.raises(ValueError, match="between 3 and 63"):
            config.validate()

    def test_validate_bucket_too_long(self) -> None:
        """Test validation fails when bucket name is too long."""
        config = S3BackendConfig(bucket="a" * 64, key="state.tfstate")

        with pytest.raises(ValueError, match="between 3 and 63"):
            config.validate()

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        config = S3BackendConfig(
            bucket="my-bucket",
            key="state.tfstate",
            region="us-east-1",
            dynamodb_table="locks",
        )

        result = config.to_dict()

        assert result["bucket"] == "my-bucket"
        assert result["key"] == "state.tfstate"
        assert result["region"] == "us-east-1"
        assert result["encrypt"] is True
        assert result["dynamodb_table"] == "locks"


class TestLocalBackendConfig:
    """Tests for LocalBackendConfig dataclass."""

    def test_default_path(self) -> None:
        """Test default state file path."""
        config = LocalBackendConfig()
        assert config.path == "terraform.tfstate"

    def test_custom_path(self) -> None:
        """Test custom state file path."""
        config = LocalBackendConfig(path="custom.tfstate")
        assert config.path == "custom.tfstate"


class TestBackendGenerator:
    """Tests for BackendGenerator."""

    @pytest.fixture
    def generator(self) -> BackendGenerator:
        """Create a BackendGenerator instance."""
        return BackendGenerator()

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory for output."""
        output = tmp_path / "terraform"
        output.mkdir()
        return output

    def test_s3_backend_basic(
        self, generator: BackendGenerator, temp_dir: Path
    ) -> None:
        """Test basic S3 backend generation."""
        config = S3BackendConfig(
            bucket="my-terraform-state",
            key="prod/terraform.tfstate",
            region="us-east-1",
        )

        output = generator.generate_s3_backend(config, temp_dir)

        assert output.exists()
        assert output.name == "backend.tf"

        content = output.read_text()
        assert 'backend "s3"' in content
        assert 'bucket = "my-terraform-state"' in content
        assert 'key    = "prod/terraform.tfstate"' in content
        assert 'region = "us-east-1"' in content
        assert "encrypt = true" in content

    def test_s3_backend_with_dynamodb(
        self, generator: BackendGenerator, temp_dir: Path
    ) -> None:
        """Test S3 backend with DynamoDB locking."""
        config = S3BackendConfig(
            bucket="my-state",
            key="state.tfstate",
            region="us-east-1",
            dynamodb_table="terraform-locks",
        )

        output = generator.generate_s3_backend(config, temp_dir)
        content = output.read_text()

        assert 'dynamodb_table = "terraform-locks"' in content

    def test_s3_backend_with_all_options(
        self, generator: BackendGenerator, temp_dir: Path
    ) -> None:
        """Test S3 backend with all options."""
        config = S3BackendConfig(
            bucket="my-state",
            key="state.tfstate",
            region="eu-west-1",
            encrypt=True,
            dynamodb_table="locks",
            workspace_key_prefix="env",
            role_arn="arn:aws:iam::123:role/Role",
            profile="tf-admin",
        )

        output = generator.generate_s3_backend(config, temp_dir)
        content = output.read_text()

        assert 'workspace_key_prefix = "env"' in content
        assert 'role_arn = "arn:aws:iam::123:role/Role"' in content
        assert 'profile = "tf-admin"' in content

    def test_s3_backend_validation_error(
        self, generator: BackendGenerator, temp_dir: Path
    ) -> None:
        """Test S3 backend validation error."""
        config = S3BackendConfig(bucket="", key="state.tfstate")

        with pytest.raises(ValueError):
            generator.generate_s3_backend(config, temp_dir)

    def test_local_backend(
        self, generator: BackendGenerator, temp_dir: Path
    ) -> None:
        """Test local backend generation."""
        config = LocalBackendConfig(path="mystate.tfstate")

        output = generator.generate_local_backend(config, temp_dir)

        assert output.exists()
        content = output.read_text()

        assert 'backend "local"' in content
        assert 'path = "mystate.tfstate"' in content

    def test_bootstrap_generation(
        self, generator: BackendGenerator, temp_dir: Path
    ) -> None:
        """Test backend bootstrap generation."""
        config = S3BackendConfig(
            bucket="my-state",
            key="state.tfstate",
            region="us-east-1",
            dynamodb_table="terraform-locks",
        )

        output = generator.generate_backend_bootstrap(config, temp_dir)

        assert output.exists()
        assert output.parent.name == "bootstrap"

        content = output.read_text()

        # Check S3 bucket resources
        assert "aws_s3_bucket" in content
        assert "aws_s3_bucket_versioning" in content
        assert "aws_s3_bucket_server_side_encryption_configuration" in content
        assert "aws_s3_bucket_public_access_block" in content

        # Check DynamoDB table
        assert "aws_dynamodb_table" in content
        assert "terraform-locks" in content
        assert 'hash_key     = "LockID"' in content

        # Check outputs
        assert "output" in content
        assert "state_bucket_name" in content
        assert "dynamodb_table_name" in content

    def test_bootstrap_without_dynamodb(
        self, generator: BackendGenerator, temp_dir: Path
    ) -> None:
        """Test bootstrap generation without DynamoDB."""
        config = S3BackendConfig(
            bucket="my-state",
            key="state.tfstate",
            region="us-east-1",
        )

        output = generator.generate_backend_bootstrap(config, temp_dir)
        content = output.read_text()

        # Should have S3 but not DynamoDB
        assert "aws_s3_bucket" in content
        assert "aws_dynamodb_table" not in content

    def test_creates_output_dir(
        self, generator: BackendGenerator, tmp_path: Path
    ) -> None:
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "nonexistent" / "terraform"
        config = S3BackendConfig(bucket="my-bucket", key="state.tfstate")

        output = generator.generate_s3_backend(config, output_dir)

        assert output_dir.exists()
        assert output.exists()
