"""
AWS Client Configuration for RepliMap.

This module provides standardized botocore.Config settings for all
AWS API clients to ensure:
1. Consistent timeout behavior
2. Coordinated retry behavior with our custom retry decorator
3. Proper error handling for high-concurrency scanning

IMPORTANT: All boto3 clients MUST use BOTO_CONFIG to prevent
"retry storm" behavior where boto3 internal retries compound
with our custom retry decorator.

For high-concurrency scanning (50+ threads), use HIGH_CONCURRENCY_CONFIG
which includes larger connection pools and adaptive retry mode.
"""

from __future__ import annotations

import os
from typing import Literal

from botocore.config import Config

# Timeout configuration (seconds)
CONNECT_TIMEOUT = int(os.environ.get("REPLIMAP_CONNECT_TIMEOUT", "10"))
READ_TIMEOUT = int(os.environ.get("REPLIMAP_READ_TIMEOUT", "30"))

# Default connection pool size
DEFAULT_POOL_SIZE = 10

# High-concurrency pool size (for large account scanning)
HIGH_CONCURRENCY_POOL_SIZE = 50

# Disable boto3 internal retries - we handle retries ourselves
# This prevents "retry storm" where boto3 retries 5x and our decorator
# retries 5x, resulting in up to 25 attempts
BOTO_CONFIG = Config(
    retries={
        "mode": "standard",
        "max_attempts": 1,  # Disable boto3 retries, we handle it ourselves
    },
    connect_timeout=CONNECT_TIMEOUT,
    read_timeout=READ_TIMEOUT,
    # Use signature version 4 for all regions
    signature_version="v4",
)


# High-concurrency config for large AWS accounts
# Uses adaptive retry mode which auto-adjusts request rate based on throttling
# Combined with our custom retry decorator for maximum resilience
HIGH_CONCURRENCY_CONFIG = Config(
    retries={
        "mode": "adaptive",  # Auto-adjusts based on throttling responses
        "max_attempts": 3,  # Light internal retry before our decorator kicks in
    },
    connect_timeout=CONNECT_TIMEOUT,
    read_timeout=READ_TIMEOUT,
    max_pool_connections=HIGH_CONCURRENCY_POOL_SIZE,
    signature_version="v4",
)


def get_boto_config(
    connect_timeout: int | None = None,
    read_timeout: int | None = None,
    max_pool_connections: int | None = None,
    mode: Literal["standard", "high-concurrency"] = "standard",
) -> Config:
    """
    Get a customized botocore Config.

    Use this when you need different timeout values than the defaults,
    but still want to maintain the retry coordination.

    Args:
        connect_timeout: Connection timeout in seconds (default: 10)
        read_timeout: Read timeout in seconds (default: 30)
        max_pool_connections: Max connections in the pool (default: 10)
        mode: Configuration mode:
            - "standard": Disable internal retries, rely on custom decorator
            - "high-concurrency": Use adaptive retry with larger pool

    Returns:
        Configured botocore.Config instance

    Examples:
        # Standard config (default)
        client = session.client("ec2", config=get_boto_config())

        # High-concurrency config for large accounts
        client = session.client("ec2", config=get_boto_config(
            mode="high-concurrency",
            max_pool_connections=100
        ))
    """
    if mode == "high-concurrency":
        return Config(
            retries={
                "mode": "adaptive",
                "max_attempts": 3,
            },
            connect_timeout=connect_timeout or CONNECT_TIMEOUT,
            read_timeout=read_timeout or READ_TIMEOUT,
            max_pool_connections=max_pool_connections or HIGH_CONCURRENCY_POOL_SIZE,
            signature_version="v4",
        )

    # Standard mode - disable internal retries
    config_dict: dict[str, object] = {
        "retries": {
            "mode": "standard",
            "max_attempts": 1,
        },
        "connect_timeout": connect_timeout or CONNECT_TIMEOUT,
        "read_timeout": read_timeout or READ_TIMEOUT,
        "signature_version": "v4",
    }

    if max_pool_connections is not None:
        config_dict["max_pool_connections"] = max_pool_connections

    return Config(**config_dict)
