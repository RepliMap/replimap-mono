"""
Tests for the Audit Remediation Generator.

These tests verify that:
1. Remediation models work correctly
2. Templates generate valid Terraform code
3. Generator produces correct remediation plans
4. CLI integration works
"""

import tempfile
from pathlib import Path

from replimap.audit.checkov_runner import CheckovFinding
from replimap.audit.remediation import (
    RemediationFile,
    RemediationGenerator,
    RemediationPlan,
    RemediationSeverity,
    RemediationType,
)
from replimap.audit.remediation.templates import (
    generate_kms_rotation,
    generate_rds_encryption,
    generate_s3_encryption,
    generate_s3_public_access_block,
    generate_s3_versioning,
    generate_security_group_restrict,
)

# =============================================================================
# MODEL TESTS
# =============================================================================


class TestRemediationFile:
    """Test RemediationFile model."""

    def test_create_basic_file(self):
        """Test creating a basic remediation file."""
        file = RemediationFile(
            path=Path("s3/bucket_encryption.tf"),
            content="# Test content",
            description="Enable S3 encryption",
        )

        assert file.path == Path("s3/bucket_encryption.tf")
        assert file.content == "# Test content"
        assert file.description == "Enable S3 encryption"
        assert file.remediation_type == RemediationType.OTHER
        assert file.severity == RemediationSeverity.MEDIUM

    def test_file_with_all_attributes(self):
        """Test creating a file with all attributes."""
        file = RemediationFile(
            path=Path("s3/bucket_encryption.tf"),
            content="resource ...",
            description="Enable S3 encryption",
            check_ids=["CKV_AWS_19"],
            remediation_type=RemediationType.S3_ENCRYPTION,
            severity=RemediationSeverity.HIGH,
            resource_ids=["aws_s3_bucket.my_bucket"],
            requires_import=True,
            import_commands=["terraform import aws_s3_bucket.my_bucket my-bucket"],
        )

        assert file.check_ids == ["CKV_AWS_19"]
        assert file.remediation_type == RemediationType.S3_ENCRYPTION
        assert file.severity == RemediationSeverity.HIGH
        assert file.requires_import is True
        assert len(file.import_commands) == 1

    def test_file_write(self):
        """Test writing a remediation file to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            file = RemediationFile(
                path=Path("s3/bucket_encryption.tf"),
                content="# S3 encryption config",
                description="Enable S3 encryption",
            )

            written_path = file.write(base_dir)

            assert written_path.exists()
            assert written_path.read_text() == "# S3 encryption config"


class TestRemediationPlan:
    """Test RemediationPlan model."""

    def test_empty_plan(self):
        """Test creating an empty plan."""
        plan = RemediationPlan()

        assert len(plan.files) == 0
        assert plan.total_findings == 0
        assert plan.coverage_percent == 100.0
        assert plan.has_critical is False
        assert plan.has_imports is False

    def test_plan_with_files(self):
        """Test creating a plan with files."""
        plan = RemediationPlan(
            total_findings=10,
            remediable_findings=8,
            skipped_findings=2,
            files=[
                RemediationFile(
                    path=Path("s3/bucket.tf"),
                    content="# content",
                    description="Fix S3",
                    severity=RemediationSeverity.CRITICAL,
                ),
                RemediationFile(
                    path=Path("rds/db.tf"),
                    content="# content",
                    description="Fix RDS",
                    severity=RemediationSeverity.HIGH,
                    requires_import=True,
                ),
            ],
        )

        assert plan.coverage_percent == 80.0
        assert plan.has_critical is True
        assert plan.has_imports is True

    def test_files_by_severity(self):
        """Test grouping files by severity."""
        plan = RemediationPlan(
            files=[
                RemediationFile(
                    path=Path("a.tf"),
                    content="",
                    description="A",
                    severity=RemediationSeverity.CRITICAL,
                ),
                RemediationFile(
                    path=Path("b.tf"),
                    content="",
                    description="B",
                    severity=RemediationSeverity.HIGH,
                ),
                RemediationFile(
                    path=Path("c.tf"),
                    content="",
                    description="C",
                    severity=RemediationSeverity.HIGH,
                ),
            ]
        )

        by_severity = plan.files_by_severity()

        assert len(by_severity[RemediationSeverity.CRITICAL]) == 1
        assert len(by_severity[RemediationSeverity.HIGH]) == 2
        assert len(by_severity[RemediationSeverity.MEDIUM]) == 0
        assert len(by_severity[RemediationSeverity.LOW]) == 0

    def test_files_by_type(self):
        """Test grouping files by type."""
        plan = RemediationPlan(
            files=[
                RemediationFile(
                    path=Path("a.tf"),
                    content="",
                    description="A",
                    remediation_type=RemediationType.S3_ENCRYPTION,
                ),
                RemediationFile(
                    path=Path("b.tf"),
                    content="",
                    description="B",
                    remediation_type=RemediationType.S3_VERSIONING,
                ),
                RemediationFile(
                    path=Path("c.tf"),
                    content="",
                    description="C",
                    remediation_type=RemediationType.S3_ENCRYPTION,
                ),
            ]
        )

        by_type = plan.files_by_type()

        assert len(by_type[RemediationType.S3_ENCRYPTION]) == 2
        assert len(by_type[RemediationType.S3_VERSIONING]) == 1

    def test_write_all(self):
        """Test writing all files in plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            plan = RemediationPlan(
                files=[
                    RemediationFile(
                        path=Path("s3/bucket.tf"),
                        content="# S3 content",
                        description="S3 fix",
                    ),
                    RemediationFile(
                        path=Path("rds/db.tf"),
                        content="# RDS content",
                        description="RDS fix",
                    ),
                ],
                readme_content="# README",
                import_script="#!/bin/bash\necho test",
            )

            paths = plan.write_all(base_dir)

            assert len(paths) == 4  # 2 files + README + import script
            assert (base_dir / "s3/bucket.tf").exists()
            assert (base_dir / "rds/db.tf").exists()
            assert (base_dir / "README.md").exists()
            assert (base_dir / "import.sh").exists()

    def test_summary(self):
        """Test plan summary generation."""
        plan = RemediationPlan(
            total_findings=10,
            remediable_findings=8,
            skipped_findings=2,
            files=[
                RemediationFile(
                    path=Path("a.tf"),
                    content="",
                    description="A",
                    severity=RemediationSeverity.HIGH,
                )
            ],
            warnings=["Test warning"],
        )

        summary = plan.summary()

        assert "Total findings analyzed: 10" in summary
        assert "Remediable findings: 8 (80.0%)" in summary
        assert "HIGH: 1 fixes" in summary
        assert "Test warning" in summary


