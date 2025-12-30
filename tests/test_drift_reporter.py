"""
Comprehensive tests for the Drift Reporter module.

Tests cover:
- Terraform resource name sanitization
- Shell quoting for resource IDs
- Remediation command generation for all drift types
- Edge cases and error handling
"""


from replimap.drift.models import DriftType, ResourceDrift
from replimap.drift.reporter import (
    _generate_remediation_cmd,
    _get_drift_classification,
    _sanitize_tf_resource_name,
    _shell_quote,
)


class TestSanitizeTfResourceName:
    """Tests for Terraform resource name sanitization."""

    def test_simple_name_unchanged(self):
        """Simple alphanumeric names should be unchanged."""
        assert _sanitize_tf_resource_name("my_resource") == "my_resource"
        assert _sanitize_tf_resource_name("MyResource123") == "MyResource123"

    def test_dashes_replaced_with_underscore(self):
        """Dashes should be replaced with underscores."""
        assert _sanitize_tf_resource_name("my-resource") == "my_resource"
        assert _sanitize_tf_resource_name("my-long-name") == "my_long_name"

    def test_slashes_replaced_with_underscore(self):
        """Forward slashes should be replaced with underscores."""
        assert _sanitize_tf_resource_name("/aws-glue/crawlers") == "aws_glue_crawlers"
        assert _sanitize_tf_resource_name("path/to/resource") == "path_to_resource"

    def test_colons_replaced_with_underscore(self):
        """Colons should be replaced with underscores."""
        result = _sanitize_tf_resource_name("arn:aws:sns:us-east-1:123:topic")
        assert result == "arn_aws_sns_us_east_1_123_topic"

    def test_dots_replaced_with_underscore(self):
        """Dots should be replaced with underscores."""
        assert _sanitize_tf_resource_name("my.resource.name") == "my_resource_name"

    def test_spaces_replaced_with_underscore(self):
        """Spaces should be replaced with underscores."""
        assert _sanitize_tf_resource_name("my resource") == "my_resource"
        assert _sanitize_tf_resource_name("log group name") == "log_group_name"

    def test_special_chars_replaced(self):
        """Various special characters should be replaced."""
        assert _sanitize_tf_resource_name("name@domain") == "name_domain"
        assert _sanitize_tf_resource_name("name#tag") == "name_tag"
        assert _sanitize_tf_resource_name("name!important") == "name_important"
        assert _sanitize_tf_resource_name("name$var") == "name_var"

    def test_consecutive_underscores_collapsed(self):
        """Multiple consecutive underscores should collapse to one."""
        assert _sanitize_tf_resource_name("my---name") == "my_name"
        assert _sanitize_tf_resource_name("a//b//c") == "a_b_c"
        assert _sanitize_tf_resource_name("path/to//resource") == "path_to_resource"

    def test_leading_underscores_stripped(self):
        """Leading underscores should be stripped."""
        assert _sanitize_tf_resource_name("/resource") == "resource"
        assert _sanitize_tf_resource_name("///resource") == "resource"

    def test_trailing_underscores_stripped(self):
        """Trailing underscores should be stripped."""
        assert _sanitize_tf_resource_name("resource/") == "resource"
        assert _sanitize_tf_resource_name("resource///") == "resource"

    def test_leading_digit_gets_prefix(self):
        """Names starting with digit should get 'r_' prefix."""
        assert _sanitize_tf_resource_name("123bucket") == "r_123bucket"
        assert _sanitize_tf_resource_name("123-my-bucket") == "r_123_my_bucket"
        assert _sanitize_tf_resource_name("0_start") == "r_0_start"

    def test_empty_string_returns_unknown(self):
        """Empty string should return 'unknown'."""
        assert _sanitize_tf_resource_name("") == "unknown"

    def test_only_special_chars_returns_imported(self):
        """String with only special chars returns 'imported'."""
        assert _sanitize_tf_resource_name("///") == "imported"
        assert _sanitize_tf_resource_name("---") == "imported"
        assert _sanitize_tf_resource_name("...") == "imported"
        assert _sanitize_tf_resource_name("@#$%") == "imported"

    def test_length_limited_to_60(self):
        """Very long names should be truncated to 60 chars."""
        long_name = "a" * 100
        result = _sanitize_tf_resource_name(long_name)
        assert len(result) == 60
        assert result == "a" * 60

    def test_complex_aws_log_group_paths(self):
        """Test real-world AWS CloudWatch log group paths."""
        assert (
            _sanitize_tf_resource_name("/aws/lambda/my-function")
            == "aws_lambda_my_function"
        )
        assert (
            _sanitize_tf_resource_name("/aws/rds/cluster/my-db")
            == "aws_rds_cluster_my_db"
        )
        assert _sanitize_tf_resource_name("/ecs/my-service") == "ecs_my_service"


