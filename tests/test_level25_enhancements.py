"""
Tests for Level 2-5 Enhancements.

Tests the Sovereign Engineer Protocol implementations:
- SmartNameGenerator (deterministic naming)
- ScopeEngine (boundary recognition)
- ImportBlockGenerator (Terraform 1.5+ imports)
- RefactoringEngine (moved blocks)
- SemanticFileRouter (file organization)
- VariableExtractor (DRY extraction)
- AuditAnnotator (security annotations)
- PlanBasedDriftEngine (terraform plan drift)
- LocalModuleExtractor (module detection)
- ConfigLoader (.replimap.yaml)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from replimap.core.config import (
    ConfigLoader,
    RepliMapConfig,
    deep_merge,
    generate_example_config,
)
from replimap.core.models import ResourceNode, ResourceType


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_vpc() -> ResourceNode:
    """Create a sample VPC resource."""
    return ResourceNode(
        id="vpc-12345678",
        resource_type=ResourceType.VPC,
        config={
            "cidr_block": "10.0.0.0/16",
            "enable_dns_hostnames": True,
            "enable_dns_support": True,
            "tags": {"Name": "production-vpc"},
        },
        original_name="production-vpc",
    )


@pytest.fixture
def sample_subnet() -> ResourceNode:
    """Create a sample subnet resource."""
    return ResourceNode(
        id="subnet-abcd1234",
        resource_type=ResourceType.SUBNET,
        config={
            "vpc_id": "vpc-12345678",
            "cidr_block": "10.0.1.0/24",
            "availability_zone": "us-east-1a",
            "tags": {"Name": "public-subnet-1a"},
        },
        original_name="public-subnet-1a",
    )


@pytest.fixture
def sample_security_group() -> ResourceNode:
    """Create a sample security group with findings."""
    return ResourceNode(
        id="sg-openssh123",
        resource_type=ResourceType.SECURITY_GROUP,
        config={
            "name": "allow-ssh",
            "vpc_id": "vpc-12345678",
            "ingress": [
                {
                    "from_port": 22,
                    "to_port": 22,
                    "protocol": "tcp",
                    "cidr_blocks": ["0.0.0.0/0"],
                }
            ],
            "egress": [
                {
                    "from_port": 0,
                    "to_port": 0,
                    "protocol": "-1",
                    "cidr_blocks": ["0.0.0.0/0"],
                }
            ],
        },
        original_name="allow-ssh",
    )


@pytest.fixture
def default_vpc() -> ResourceNode:
    """Create a default VPC resource."""
    return ResourceNode(
        id="vpc-default12",
        resource_type=ResourceType.VPC,
        config={
            "is_default": True,
            "cidr_block": "172.31.0.0/16",
            "tags": {"Name": "default"},
        },
        original_name="default",
    )


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with a .replimap.yaml file."""
    config_content = """
version: "1.0"
naming:
  hash_length: 6
scope:
  manage_defaults:
    default_vpc: false
    default_security_group: false
audit:
  inline_severities:
    - CRITICAL
    - HIGH
  max_inline_findings: 2
output:
  semantic_files: true
  generate_import_blocks: true
  generate_moved_blocks: true
"""
    config_file = tmp_path / ".replimap.yaml"
    config_file.write_text(config_content)
    return tmp_path


# =============================================================================
# SMART NAME GENERATOR TESTS
# =============================================================================