# =============================================================================
# TEMPLATE TESTS
# =============================================================================


class TestS3Templates:
    """Test S3 remediation templates."""

    def test_s3_encryption_aes256(self):
        """Test S3 encryption template with AES256."""
        content = generate_s3_encryption("my-bucket", "aws_s3_bucket.my_bucket")

        assert "my-bucket" in content
        assert "AES256" in content
        assert "CKV_AWS_19" in content
        assert "terraform import" in content

    def test_s3_encryption_kms(self):
        """Test S3 encryption template with KMS."""
        content = generate_s3_encryption(
            "my-bucket", "aws_s3_bucket.my_bucket", use_kms=True
        )

        assert "my-bucket" in content
        assert "aws:kms" in content
        assert "CKV_AWS_145" in content

    def test_s3_versioning(self):
        """Test S3 versioning template."""
        content = generate_s3_versioning("my-bucket", "aws_s3_bucket.my_bucket")

        assert "my-bucket" in content
        assert "Enabled" in content
        assert "CKV_AWS_18" in content

    def test_s3_public_access_block(self):
        """Test S3 public access block template."""
        content = generate_s3_public_access_block(
            "my-bucket", "aws_s3_bucket.my_bucket"
        )

        assert "my-bucket" in content
        assert "block_public_acls" in content
        assert "block_public_policy" in content
        assert "CKV_AWS_53" in content


