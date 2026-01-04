"""
Pytest configuration and fixtures for RepliMap tests.

VCR.py Integration:
    This module provides VCR.py configuration for recording and replaying
    AWS API responses. This enables:
    - Offline testing without AWS credentials
    - Deterministic tests (same response every time)
    - Fast CI/CD (no network calls)

Usage:
    @pytest.mark.vcr
    def test_something():
        # Make AWS calls - will be recorded/replayed
        pass

    # Or with explicit cassette:
    @use_cassette('my_cassette')
    def test_something_else():
        pass
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

# VCR.py imports - optional dependency
try:
    import vcr
    from vcr.cassette import Cassette

    VCR_AVAILABLE = True
except ImportError:
    VCR_AVAILABLE = False
    vcr = None  # type: ignore[assignment]


# ═══════════════════════════════════════════════════════════════════════════════
# VCR.py Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Cassette storage directory
CASSETTES_DIR = Path(__file__).parent / "cassettes"


def sanitize_response(response: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize sensitive data from recorded responses.

    This runs BEFORE saving cassettes to disk, ensuring no secrets
    are committed to version control.

    Args:
        response: VCR response dictionary

    Returns:
        Sanitized response
    """
    body = response.get("body", {}).get("string")
    if not body:
        return response

    # Decode if bytes
    if isinstance(body, bytes):
        try:
            body = body.decode("utf-8")
        except UnicodeDecodeError:
            return response

    # Sanitize AWS account IDs (12-digit numbers in specific contexts)
    body = re.sub(r"(\b\d{12}\b)", "123456789012", body)

    # Sanitize ARNs (replace account ID portion)
    body = re.sub(
        r"(arn:aws:[a-z0-9-]+:[a-z0-9-]*):\d{12}:",
        r"\1:123456789012:",
        body,
    )

    # Sanitize access keys
    body = re.sub(r"AKIA[A-Z0-9]{16}", "AKIAIOSFODNN7EXAMPLE", body)

    # Re-encode if originally bytes
    if isinstance(response.get("body", {}).get("string"), bytes):
        body = body.encode("utf-8")

    response["body"]["string"] = body
    return response


def create_vcr_config() -> "vcr.VCR | None":
    """
    Create VCR configuration for AWS API recording.

    Returns:
        Configured VCR instance, or None if vcrpy not installed
    """
    if not VCR_AVAILABLE:
        return None

    # Ensure cassettes directory exists
    CASSETTES_DIR.mkdir(exist_ok=True)

    return vcr.VCR(
        cassette_library_dir=str(CASSETTES_DIR),
        record_mode="once",  # Record once, then replay
        match_on=[
            "method",
            "scheme",
            "host",
            "port",
            "path",
            "query",
        ],
        # Filter sensitive headers (never recorded)
        filter_headers=[
            "authorization",
            "x-amz-security-token",
            "x-amz-date",
            "x-amz-content-sha256",
            "x-amzn-requestid",
        ],
        # Filter sensitive POST data
        filter_post_data_parameters=[
            "credentials",
            "X-Amz-Credential",
            "X-Amz-Signature",
        ],
        # Decode compressed responses for readability
        decode_compressed_response=True,
        # Sanitize responses before recording
        before_record_response=sanitize_response,
    )


# Global VCR instance
vcr_config = create_vcr_config()


# ═══════════════════════════════════════════════════════════════════════════════
# VCR Fixtures and Decorators
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def vcr_cassette(request: pytest.FixtureRequest) -> "Cassette | None":
    """
    Fixture to use VCR cassette for a test.

    The cassette name is derived from the test name.

    Usage:
        def test_something(vcr_cassette):
            with vcr_cassette:
                # Make AWS calls
                pass
    """
    if not VCR_AVAILABLE or vcr_config is None:
        pytest.skip("VCR.py not installed")
        return None

    cassette_name = f"{request.node.name}.yaml"
    return vcr_config.use_cassette(cassette_name)


def use_cassette(name: str | None = None) -> Any:
    """
    Decorator to use VCR cassette for a test.

    Args:
        name: Cassette name (without .yaml extension).
              If None, uses the function name.

    Usage:
        @use_cassette('ec2_describe_instances')
        def test_ec2_scan():
            ...

        @use_cassette()  # Uses function name
        def test_s3_list():
            ...
    """
    if not VCR_AVAILABLE or vcr_config is None:

        def noop_decorator(func: Any) -> Any:
            return func

        return noop_decorator

    def decorator(func: Any) -> Any:
        cassette_name = name or func.__name__
        if not cassette_name.endswith(".yaml"):
            cassette_name = f"{cassette_name}.yaml"
        return vcr_config.use_cassette(cassette_name)(func)

    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# Standard Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def disable_dev_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Disable dev mode for all tests by default.

    Dev mode (REPLIMAP_DEV_MODE) bypasses license restrictions and returns
    ENTERPRISE plan unconditionally. This must be disabled during tests
    to properly verify licensing behavior.

    Tests that specifically need dev mode (like TestDevMode) can use
    monkeypatch to enable it, which will override this fixture.
    """
    monkeypatch.delenv("REPLIMAP_DEV_MODE", raising=False)


@pytest.fixture(autouse=True)
def disable_colors(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Disable Rich/Typer colors for all tests.

    ANSI color codes in CLI output can cause string assertions to fail
    because the escape codes split the text. Setting NO_COLOR and TERM=dumb
    ensures plain text output for reliable test assertions.
    """
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("TERM", "dumb")


# ═══════════════════════════════════════════════════════════════════════════════
# Exports
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "CASSETTES_DIR",
    "VCR_AVAILABLE",
    "create_vcr_config",
    "sanitize_response",
    "use_cassette",
    "vcr_cassette",
    "vcr_config",
]