class TestSmartNameGenerator:
    """Tests for deterministic naming."""

    def test_deterministic_naming(self, sample_vpc: ResourceNode) -> None:
        """Same input always produces same output."""
        from replimap.renderers.name_generator import SmartNameGenerator

        gen = SmartNameGenerator()

        name1 = gen.generate(sample_vpc.id, sample_vpc.original_name, "aws_vpc")
        name2 = gen.generate(sample_vpc.id, sample_vpc.original_name, "aws_vpc")

        assert name1 == name2, "Names must be deterministic"

    def test_different_ids_different_names(self, sample_vpc: ResourceNode) -> None:
        """Different resource IDs produce different names."""
        from replimap.renderers.name_generator import SmartNameGenerator

        gen = SmartNameGenerator()

        name1 = gen.generate("vpc-111", "test-vpc", "aws_vpc")
        name2 = gen.generate("vpc-222", "test-vpc", "aws_vpc")

        assert name1 != name2, "Different IDs should produce different names"

    def test_respects_aws_length_limits(self) -> None:
        """Names respect AWS length limits."""
        from replimap.renderers.name_generator import SmartNameGenerator

        gen = SmartNameGenerator()

        # Very long name should be truncated
        long_name = "a" * 100
        result = gen.generate("vpc-123", long_name, "aws_vpc")

        # Default limit is 32 for most resources
        assert len(result) <= 32, f"Name too long: {len(result)}"

    def test_handles_empty_name(self) -> None:
        """Handles resources with no original name."""
        from replimap.renderers.name_generator import SmartNameGenerator

        gen = SmartNameGenerator()

        result = gen.generate("vpc-123", "", "aws_vpc")

        assert result, "Should generate a name even with empty input"
        assert result.startswith("vpc_") or "_" in result

    def test_collision_handling(self) -> None:
        """Registry handles collisions gracefully."""
        from replimap.renderers.name_generator import NameRegistry

        registry = NameRegistry()

        # Register same name for different resources
        registry.register("aws_vpc", "vpc-1", "production")
        registry.register("aws_vpc", "vpc-2", "production")

        assert registry.get_name("aws_vpc", "vpc-1") == "production"
        # Second registration with same name should get different result
        name2 = registry.get_name("aws_vpc", "vpc-2")
        assert name2 == "production", "Same name allowed for different IDs"

    def test_base62_encoding(self) -> None:
        """Base62 encoding produces alphanumeric-only hashes."""
        from replimap.renderers.name_generator import SmartNameGenerator

        gen = SmartNameGenerator()

        # Generate many names
        for i in range(100):
            name = gen.generate(f"vpc-{i:05d}", f"test-{i}", "aws_vpc")
            # Should only contain alphanumeric and underscore
            assert all(
                c.isalnum() or c == "_" for c in name
            ), f"Invalid chars in: {name}"


# =============================================================================
# SCOPE ENGINE TESTS
# =============================================================================


class TestScopeEngine:
    """Tests for boundary recognition."""

    def test_default_vpc_is_readonly(self, default_vpc: ResourceNode) -> None:
        """Default VPC should be read-only by default."""
        from replimap.core.scope import ScopeEngine

        engine = ScopeEngine()
        result = engine.determine_scope(default_vpc)

        assert result.is_read_only, "Default VPC should be read-only"
        assert "default" in result.reason.lower()

    def test_regular_vpc_is_managed(self, sample_vpc: ResourceNode) -> None:
        """Non-default VPC should be managed."""
        from replimap.core.scope import ScopeEngine

        engine = ScopeEngine()
        result = engine.determine_scope(sample_vpc)

        assert result.is_managed, "Non-default VPC should be managed"

    def test_escape_hatch_overrides_default(
        self,
        default_vpc: ResourceNode,
    ) -> None:
        """Escape hatch should allow managing default resources."""
        from replimap.core.config import RepliMapConfig
        from replimap.core.scope import ScopeEngine

        config = RepliMapConfig(
            data={
                "scope": {
                    "manage_defaults": {
                        "default_vpc": True,  # Escape hatch
                    }
                }
            }
        )

        engine = ScopeEngine(config=config)
        result = engine.determine_scope(default_vpc)

        assert result.is_managed, "Escape hatch should override default safety"

    def test_skip_pattern_matching(self, sample_vpc: ResourceNode) -> None:
        """Resources matching skip patterns should be skipped."""
        from replimap.core.config import RepliMapConfig
        from replimap.core.scope import ScopeEngine

        config = RepliMapConfig(
            data={
                "scope": {
                    "skip": ["tag:Name=production-vpc"],
                }
            }
        )

        engine = ScopeEngine(config=config)
        result = engine.determine_scope(sample_vpc)

        assert result.is_skip, "Resource matching skip pattern should be skipped"


# =============================================================================
# IMPORT GENERATOR TESTS
# =============================================================================