class TestSecurityGroupTemplates:
    """Test Security Group remediation templates."""

    def test_sg_ssh_restriction(self):
        """Test SSH restriction template."""
        content = generate_security_group_restrict(
            "sg-123456", "aws_security_group.my_sg", port=22
        )

        assert "sg-123456" in content
        assert "22" in content
        assert "CKV_AWS_24" in content
        assert "10.0.0.0/8" in content

    def test_sg_rdp_restriction(self):
        """Test RDP restriction template."""
        content = generate_security_group_restrict(
            "sg-123456", "aws_security_group.my_sg", port=3389
        )

        assert "3389" in content
        assert "CKV_AWS_25" in content

    def test_sg_custom_cidrs(self):
        """Test custom CIDR blocks."""
        content = generate_security_group_restrict(
            "sg-123456",
            "aws_security_group.my_sg",
            allowed_cidrs=["192.168.1.0/24", "10.1.0.0/16"],
        )

        assert "192.168.1.0/24" in content
        assert "10.1.0.0/16" in content


class TestRDSTemplates:
    """Test RDS remediation templates."""

    def test_rds_encryption(self):
        """Test RDS encryption template."""
        content = generate_rds_encryption("my-db", "aws_db_instance.my_db")

        assert "my-db" in content
        assert "storage_encrypted = true" in content
        assert "CKV_AWS_16" in content

    def test_rds_multi_az(self):
        """Test RDS Multi-AZ template."""
        from replimap.audit.remediation.templates import generate_rds_multi_az

        content = generate_rds_multi_az("my-db", "aws_db_instance.my_db")

        assert "multi_az = true" in content
        assert "CKV_AWS_157" in content


class TestKMSTemplates:
    """Test KMS remediation templates."""

    def test_kms_rotation(self):
        """Test KMS rotation template."""
        content = generate_kms_rotation("key-123", "aws_kms_key.my_key")

        assert "key-123" in content
        assert "enable_key_rotation = true" in content
        assert "CKV_AWS_7" in content

    def test_kms_policy(self):
        """Test KMS policy template."""
        from replimap.audit.remediation.templates import generate_kms_policy

        content = generate_kms_policy(
            "key-123", "aws_kms_key.my_key", account_id="123456789012"
        )

        assert "key-123" in content
        assert "123456789012" in content
        assert "CKV_AWS_33" in content


# =============================================================================
# GENERATOR TESTS
# =============================================================================


def create_mock_finding(
    check_id: str,
    resource: str = "aws_s3_bucket.test",
    check_name: str = "Test check",
    file_path: str = "/path/to/file.tf",
) -> CheckovFinding:
    """Create a mock CheckovFinding for testing."""
    return CheckovFinding(
        check_id=check_id,
        check_name=check_name,
        severity="HIGH",
        resource=resource,
        file_path=file_path,
        file_line_range=(1, 10),
    )


