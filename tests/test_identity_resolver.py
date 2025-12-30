"""Tests for the Identity Resolver."""

from replimap.core.identity_resolver import (
    IDENTITY_REGISTRY,
    STRATEGIES,
    IdentityResolver,
    get_scanner_coverage,
    has_scanner_coverage,
)


class TestStrategies:
    """Tests for strategy functions."""

    def test_literal_returns_as_is(self):
        """Literal strategy returns value unchanged."""
        assert STRATEGIES["literal"]("vpc-12345", None) == "vpc-12345"
        assert STRATEGIES["literal"]("anything", None) == "anything"

    def test_path_tail_extracts_last_segment(self):
        """Path tail strategy extracts last path segment."""
        assert STRATEGIES["path_tail"]("/path/to/resource", None) == "resource"
        assert STRATEGIES["path_tail"]("a/b/c", None) == "c"
        assert STRATEGIES["path_tail"]("no-slash", None) == "no-slash"

    def test_path_tail_strips_trailing_slash(self):
        """Path tail handles trailing slashes."""
        assert STRATEGIES["path_tail"]("/path/to/resource/", None) == "resource"

    def test_url_tail_extracts_from_url(self):
        """URL tail strategy extracts resource from URL."""
        url = "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue"
        assert STRATEGIES["url_tail"](url, None) == "my-queue"

    def test_arn_tail_extracts_last_colon_segment(self):
        """ARN tail strategy extracts last colon-separated segment."""
        arn = "arn:aws:sqs:us-east-1:123456789012:my-queue"
        assert STRATEGIES["arn_tail"](arn, None) == "my-queue"

    def test_arn_resource_extracts_after_slash(self):
        """ARN resource strategy extracts resource after slash."""
        arn = "arn:aws:lambda:us-east-1:123456789012:function:my-function"
        assert STRATEGIES["arn_resource"](arn, None) == "my-function"

    def test_arn_resource_falls_back_to_arn_tail(self):
        """ARN resource uses arn_tail if no slash present."""
        arn = "arn:aws:sqs:us-east-1:123456789012:my-queue"
        assert STRATEGIES["arn_resource"](arn, None) == "my-queue"

    def test_regex_extracts_with_pattern(self):
        """Regex strategy extracts using provided pattern."""
        value = "autoScalingGroup:abc:autoScalingGroupName/my-asg"
        pattern = r"autoScalingGroupName/(.+)$"
        assert STRATEGIES["regex"](value, pattern) == "my-asg"

    def test_regex_returns_original_on_no_match(self):
        """Regex strategy returns original value if pattern doesn't match."""
        value = "no-match-here"
        pattern = r"autoScalingGroupName/(.+)$"
        assert STRATEGIES["regex"](value, pattern) == value

    def test_regex_returns_original_on_no_pattern(self):
        """Regex strategy returns original value if no pattern provided."""
        value = "some-value"
        assert STRATEGIES["regex"](value, None) == value


class TestIdentityRegistry:
    """Tests for the identity registry configuration."""

    def test_sqs_queue_has_dual_strategy(self):
        """SQS queue has different strategies for scanner and TF state."""
        config = IDENTITY_REGISTRY.get("aws_sqs_queue")
        assert config is not None
        assert config["scanner_id"]["strategy"] == "arn_tail"
        assert config["tf_state_id"]["strategy"] == "url_tail"

    def test_asg_uses_regex_for_scanner(self):
        """ASG uses regex strategy for scanner ID."""
        config = IDENTITY_REGISTRY.get("aws_autoscaling_group")
        assert config is not None
        assert config["scanner_id"]["strategy"] == "regex"
        assert "pattern" in config["scanner_id"]
        assert config["tf_state_id"]["strategy"] == "literal"

    def test_ec2_uses_literal(self):
        """EC2 instance uses literal strategy for both."""
        config = IDENTITY_REGISTRY.get("aws_instance")
        assert config is not None
        assert config["scanner_id"]["strategy"] == "literal"
        assert config["tf_state_id"]["strategy"] == "literal"

    def test_all_entries_have_both_strategies(self):
        """All registry entries have both scanner_id and tf_state_id."""
        for resource_type, config in IDENTITY_REGISTRY.items():
            assert "scanner_id" in config, f"{resource_type} missing scanner_id"
            assert "tf_state_id" in config, f"{resource_type} missing tf_state_id"
            assert "strategy" in config["scanner_id"]
            assert "strategy" in config["tf_state_id"]