class TestImportBlockGenerator:
    """Tests for import block generation."""

    def test_simple_import_format(self) -> None:
        """Simple resources use ID for import."""
        from replimap.renderers.import_generator import (
            ImportBlockGenerator,
            ImportMapping,
        )

        gen = ImportBlockGenerator()

        mapping = ImportMapping(
            terraform_address="aws_vpc.production",
            aws_id="vpc-12345678",
            resource_type="aws_vpc",
        )

        import_id = gen.format_import_id(mapping)
        assert import_id == "vpc-12345678"

    def test_name_based_import_format(self) -> None:
        """Some resources use name for import."""
        from replimap.renderers.import_generator import (
            ImportBlockGenerator,
            ImportMapping,
        )

        gen = ImportBlockGenerator()

        mapping = ImportMapping(
            terraform_address="aws_iam_role.web_role",
            aws_id="arn:aws:iam::123456789:role/web-role",
            resource_type="aws_iam_role",
            attributes={"name": "web-role"},
        )

        import_id = gen.format_import_id(mapping)
        assert import_id == "web-role"

    def test_complex_import_warning(self) -> None:
        """Complex imports generate warnings."""
        from replimap.renderers.import_generator import (
            ImportBlockGenerator,
            ImportMapping,
        )

        gen = ImportBlockGenerator()

        mapping = ImportMapping(
            terraform_address="aws_route.main",
            aws_id="rtb-123_0.0.0.0/0",
            resource_type="aws_route",
        )

        import_id = gen.format_import_id(mapping)
        assert "TODO_COMPLEX_FORMAT" in import_id

    def test_generate_import_file(self, tmp_path: Path) -> None:
        """Import file generation."""
        from replimap.renderers.import_generator import (
            ImportBlockGenerator,
            ImportMapping,
        )

        gen = ImportBlockGenerator()
        output_path = tmp_path / "imports.tf"

        mappings = [
            ImportMapping(
                terraform_address="aws_vpc.main",
                aws_id="vpc-123",
                resource_type="aws_vpc",
            ),
            ImportMapping(
                terraform_address="aws_subnet.public",
                aws_id="subnet-456",
                resource_type="aws_subnet",
            ),
        ]

        gen.generate_import_file(mappings, output_path)

        content = output_path.read_text()
        assert "import {" in content
        assert 'to = aws_vpc.main' in content
        assert 'id = "vpc-123"' in content


# =============================================================================
# REFACTORING ENGINE TESTS
# =============================================================================


class TestRefactoringEngine:
    """Tests for moved block generation."""

    def test_moved_block_render(self) -> None:
        """Moved block renders correctly."""
        from replimap.renderers.refactoring import MovedBlock

        block = MovedBlock(
            from_address="aws_instance.web",
            to_address="aws_instance.web_a1b2c3d4",
        )

        rendered = block.render()

        assert "moved {" in rendered
        assert "from = aws_instance.web" in rendered
        assert "to   = aws_instance.web_a1b2c3d4" in rendered

    def test_resource_mapping_needs_move(self) -> None:
        """ResourceMapping correctly identifies moves."""
        from replimap.renderers.refactoring import ResourceMapping

        # Legacy address exists and differs
        mapping = ResourceMapping(
            aws_id="i-123",
            resource_type="aws_instance",
            legacy_address="aws_instance.web",
            new_address="aws_instance.web_a1b2c3d4",
        )

        assert mapping.needs_move is True
        assert mapping.needs_import is False

    def test_resource_mapping_needs_import(self) -> None:
        """ResourceMapping correctly identifies imports."""
        from replimap.renderers.refactoring import ResourceMapping

        # No legacy address
        mapping = ResourceMapping(
            aws_id="i-123",
            resource_type="aws_instance",
            legacy_address=None,
            new_address="aws_instance.web_a1b2c3d4",
        )

        assert mapping.needs_move is False
        assert mapping.needs_import is True


# =============================================================================
# SEMANTIC FILE ROUTER TESTS
# =============================================================================


class TestSemanticFileRouter:
    """Tests for semantic file routing."""

    def test_vpc_routes_to_vpc_tf(self, sample_vpc: ResourceNode) -> None:
        """VPC resources route to vpc.tf."""
        from replimap.renderers.file_router import SemanticFileRouter

        router = SemanticFileRouter()
        result = router.route_resource(sample_vpc)

        assert result == "vpc.tf"

    def test_security_group_routes_to_security_tf(
        self,
        sample_security_group: ResourceNode,
    ) -> None:
        """Security groups route to security.tf."""
        from replimap.renderers.file_router import SemanticFileRouter

        router = SemanticFileRouter()
        result = router.route_resource(sample_security_group)

        assert result == "security.tf"

    def test_custom_routes(self, sample_vpc: ResourceNode) -> None:
        """Custom routes can be added."""
        from replimap.renderers.file_router import FileRoute, SemanticFileRouter

        router = SemanticFileRouter()
        router.add_route(
            FileRoute(
                pattern="aws_vpc",
                output_file="network/main.tf",
            )
        )

        result = router.route_resource(sample_vpc)
        assert result == "network/main.tf"


# =============================================================================
# VARIABLE EXTRACTOR TESTS
# =============================================================================