class TestRemediationGenerator:
    """Test RemediationGenerator class."""

    def test_generate_s3_encryption(self):
        """Test generating S3 encryption remediation."""
        findings = [
            create_mock_finding("CKV_AWS_19", "aws_s3_bucket.my_bucket"),
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        assert plan.remediable_findings == 1
        # 1 remediation file + 1 imports.tf (Terraform 1.5+ import blocks)
        assert len(plan.files) == 2
        remediation_files = [f for f in plan.files if f.path.name != "imports.tf"]
        assert len(remediation_files) == 1
        assert remediation_files[0].remediation_type == RemediationType.S3_ENCRYPTION

    def test_generate_multiple_findings(self):
        """Test generating remediation for multiple findings."""
        findings = [
            create_mock_finding("CKV_AWS_19", "aws_s3_bucket.bucket1"),
            create_mock_finding("CKV_AWS_18", "aws_s3_bucket.bucket2"),
            create_mock_finding("CKV_AWS_16", "aws_db_instance.my_db"),
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        assert plan.remediable_findings == 3
        # 3 remediation files + 1 imports.tf (Terraform 1.5+ import blocks)
        assert len(plan.files) == 4
        remediation_files = [f for f in plan.files if f.path.name != "imports.tf"]
        assert len(remediation_files) == 3

    def test_skip_unsupported_check(self):
        """Test that unsupported checks are skipped."""
        findings = [
            create_mock_finding("CKV_UNSUPPORTED_999", "some_resource"),
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        assert plan.remediable_findings == 0
        assert plan.skipped_findings == 1
        assert len(plan.files) == 0

    def test_deduplicate_findings(self):
        """Test that duplicate findings are deduplicated."""
        findings = [
            create_mock_finding("CKV_AWS_19", "aws_s3_bucket.bucket1"),
            create_mock_finding("CKV_AWS_19", "aws_s3_bucket.bucket1"),  # Duplicate
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        assert plan.remediable_findings == 1
        # 1 remediation file + 1 imports.tf (Terraform 1.5+ import blocks)
        assert len(plan.files) == 2
        remediation_files = [f for f in plan.files if f.path.name != "imports.tf"]
        assert len(remediation_files) == 1

    def test_generate_import_script(self):
        """Test import script generation."""
        findings = [
            create_mock_finding("CKV_AWS_19", "aws_s3_bucket.bucket1"),
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        assert plan.import_script
        assert "#!/bin/bash" in plan.import_script
        assert "terraform import" in plan.import_script

    def test_generate_readme(self):
        """Test README generation."""
        findings = [
            create_mock_finding("CKV_AWS_19", "aws_s3_bucket.bucket1"),
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        assert plan.readme_content
        assert "RepliMap Security Remediation" in plan.readme_content
        assert "How to Apply" in plan.readme_content

    def test_security_group_findings(self):
        """Test security group remediation."""
        findings = [
            create_mock_finding("CKV_AWS_24", "aws_security_group.web_sg"),
            create_mock_finding("CKV_AWS_25", "aws_security_group.rdp_sg"),
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        assert plan.remediable_findings == 2
        # Filter out the imports.tf file added for Terraform 1.5+ import blocks
        remediation_files = [f for f in plan.files if f.path.name != "imports.tf"]
        assert all(
            f.remediation_type == RemediationType.SECURITY_GROUP
            for f in remediation_files
        )

    def test_kms_findings(self):
        """Test KMS remediation."""
        findings = [
            create_mock_finding("CKV_AWS_7", "aws_kms_key.my_key"),
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        assert plan.remediable_findings == 1
        assert plan.files[0].remediation_type == RemediationType.KMS_ROTATION


class TestRemediationGeneratorOutput:
    """Test actual file output from generator."""

    def test_write_output(self):
        """Test writing generated files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            findings = [
                create_mock_finding("CKV_AWS_19", "aws_s3_bucket.bucket1"),
                create_mock_finding("CKV_AWS_18", "aws_s3_bucket.bucket2"),
            ]

            generator = RemediationGenerator(findings, output_dir)
            plan = generator.generate()
            paths = plan.write_all(output_dir)

            # Check that files were written
            assert len(paths) >= 2

            # Check that TF files exist (2 remediation + 1 imports.tf)
            tf_files = list(output_dir.glob("**/*.tf"))
            assert len(tf_files) == 3

            # Check README exists
            assert (output_dir / "README.md").exists()

    def test_terraform_syntax(self):
        """Test that generated Terraform is syntactically correct."""
        findings = [
            create_mock_finding("CKV_AWS_19", "aws_s3_bucket.bucket1"),
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        content = plan.files[0].content

        # Basic Terraform syntax checks
        assert "resource" in content
        assert "{" in content
        assert "}" in content
        assert content.count("{") == content.count("}")


# =============================================================================
# SEVERITY TESTS
# =============================================================================


class TestSeverityMapping:
    """Test severity mapping."""

    def test_critical_severity(self):
        """Test critical severity checks."""
        findings = [
            create_mock_finding("CKV_AWS_24", "aws_security_group.sg"),
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        assert plan.files[0].severity == RemediationSeverity.CRITICAL

    def test_high_severity(self):
        """Test high severity checks."""
        findings = [
            create_mock_finding("CKV_AWS_19", "aws_s3_bucket.bucket"),
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        assert plan.files[0].severity == RemediationSeverity.HIGH

    def test_medium_severity(self):
        """Test medium severity checks."""
        findings = [
            create_mock_finding("CKV_AWS_18", "aws_s3_bucket.bucket"),
        ]

        generator = RemediationGenerator(findings)
        plan = generator.generate()

        assert plan.files[0].severity == RemediationSeverity.MEDIUM