class TestShellQuote:
    """Tests for shell quoting function."""

    def test_simple_string_not_quoted(self):
        """Simple strings without special chars aren't quoted."""
        assert _shell_quote("simple-id") == "simple-id"
        assert _shell_quote("my_resource") == "my_resource"
        assert _shell_quote("sg-abc123") == "sg-abc123"

    def test_slashes_not_quoted(self):
        """Forward slashes don't need quoting."""
        assert _shell_quote("/aws-glue/crawlers") == "/aws-glue/crawlers"
        assert _shell_quote("path/to/resource") == "path/to/resource"

    def test_colons_not_quoted(self):
        """Colons don't need quoting."""
        assert (
            _shell_quote("arn:aws:sns:us-east-1:123:topic")
            == "arn:aws:sns:us-east-1:123:topic"
        )

    def test_spaces_get_quoted(self):
        """Strings with spaces should be quoted."""
        assert _shell_quote("id with spaces") == "'id with spaces'"
        assert _shell_quote("my resource") == "'my resource'"

    def test_tabs_get_quoted(self):
        """Strings with tabs should be quoted."""
        assert _shell_quote("id\twith\ttabs") == "'id\twith\ttabs'"

    def test_special_shell_chars_get_quoted(self):
        """Special shell characters trigger quoting."""
        assert _shell_quote("$(command)") == "'$(command)'"
        assert _shell_quote("foo && bar") == "'foo && bar'"
        assert _shell_quote("foo | bar") == "'foo | bar'"
        assert _shell_quote("foo; bar") == "'foo; bar'"
        assert _shell_quote("foo > bar") == "'foo > bar'"
        assert _shell_quote("foo < bar") == "'foo < bar'"

    def test_single_quotes_escaped(self):
        """Single quotes within the string are properly escaped."""
        result = _shell_quote("it's")
        assert result == "'it'\"'\"'s'"

    def test_double_quotes_trigger_quoting(self):
        """Double quotes trigger single-quote wrapping."""
        assert _shell_quote('say "hello"') == "'say \"hello\"'"

    def test_backticks_get_quoted(self):
        """Backticks should be quoted to prevent command substitution."""
        assert _shell_quote("`command`") == "'`command`'"

    def test_backslash_gets_quoted(self):
        """Backslashes should be quoted."""
        assert _shell_quote("path\\to\\resource") == "'path\\to\\resource'"

    def test_wildcards_get_quoted(self):
        """Wildcard characters should be quoted."""
        assert _shell_quote("file*") == "'file*'"
        assert _shell_quote("file?") == "'file?'"


class TestGenerateRemediationCmd:
    """Tests for remediation command generation."""

    def _make_drift(
        self,
        resource_id: str,
        resource_type: str = "aws_instance",
        drift_type: DriftType = DriftType.MODIFIED,
        tf_address: str = "",
    ) -> ResourceDrift:
        """Helper to create a ResourceDrift for testing."""
        return ResourceDrift(
            resource_id=resource_id,
            resource_type=resource_type,
            resource_name="test",
            drift_type=drift_type,
            tf_address=tf_address,
            diffs=[],
        )

    def test_modified_with_tf_address(self):
        """MODIFIED with tf_address uses the address directly."""
        drift = self._make_drift(
            resource_id="i-12345",
            drift_type=DriftType.MODIFIED,
            tf_address="module.web.aws_instance.main",
        )
        cmd = _generate_remediation_cmd(drift)
        assert cmd == "terraform apply -target=module.web.aws_instance.main"

    def test_modified_without_tf_address(self):
        """MODIFIED without tf_address generates address from ID."""
        drift = self._make_drift(
            resource_id="i-12345",
            drift_type=DriftType.MODIFIED,
        )
        cmd = _generate_remediation_cmd(drift)
        assert cmd == "terraform apply -target=aws_instance.i_12345"

    def test_added_generates_import_command(self):
        """ADDED generates terraform import command."""
        drift = self._make_drift(
            resource_id="sg-abc123",
            resource_type="aws_security_group",
            drift_type=DriftType.ADDED,
        )
        cmd = _generate_remediation_cmd(drift)
        assert cmd == "terraform import aws_security_group.sg_abc123 sg-abc123"

    def test_added_with_special_chars_in_id(self):
        """ADDED with special chars quotes the resource ID."""
        drift = self._make_drift(
            resource_id="/aws glue/crawlers",  # Space in path
            resource_type="aws_cloudwatch_log_group",
            drift_type=DriftType.ADDED,
        )
        cmd = _generate_remediation_cmd(drift)
        assert (
            cmd
            == "terraform import aws_cloudwatch_log_group.aws_glue_crawlers '/aws glue/crawlers'"
        )

    def test_added_with_leading_digit(self):
        """ADDED with leading digit in ID prefixes resource name."""
        drift = self._make_drift(
            resource_id="123-my-bucket",
            resource_type="aws_s3_bucket",
            drift_type=DriftType.ADDED,
        )
        cmd = _generate_remediation_cmd(drift)
        assert cmd == "terraform import aws_s3_bucket.r_123_my_bucket 123-my-bucket"

    def test_added_with_only_special_chars(self):
        """ADDED with only special chars in ID uses fallback name."""
        drift = self._make_drift(
            resource_id="///",
            resource_type="aws_cloudwatch_log_group",
            drift_type=DriftType.ADDED,
        )
        cmd = _generate_remediation_cmd(drift)
        assert cmd == "terraform import aws_cloudwatch_log_group.imported ///"

    def test_removed_generates_apply_command(self):
        """REMOVED generates terraform apply command to recreate."""
        drift = self._make_drift(
            resource_id="sg-deleted",
            resource_type="aws_security_group",
            drift_type=DriftType.REMOVED,
            tf_address="aws_security_group.web",
        )
        cmd = _generate_remediation_cmd(drift)
        assert cmd == "terraform apply -target=aws_security_group.web"

    def test_unscanned_returns_empty(self):
        """UNSCANNED returns empty string."""
        drift = self._make_drift(
            resource_id="some-resource",
            drift_type=DriftType.UNSCANNED,
        )
        cmd = _generate_remediation_cmd(drift)
        assert cmd == ""

    def test_unchanged_returns_empty(self):
        """UNCHANGED returns empty string."""
        drift = self._make_drift(
            resource_id="some-resource",
            drift_type=DriftType.UNCHANGED,
        )
        cmd = _generate_remediation_cmd(drift)
        assert cmd == ""

    def test_cloudwatch_log_group_path(self):
        """Real-world CloudWatch log group path test."""
        drift = self._make_drift(
            resource_id="/aws/lambda/my-function",
            resource_type="aws_cloudwatch_log_group",
            drift_type=DriftType.ADDED,
        )
        cmd = _generate_remediation_cmd(drift)
        assert (
            cmd
            == "terraform import aws_cloudwatch_log_group.aws_lambda_my_function /aws/lambda/my-function"
        )

    def test_arn_based_resource_id(self):
        """ARN-based resource IDs are sanitized correctly."""
        drift = self._make_drift(
            resource_id="arn:aws:sns:us-east-1:123456789012:my-topic",
            resource_type="aws_sns_topic",
            drift_type=DriftType.ADDED,
        )
        cmd = _generate_remediation_cmd(drift)
        # The sanitized name should not be too long
        assert "terraform import aws_sns_topic." in cmd
        assert "arn:aws:sns:us-east-1:123456789012:my-topic" in cmd