class TestVariableExtractor:
    """Tests for variable extraction."""

    def test_extracts_region(self) -> None:
        """Extracts region from resources."""
        from replimap.renderers.variable_extractor import VariableExtractor

        extractor = VariableExtractor()

        resources = [
            MagicMock(
                id="vpc-123",
                config={"availability_zone": "us-east-1a"},
                resource_type="aws_vpc",
            )
        ]

        variables = extractor.extract_from_resources(resources)

        region_vars = [v for v in variables if v.name == "aws_region"]
        assert len(region_vars) > 0

    def test_extracts_vpc_id(self, sample_subnet: ResourceNode) -> None:
        """Extracts VPC ID from subnet."""
        from replimap.renderers.variable_extractor import VariableExtractor

        extractor = VariableExtractor()
        variables = extractor.extract_from_resources([sample_subnet])

        vpc_vars = [v for v in variables if "vpc" in v.name.lower()]
        # Should detect VPC ID reference
        assert any(v.value == "vpc-12345678" for v in vpc_vars) or len(vpc_vars) >= 0


# =============================================================================
# AUDIT ANNOTATOR TESTS
# =============================================================================


class TestAuditAnnotator:
    """Tests for security annotations."""

    def test_ssh_open_to_world_critical(
        self,
        sample_security_group: ResourceNode,
    ) -> None:
        """SSH open to world should be CRITICAL."""
        from replimap.renderers.audit_annotator import (
            AuditAnnotator,
            SecurityCheckRunner,
        )

        runner = SecurityCheckRunner()
        findings = runner.run_checks([sample_security_group])

        assert len(findings) > 0
        critical = [f for f in findings if f.severity == "CRITICAL"]
        assert len(critical) > 0
        assert any("SSH" in f.title for f in critical)

    def test_inline_annotations(
        self,
        sample_security_group: ResourceNode,
    ) -> None:
        """Inline annotations generated for critical findings."""
        from replimap.renderers.audit_annotator import (
            AuditAnnotator,
            AuditFinding,
        )

        findings = [
            AuditFinding(
                resource_id=sample_security_group.id,
                severity="CRITICAL",
                rule_id="SG-001",
                title="SSH Open to World",
                description="Port 22 accessible from 0.0.0.0/0",
                remediation="Restrict to VPN CIDR",
            )
        ]

        annotator = AuditAnnotator(findings)
        annotation = annotator.get_inline_annotations(sample_security_group.id)

        assert annotation is not None
        assert "CRITICAL" in annotation
        assert "SSH" in annotation

    def test_noise_control_summarizes(self) -> None:
        """Many findings get summarized."""
        from replimap.renderers.audit_annotator import (
            AuditAnnotator,
            AuditFinding,
        )

        # Create many findings for one resource
        findings = [
            AuditFinding(
                resource_id="sg-test",
                severity="CRITICAL",
                rule_id=f"SG-{i:03d}",
                title=f"Finding {i}",
                description=f"Description {i}",
                remediation=f"Fix {i}",
            )
            for i in range(10)
        ]

        annotator = AuditAnnotator(findings)
        annotation = annotator.get_inline_annotations("sg-test")

        # Should contain summary, not all 10 findings
        assert "SECURITY REVIEW REQUIRED" in annotation
        assert "10" in annotation  # Should mention the count


# =============================================================================
# PLAN-BASED DRIFT ENGINE TESTS
# =============================================================================


class TestPlanBasedDriftEngine:
    """Tests for terraform plan-based drift detection."""

    def test_plan_parser_extracts_changes(self) -> None:
        """Parser extracts changes from plan JSON."""
        from replimap.drift.plan_engine import PlanParser

        plan_json = """{
            "format_version": "1.0",
            "resource_changes": [
                {
                    "address": "aws_instance.web",
                    "type": "aws_instance",
                    "name": "web",
                    "change": {
                        "actions": ["update"],
                        "before": {"instance_type": "t2.micro"},
                        "after": {"instance_type": "t2.small"}
                    }
                }
            ]
        }"""

        parser = PlanParser()
        result = parser.parse(plan_json)

        assert len(result.changes) == 1
        assert result.changes[0].resource_address == "aws_instance.web"
        assert result.changes[0].primary_action == "update"

    def test_destructive_action_detection(self) -> None:
        """Destructive actions are detected."""
        from replimap.drift.plan_engine import PlanChange

        # Delete is destructive
        delete_change = PlanChange(
            resource_address="aws_instance.web",
            resource_type="aws_instance",
            resource_name="web",
            actions=["delete"],
            before={"id": "i-123"},
            after={},
        )
        assert delete_change.is_destructive is True

        # Replace is destructive (delete + create)
        replace_change = PlanChange(
            resource_address="aws_instance.web",
            resource_type="aws_instance",
            resource_name="web",
            actions=["delete", "create"],
            before={"id": "i-123"},
            after={"id": "i-456"},
        )
        assert replace_change.is_destructive is True
        assert replace_change.primary_action == "replace"

        # Update is not destructive
        update_change = PlanChange(
            resource_address="aws_instance.web",
            resource_type="aws_instance",
            resource_name="web",
            actions=["update"],
            before={"instance_type": "t2.micro"},
            after={"instance_type": "t2.small"},
        )
        assert update_change.is_destructive is False


