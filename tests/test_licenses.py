"""Tests for license API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestLicenseEndpoints:
    """Tests for license API."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient) -> None:
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @pytest.mark.asyncio
    async def test_validate_invalid_license(self, client: AsyncClient) -> None:
        """Test validating an invalid license."""
        response = await client.post(
            "/api/v1/licenses/validate",
            json={"license_key": "INVALID-KEY"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["error"] == "invalid_license"

    @pytest.mark.asyncio
    async def test_get_nonexistent_license(self, client: AsyncClient) -> None:
        """Test getting a non-existent license."""
        response = await client.get("/api/v1/licenses/INVALID-KEY")
        assert response.status_code == 404


class TestUsageEndpoints:
    """Tests for usage API."""

    @pytest.mark.asyncio
    async def test_sync_invalid_license(self, client: AsyncClient) -> None:
        """Test syncing usage for invalid license."""
        response = await client.post(
            "/api/v1/usage/sync",
            json={
                "license_key": "INVALID-KEY",
                "machine_id": "test-machine",
                "usage": {"scans_count": 1},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["synced"] is False
        assert data["error"] == "invalid_license"

    @pytest.mark.asyncio
    async def test_check_quota_invalid_license(self, client: AsyncClient) -> None:
        """Test checking quota for invalid license."""
        response = await client.post(
            "/api/v1/usage/check-quota",
            json={
                "license_key": "INVALID-KEY",
                "operation": "scans",
                "amount": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert data["error"] == "invalid_license"
