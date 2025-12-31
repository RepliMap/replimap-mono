"""Tests for Terraform naming utilities."""

import pytest

from replimap.core.naming import (
    get_size_variable_name,
    get_variable_name,
    sanitize_name,
)


class TestSanitizeName:
    """Tests for sanitize_name function."""

    def test_basic_hyphen_replacement(self) -> None:
        """Hyphens should be replaced with underscores."""
        assert sanitize_name("web-server") == "web_server"

    def test_dot_replacement(self) -> None:
        """Dots should be replaced with underscores."""
        assert sanitize_name("main.db") == "main_db"
        assert sanitize_name("my-db.production") == "my_db_production"

    def test_colon_replacement(self) -> None:
        """Colons should be replaced with underscores."""
        assert sanitize_name("a:b:c") == "a_b_c"

    def test_slash_replacement(self) -> None:
        """Slashes should be replaced with underscores."""
        assert sanitize_name("path/to/resource") == "path_to_resource"

    def test_space_replacement(self) -> None:
        """Spaces should be replaced with underscores."""
        assert sanitize_name("my resource") == "my_resource"

    def test_mixed_special_chars(self) -> None:
        """Multiple special characters should all be handled."""
        assert sanitize_name("a:b/c.d-e f") == "a_b_c_d_e_f"

    def test_lowercase_conversion(self) -> None:
        """Names should be lowercased."""
        assert sanitize_name("MyResource-123") == "myresource_123"
        assert sanitize_name("UPPERCASE") == "uppercase"

    def test_numeric_start_prefix(self) -> None:
        """Names starting with digit should be prefixed with underscore."""
        assert sanitize_name("123-invalid") == "_123_invalid"
        assert sanitize_name("0test") == "_0test"

    def test_collapse_multiple_underscores(self) -> None:
        """Multiple consecutive underscores should be collapsed."""
        assert sanitize_name("a--b__c") == "a_b_c"
        assert sanitize_name("test___name") == "test_name"

    def test_strip_leading_trailing_underscores(self) -> None:
        """Leading and trailing underscores should be stripped."""
        assert sanitize_name("_test_") == "test"
        assert sanitize_name("__name__") == "name"

    def test_empty_string(self) -> None:
        """Empty string should return _unnamed."""
        assert sanitize_name("") == "_unnamed"

    def test_only_special_chars(self) -> None:
        """String with only special characters should return _unnamed."""
        assert sanitize_name("---") == "_unnamed"
        assert sanitize_name("...") == "_unnamed"

    def test_preserves_numbers(self) -> None:
        """Numbers within names should be preserved."""
        assert sanitize_name("ec2-i-12345") == "ec2_i_12345"
        assert sanitize_name("rds123") == "rds123"


class TestGetVariableName:
    """Tests for get_variable_name function."""

    def test_basic_variable_name(self) -> None:
        """Should generate proper variable name."""
        result = get_variable_name("aws_instance", "web-server", "instance_type")
        assert result == "aws_instance_web_server_instance_type"

    def test_sanitizes_resource_name(self) -> None:
        """Resource name should be sanitized."""
        result = get_variable_name("aws_db_instance", "main.db", "instance_class")
        assert result == "aws_db_instance_main_db_instance_class"

    def test_handles_special_chars(self) -> None:
        """Should handle special characters in all parts."""
        result = get_variable_name("aws_instance", "my:special/name", "type")
        assert result == "aws_instance_my_special_name_type"


class TestGetSizeVariableName:
    """Tests for get_size_variable_name function."""

    def test_ec2_instance_type(self) -> None:
        """EC2 should use instance_type attribute."""
        result = get_size_variable_name("aws_instance", "web")
        assert result == "aws_instance_web_instance_type"

    def test_rds_instance_class(self) -> None:
        """RDS should use instance_class attribute."""
        result = get_size_variable_name("aws_db_instance", "main")
        assert result == "aws_db_instance_main_instance_class"

    def test_elasticache_node_type(self) -> None:
        """ElastiCache should use node_type attribute."""
        result = get_size_variable_name("aws_elasticache_cluster", "cache")
        assert result == "aws_elasticache_cluster_cache_node_type"

    def test_unknown_resource_fallback(self) -> None:
        """Unknown resource types should fall back to instance_type."""
        result = get_size_variable_name("aws_unknown", "test")
        assert result == "aws_unknown_test_instance_type"