class TestIdentityResolverStripAccountPrefix:
    """Tests for account prefix stripping."""

    def test_strips_valid_account_prefix(self):
        """Strips account:region: prefix when present."""
        raw_id = "123456789012:us-east-1:vpc-12345"
        assert IdentityResolver.strip_account_prefix(raw_id) == "vpc-12345"

    def test_preserves_non_account_prefix(self):
        """Preserves IDs that don't have account prefix."""
        raw_id = "vpc-12345"
        assert IdentityResolver.strip_account_prefix(raw_id) == "vpc-12345"

    def test_preserves_arn_format(self):
        """Preserves ARN format (first part is not 12-digit account)."""
        arn = "arn:aws:sqs:us-east-1:123456789012:my-queue"
        assert IdentityResolver.strip_account_prefix(arn) == arn

    def test_handles_empty_string(self):
        """Handles empty string."""
        assert IdentityResolver.strip_account_prefix("") == ""

    def test_handles_none(self):
        """Handles None-like empty value."""
        assert IdentityResolver.strip_account_prefix("") == ""

    def test_preserves_colons_in_resource_part(self):
        """Preserves colons in the resource part after stripping prefix."""
        raw_id = "123456789012:us-east-1:some:resource:with:colons"
        assert (
            IdentityResolver.strip_account_prefix(raw_id) == "some:resource:with:colons"
        )


class TestIdentityResolverSafeExecute:
    """Tests for safe execution wrapper."""

    def test_safe_execute_success(self):
        """Safe execute returns result on success."""
        result = IdentityResolver.safe_execute(lambda x, _: x.upper(), "test", None)
        assert result == "TEST"

    def test_safe_execute_catches_exception(self):
        """Safe execute catches exception and returns original."""

        def bad_func(x, _):
            raise ValueError("Intentional error")

        result = IdentityResolver.safe_execute(bad_func, "original", None)
        assert result == "original"

    def test_safe_execute_catches_index_error(self):
        """Safe execute catches index errors."""

        def index_error_func(x, _):
            return x.split("/")[99]  # Out of bounds

        result = IdentityResolver.safe_execute(index_error_func, "a/b/c", None)
        assert result == "a/b/c"


class TestIdentityResolverNormalize:
    """Tests for the normalize method."""

    def test_normalize_scanner_sqs(self):
        """Normalize SQS scanner ID extracts queue name from ARN."""
        arn = "arn:aws:sqs:us-east-1:123456789012:my-queue"
        result = IdentityResolver.normalize(arn, "aws_sqs_queue", "scanner")
        assert result == "my-queue"

    def test_normalize_tf_state_sqs(self):
        """Normalize SQS TF state ID extracts queue name from URL."""
        url = "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue"
        result = IdentityResolver.normalize(url, "aws_sqs_queue", "tf_state")
        assert result == "my-queue"

    def test_normalize_asg_scanner(self):
        """Normalize ASG scanner ID extracts name from ARN."""
        arn = "arn:aws:autoscaling:us-east-1:123:autoScalingGroup:id:autoScalingGroupName/my-asg"
        result = IdentityResolver.normalize(arn, "aws_autoscaling_group", "scanner")
        assert result == "my-asg"

    def test_normalize_asg_tf_state(self):
        """Normalize ASG TF state ID returns as-is (name format)."""
        name = "my-asg"
        result = IdentityResolver.normalize(name, "aws_autoscaling_group", "tf_state")
        assert result == "my-asg"

    def test_normalize_strips_account_prefix_for_scanner(self):
        """Normalize strips account:region prefix for scanner IDs."""
        prefixed = "123456789012:us-east-1:vpc-12345"
        result = IdentityResolver.normalize(prefixed, "aws_vpc", "scanner")
        assert result == "vpc-12345"

    def test_normalize_does_not_strip_prefix_for_tf_state(self):
        """Normalize does not strip prefix for TF state IDs."""
        # TF state shouldn't have account prefix, but verify behavior
        raw = "vpc-12345"
        result = IdentityResolver.normalize(raw, "aws_vpc", "tf_state")
        assert result == "vpc-12345"

    def test_normalize_unknown_type_uses_literal(self):
        """Unknown resource type falls back to literal strategy."""
        value = "some-unknown-value"
        result = IdentityResolver.normalize(value, "aws_unknown_resource", "scanner")
        assert result == "some-unknown-value"

    def test_normalize_empty_value(self):
        """Normalize handles empty values."""
        assert IdentityResolver.normalize("", "aws_vpc", "scanner") == ""


