"""
Tests for AWS client configuration module.

Verifies boto3 config settings for standard and high-concurrency modes.
"""

from __future__ import annotations

from replimap.core.aws_config import (
    BOTO_CONFIG,
    CONNECT_TIMEOUT,
    DEFAULT_POOL_SIZE,
    HIGH_CONCURRENCY_CONFIG,
    HIGH_CONCURRENCY_POOL_SIZE,
    READ_TIMEOUT,
    get_boto_config,
)


class TestBotoConfigConstants:
    """Test configuration constants."""

    def test_default_timeouts(self) -> None:
        """Default timeouts are reasonable."""
        assert CONNECT_TIMEOUT == 10
        assert READ_TIMEOUT == 30

    def test_pool_sizes(self) -> None:
        """Pool sizes are configured."""
        assert DEFAULT_POOL_SIZE == 10
        assert HIGH_CONCURRENCY_POOL_SIZE == 50


class TestStandardBotoConfig:
    """Test the standard BOTO_CONFIG."""

    def test_disables_internal_retries(self) -> None:
        """Standard config disables boto3 internal retries."""
        assert BOTO_CONFIG.retries["max_attempts"] == 1

    def test_uses_standard_mode(self) -> None:
        """Standard config uses standard retry mode."""
        assert BOTO_CONFIG.retries["mode"] == "standard"

    def test_has_correct_timeouts(self) -> None:
        """Standard config has correct timeouts."""
        assert BOTO_CONFIG.connect_timeout == CONNECT_TIMEOUT
        assert BOTO_CONFIG.read_timeout == READ_TIMEOUT

    def test_uses_signature_v4(self) -> None:
        """Standard config uses signature version 4."""
        assert BOTO_CONFIG.signature_version == "v4"


class TestHighConcurrencyConfig:
    """Test the HIGH_CONCURRENCY_CONFIG."""

    def test_uses_adaptive_mode(self) -> None:
        """High-concurrency config uses adaptive retry mode."""
        assert HIGH_CONCURRENCY_CONFIG.retries["mode"] == "adaptive"

    def test_has_light_retries(self) -> None:
        """High-concurrency config has light internal retries."""
        # 3 attempts as first-line defense before custom decorator
        assert HIGH_CONCURRENCY_CONFIG.retries["max_attempts"] == 3

    def test_has_larger_pool(self) -> None:
        """High-concurrency config has larger connection pool."""
        assert (
            HIGH_CONCURRENCY_CONFIG.max_pool_connections == HIGH_CONCURRENCY_POOL_SIZE
        )

    def test_has_correct_timeouts(self) -> None:
        """High-concurrency config has correct timeouts."""
        assert HIGH_CONCURRENCY_CONFIG.connect_timeout == CONNECT_TIMEOUT
        assert HIGH_CONCURRENCY_CONFIG.read_timeout == READ_TIMEOUT

    def test_uses_signature_v4(self) -> None:
        """High-concurrency config uses signature version 4."""
        assert HIGH_CONCURRENCY_CONFIG.signature_version == "v4"


class TestGetBotoConfig:
    """Test the get_boto_config() function."""

    def test_default_mode_is_standard(self) -> None:
        """Default mode is standard with disabled retries."""
        config = get_boto_config()
        assert config.retries["max_attempts"] == 1
        assert config.retries["mode"] == "standard"

    def test_standard_mode_explicit(self) -> None:
        """Explicit standard mode disables retries."""
        config = get_boto_config(mode="standard")
        assert config.retries["max_attempts"] == 1
        assert config.retries["mode"] == "standard"

    def test_high_concurrency_mode(self) -> None:
        """High-concurrency mode uses adaptive retries."""
        config = get_boto_config(mode="high-concurrency")
        assert config.retries["mode"] == "adaptive"
        assert config.retries["max_attempts"] == 3
        assert config.max_pool_connections == HIGH_CONCURRENCY_POOL_SIZE

    def test_custom_timeouts(self) -> None:
        """Custom timeouts are applied."""
        config = get_boto_config(connect_timeout=5, read_timeout=15)
        assert config.connect_timeout == 5
        assert config.read_timeout == 15

    def test_custom_pool_connections_standard(self) -> None:
        """Custom pool connections work in standard mode."""
        config = get_boto_config(max_pool_connections=25)
        assert config.max_pool_connections == 25

    def test_custom_pool_connections_high_concurrency(self) -> None:
        """Custom pool connections override high-concurrency default."""
        config = get_boto_config(mode="high-concurrency", max_pool_connections=100)
        assert config.max_pool_connections == 100

    def test_all_configs_use_signature_v4(self) -> None:
        """All config modes use signature version 4."""
        standard = get_boto_config(mode="standard")
        high_conc = get_boto_config(mode="high-concurrency")

        assert standard.signature_version == "v4"
        assert high_conc.signature_version == "v4"


class TestRetryStrategyDocumentation:
    """Test that retry strategy is correctly documented in config behavior."""

    def test_standard_mode_for_custom_retry_decorator(self) -> None:
        """Standard mode is designed for use with custom retry decorator.

        The custom retry decorator in replimap/core/retry.py handles retries
        with exponential backoff. Setting max_attempts=1 prevents "retry storm"
        where boto3 retries compound with custom decorator retries.
        """
        config = get_boto_config(mode="standard")
        # Only 1 attempt means boto3 won't retry - our decorator handles it
        assert config.retries["max_attempts"] == 1

    def test_high_concurrency_mode_for_large_scans(self) -> None:
        """High-concurrency mode is optimized for large AWS account scanning.

        Uses adaptive retry which auto-adjusts request rate based on throttling
        responses. The 3 max_attempts provides first-line defense before
        the custom retry decorator kicks in for more severe throttling.
        """
        config = get_boto_config(mode="high-concurrency")
        # Adaptive mode auto-adjusts based on throttling
        assert config.retries["mode"] == "adaptive"
        # Light retries as first defense
        assert config.retries["max_attempts"] == 3
        # Larger pool for concurrent requests
        assert config.max_pool_connections >= 50
