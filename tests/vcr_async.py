"""
Async VCR support for aiobotocore/aiohttp.

VCR.py works with aiohttp out of the box, but we need some helpers
for cleaner async test patterns with RepliMap's async scanners.

Usage:
    from tests.vcr_async import async_vcr_cassette, AsyncVCRTestCase

    @async_vcr_cassette('my_test')
    async def test_async_function():
        async with get_client() as client:
            result = await client.describe_instances()

    class TestMyScanner(AsyncVCRTestCase):
        cassette_name = 'my_scanner'

        async def test_scan(self):
            # VCR cassette is automatically applied
            pass
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any

from tests.conftest import VCR_AVAILABLE, vcr_config

if TYPE_CHECKING:
    from collections.abc import Coroutine


def async_vcr_cassette(cassette_name: str) -> Callable[..., Any]:
    """
    Decorator for async tests with VCR cassettes.

    Wraps an async test function to run inside a VCR cassette context.
    The cassette will record/replay HTTP calls made during the test.

    Args:
        cassette_name: Name of the cassette file (without .yaml extension)

    Usage:
        @async_vcr_cassette('ec2_describe_instances')
        async def test_ec2_scan():
            async with get_client() as client:
                result = await client.describe_instances()
                assert 'Reservations' in result

    Note:
        Works with aiobotocore and aiohttp. The cassette is loaded
        synchronously before running the async function.
    """
    if not VCR_AVAILABLE or vcr_config is None:
        # Return a no-op decorator if VCR not available
        def noop_decorator(
            func: Callable[..., Coroutine[Any, Any, Any]],
        ) -> Callable[..., Any]:
            return func

        return noop_decorator

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cassette_file = (
                f"{cassette_name}.yaml"
                if not cassette_name.endswith(".yaml")
                else cassette_name
            )
            with vcr_config.use_cassette(cassette_file):
                # Get or create event loop and run the coroutine
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                return loop.run_until_complete(func(*args, **kwargs))

        return wrapper

    return decorator


class AsyncVCRTestCase:
    """
    Base class for async VCR tests.

    Provides automatic VCR cassette management for test classes.
    Each test method gets its own cassette named:
        {cassette_name}_{method_name}.yaml

    Usage:
        class TestEC2Scanner(AsyncVCRTestCase):
            cassette_name = 'ec2_scanner'

            async def test_scan_instances(self):
                # Uses cassette: ec2_scanner_test_scan_instances.yaml
                scanner = EC2Scanner()
                results = await scanner.scan()
                assert len(results) > 0

            async def test_empty_account(self):
                # Uses cassette: ec2_scanner_test_empty_account.yaml
                pass

    Attributes:
        cassette_name: Base name for cassettes. If None, uses class name.
    """

    cassette_name: str | None = None
    _vcr_context: Any = None

    def setup_method(self, method: Callable[..., Any]) -> None:
        """Set up VCR cassette for each test method."""
        if not VCR_AVAILABLE or vcr_config is None:
            return

        # Build cassette name from class name and method name
        name = self.cassette_name or self.__class__.__name__
        cassette_file = f"{name}_{method.__name__}.yaml"

        self._vcr_context = vcr_config.use_cassette(cassette_file)
        self._vcr_context.__enter__()

    def teardown_method(self, method: Callable[..., Any]) -> None:
        """Tear down VCR cassette."""
        if hasattr(self, "_vcr_context") and self._vcr_context is not None:
            self._vcr_context.__exit__(None, None, None)
            self._vcr_context = None


# ═══════════════════════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════════════════════


def get_cassette_path(name: str) -> str:
    """
    Get the full path to a cassette file.

    Args:
        name: Cassette name (with or without .yaml extension)

    Returns:
        Full path to the cassette file
    """
    from tests.conftest import CASSETTES_DIR

    if not name.endswith(".yaml"):
        name = f"{name}.yaml"
    return str(CASSETTES_DIR / name)


def cassette_exists(name: str) -> bool:
    """
    Check if a cassette file exists.

    Args:
        name: Cassette name (with or without .yaml extension)

    Returns:
        True if the cassette exists
    """
    from pathlib import Path

    return Path(get_cassette_path(name)).exists()


__all__ = [
    "AsyncVCRTestCase",
    "async_vcr_cassette",
    "cassette_exists",
    "get_cassette_path",
]