class TestIdentityResolverConvenienceMethods:
    """Tests for convenience methods."""

    def test_normalize_scanner_id(self):
        """Convenience method for scanner ID normalization."""
        arn = "arn:aws:sqs:us-east-1:123456789012:my-queue"
        result = IdentityResolver.normalize_scanner_id(arn, "aws_sqs_queue")
        assert result == "my-queue"

    def test_normalize_tf_state_id(self):
        """Convenience method for TF state ID normalization."""
        url = "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue"
        result = IdentityResolver.normalize_tf_state_id(url, "aws_sqs_queue")
        assert result == "my-queue"


class TestScannerCoverage:
    """Tests for scanner coverage detection."""

    def test_get_scanner_coverage_returns_set(self):
        """get_scanner_coverage returns a set of resource types."""
        coverage = get_scanner_coverage()
        assert isinstance(coverage, set)
        # Should have at least some basic resource types
        assert len(coverage) > 0

    def test_get_scanner_coverage_includes_vpc(self):
        """Scanner coverage includes VPC (basic resource)."""
        coverage = get_scanner_coverage()
        assert "aws_vpc" in coverage

    def test_get_scanner_coverage_includes_new_scanners(self):
        """Scanner coverage includes newly added scanners."""
        coverage = get_scanner_coverage()
        # CloudWatch Log Group scanner was just added
        assert "aws_cloudwatch_log_group" in coverage
        # EIP scanner was just added
        assert "aws_eip" in coverage

    def test_has_scanner_coverage_true(self):
        """has_scanner_coverage returns True for covered types."""
        assert has_scanner_coverage("aws_vpc") is True
        assert has_scanner_coverage("aws_instance") is True

    def test_has_scanner_coverage_false(self):
        """has_scanner_coverage returns False for uncovered types."""
        # Lambda function doesn't have a scanner yet
        assert has_scanner_coverage("aws_lambda_function") is False
        # Completely unknown type
        assert has_scanner_coverage("aws_unknown_resource") is False


class TestIdentityResolverIntegration:
    """Integration tests for identity resolution."""

    def test_sqs_scanner_and_tf_both_resolve_to_same(self):
        """SQS scanner ARN and TF state URL resolve to same canonical ID."""
        scanner_arn = "arn:aws:sqs:us-east-1:123456789012:my-queue"
        tf_url = "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue"

        scanner_canonical = IdentityResolver.normalize_scanner_id(
            scanner_arn, "aws_sqs_queue"
        )
        tf_canonical = IdentityResolver.normalize_tf_state_id(tf_url, "aws_sqs_queue")

        assert scanner_canonical == tf_canonical == "my-queue"

    def test_asg_scanner_and_tf_both_resolve_to_same(self):
        """ASG scanner ARN and TF state name resolve to same canonical ID."""
        scanner_arn = "arn:aws:autoscaling:us-east-1:123:autoScalingGroup:uuid:autoScalingGroupName/my-asg"
        tf_name = "my-asg"

        scanner_canonical = IdentityResolver.normalize_scanner_id(
            scanner_arn, "aws_autoscaling_group"
        )
        tf_canonical = IdentityResolver.normalize_tf_state_id(
            tf_name, "aws_autoscaling_group"
        )

        assert scanner_canonical == tf_canonical == "my-asg"

    def test_account_prefixed_scanner_and_tf_resolve_to_same(self):
        """Account-prefixed scanner ID and TF state resolve to same."""
        # Scanner uses account:region:vpc-xxx format
        scanner_id = "123456789012:us-east-1:vpc-12345"
        # TF state uses vpc-xxx format
        tf_id = "vpc-12345"

        scanner_canonical = IdentityResolver.normalize_scanner_id(scanner_id, "aws_vpc")
        tf_canonical = IdentityResolver.normalize_tf_state_id(tf_id, "aws_vpc")

        assert scanner_canonical == tf_canonical == "vpc-12345"