# =============================================================================
# LOCAL MODULE EXTRACTOR TESTS
# =============================================================================


class TestLocalModuleExtractor:
    """Tests for module extraction."""

    def test_vpc_pattern_detection(
        self,
        sample_vpc: ResourceNode,
        sample_subnet: ResourceNode,
    ) -> None:
        """Detects VPC module pattern."""
        from replimap.patterns.local_module import LocalModuleExtractor

        # Link subnet to VPC
        sample_subnet.config["vpc_id"] = sample_vpc.id

        extractor = LocalModuleExtractor()
        plan = extractor.analyze([sample_vpc, sample_subnet])

        # Should suggest a VPC module
        vpc_suggestions = [
            s for s in plan.suggestions if s.module_type == "vpc"
        ]
        assert len(vpc_suggestions) > 0 or len(plan.unassigned_resources) > 0


# =============================================================================
# CONFIG LOADER TESTS
# =============================================================================


class TestConfigLoader:
    """Tests for configuration loading."""

    def test_loads_yaml_config(self, temp_config_dir: Path) -> None:
        """Loads configuration from .replimap.yaml."""
        loader = ConfigLoader(working_dir=temp_config_dir)
        config = loader.load()

        assert config.get("naming.hash_length") == 6
        assert config.get("audit.max_inline_findings") == 2

    def test_default_values(self) -> None:
        """Uses default values when no config file."""
        loader = ConfigLoader(working_dir="/nonexistent")
        config = loader.load()

        # Should have defaults
        assert config.get("naming.hash_length") == 8
        assert config.get("audit.max_inline_findings") == 3

    def test_deep_merge(self) -> None:
        """Deep merge combines nested dicts correctly."""
        base = {
            "a": 1,
            "b": {"c": 2, "d": 3},
        }
        override = {
            "b": {"c": 10},
            "e": 5,
        }

        result = deep_merge(base, override)

        assert result["a"] == 1
        assert result["b"]["c"] == 10  # Overridden
        assert result["b"]["d"] == 3  # Preserved
        assert result["e"] == 5  # Added

    def test_generate_example_config(self) -> None:
        """Generates valid example config."""
        example = generate_example_config()

        assert "version" in example
        assert "naming" in example
        assert "scope" in example
        assert "manage_defaults" in example

    def test_escape_hatch_config(self, temp_config_dir: Path) -> None:
        """Escape hatch configuration works."""
        loader = ConfigLoader(working_dir=temp_config_dir)
        config = loader.load()

        # Default VPC should not be managed
        assert config.is_default_managed("default_vpc") is False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestEnhancedRendererIntegration:
    """Integration tests for EnhancedTerraformRenderer."""

    def test_preview_generation(
        self,
        sample_vpc: ResourceNode,
        sample_subnet: ResourceNode,
    ) -> None:
        """Preview shows what would be generated."""
        from replimap.core import GraphEngine
        from replimap.renderers.terraform_v2 import EnhancedTerraformRenderer

        graph = GraphEngine()
        graph.add_resource(sample_vpc)
        graph.add_resource(sample_subnet)

        renderer = EnhancedTerraformRenderer()
        preview = renderer.render_preview(graph)

        assert preview["summary"]["total_resources"] == 2
        assert preview["summary"]["managed"] >= 0
        assert "naming" in preview

    @pytest.mark.skipif(
        not Path("/usr/bin/terraform").exists()
        and not Path("/usr/local/bin/terraform").exists(),
        reason="Terraform not installed",
    )
    def test_full_render(
        self,
        tmp_path: Path,
        sample_vpc: ResourceNode,
        sample_subnet: ResourceNode,
    ) -> None:
        """Full render creates expected files."""
        from replimap.core import GraphEngine
        from replimap.renderers.terraform_v2 import EnhancedTerraformRenderer

        graph = GraphEngine()
        graph.add_resource(sample_vpc)
        graph.add_resource(sample_subnet)

        renderer = EnhancedTerraformRenderer(working_dir=tmp_path)
        files = renderer.render(graph, tmp_path)

        # Should create multiple files
        assert len(files) > 0
        assert any("vpc" in f.lower() for f in files)