class TestGetDriftClassification:
    """Tests for drift classification logic."""

    def _make_drift(
        self,
        drift_type: DriftType = DriftType.MODIFIED,
        diffs: list | None = None,
    ) -> ResourceDrift:
        """Helper to create a ResourceDrift for testing."""

        if diffs is None:
            diffs = []
        return ResourceDrift(
            resource_id="test-id",
            resource_type="aws_instance",
            resource_name="test",
            drift_type=drift_type,
            tf_address="",
            diffs=diffs,
        )

    def test_added_is_semantic(self):
        """ADDED drift is always semantic."""
        drift = self._make_drift(drift_type=DriftType.ADDED)
        assert _get_drift_classification(drift) == "semantic"

    def test_removed_is_semantic(self):
        """REMOVED drift is always semantic."""
        drift = self._make_drift(drift_type=DriftType.REMOVED)
        assert _get_drift_classification(drift) == "semantic"

    def test_unscanned_is_none(self):
        """UNSCANNED drift is 'none' (no action possible)."""
        drift = self._make_drift(drift_type=DriftType.UNSCANNED)
        assert _get_drift_classification(drift) == "none"

    def test_modified_no_diffs_is_none(self):
        """MODIFIED with no diffs is 'none'."""
        drift = self._make_drift(drift_type=DriftType.MODIFIED, diffs=[])
        assert _get_drift_classification(drift) == "none"

    def test_modified_with_semantic_diff(self):
        """MODIFIED with semantic diff is 'semantic'."""
        from replimap.drift.models import AttributeDiff, DriftReason

        drift = self._make_drift(
            drift_type=DriftType.MODIFIED,
            diffs=[
                AttributeDiff(
                    attribute="instance_type",
                    expected="t2.micro",
                    actual="t2.small",
                    reason=DriftReason.SEMANTIC,
                )
            ],
        )
        assert _get_drift_classification(drift) == "semantic"

    def test_modified_with_only_tag_diffs(self):
        """MODIFIED with only tag diffs is 'cosmetic'."""
        from replimap.drift.models import AttributeDiff, DriftReason

        drift = self._make_drift(
            drift_type=DriftType.MODIFIED,
            diffs=[
                AttributeDiff(
                    attribute="tags.Environment",
                    expected="prod",
                    actual="production",
                    reason=DriftReason.TAG_ONLY,
                )
            ],
        )
        assert _get_drift_classification(drift) == "cosmetic"

    def test_modified_mixed_diffs_is_semantic(self):
        """MODIFIED with both semantic and cosmetic diffs is 'semantic'."""
        from replimap.drift.models import AttributeDiff, DriftReason

        drift = self._make_drift(
            drift_type=DriftType.MODIFIED,
            diffs=[
                AttributeDiff(
                    attribute="tags.Name",
                    expected="old",
                    actual="new",
                    reason=DriftReason.TAG_ONLY,
                ),
                AttributeDiff(
                    attribute="instance_type",
                    expected="t2.micro",
                    actual="t2.small",
                    reason=DriftReason.SEMANTIC,
                ),
            ],
        )
        assert _get_drift_classification(drift) == "semantic"
