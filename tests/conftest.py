"""
Pytest configuration and fixtures for RepliMap tests.
"""

import pytest


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
