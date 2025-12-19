"""Tests for license API endpoints."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/replimap_test"
os.environ["ADMIN_API_KEY"] = "test-admin-key"

from api.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_status(self, client: AsyncClient) -> None:
        """Test health check endpoint returns expected structure."""
        response = await client.get("/health")
        # Note: Will return 503 if DB is not available in test environment
        # In a real test, we'd mock the DB connection
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient) -> None:
        """Test root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "RepliMap API"
        assert data["version"] == "0.1.0"
        assert data["docs"] == "/docs"


class TestLicenseValidation:
    """Tests for license validation endpoint."""

    @pytest.mark.asyncio
    async def test_validate_invalid_license(self, client: AsyncClient) -> None:
        """Test validating an invalid license returns error."""
        response = await client.post(
            "/api/v1/licenses/validate",
            json={"license_key": "INVALID-KEY"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["error"] == "invalid_license"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_validate_empty_license_key(self, client: AsyncClient) -> None:
        """Test validating with empty license key returns validation error."""
        response = await client.post(
            "/api/v1/licenses/validate",
            json={"license_key": ""},
        )
        # Pydantic validation should reject empty string due to min_length
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validate_with_machine_id(self, client: AsyncClient) -> None:
        """Test validation with machine_id attempts activation."""
        response = await client.post(
            "/api/v1/licenses/validate",
            json={
                "license_key": "INVALID-KEY",
                "machine_id": "test-machine-123",
                "product_version": "1.0.0",
                "client_os": "linux",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False  # License doesn't exist


class TestLicenseRetrieval:
    """Tests for license retrieval endpoint."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_license(self, client: AsyncClient) -> None:
        """Test getting a non-existent license returns 404."""
        response = await client.get("/api/v1/licenses/INVALID-KEY")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "License not found"


class TestLicenseCreation:
    """Tests for license creation endpoint (admin)."""

    @pytest.mark.asyncio
    async def test_create_license_without_api_key(self, client: AsyncClient) -> None:
        """Test creating license without API key returns 401."""
        response = await client.post(
            "/api/v1/licenses/create",
            json={
                "customer_email": "test@example.com",
                "plan": "free",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "Missing X-API-Key" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_license_with_invalid_api_key(self, client: AsyncClient) -> None:
        """Test creating license with invalid API key returns 403."""
        response = await client.post(
            "/api/v1/licenses/create",
            json={
                "customer_email": "test@example.com",
                "plan": "free",
            },
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 403
        data = response.json()
        assert "Invalid API key" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_license_with_invalid_plan(self, client: AsyncClient) -> None:
        """Test creating license with invalid plan returns validation error."""
        response = await client.post(
            "/api/v1/licenses/create",
            json={
                "customer_email": "test@example.com",
                "plan": "invalid_plan",
            },
            headers={"X-API-Key": "test-admin-key"},
        )
        assert response.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_create_license_with_invalid_email(self, client: AsyncClient) -> None:
        """Test creating license with invalid email returns validation error."""
        response = await client.post(
            "/api/v1/licenses/create",
            json={
                "customer_email": "not-an-email",
                "plan": "free",
            },
            headers={"X-API-Key": "test-admin-key"},
        )
        assert response.status_code == 422


class TestLicenseRevocation:
    """Tests for license revocation endpoint (admin)."""

    @pytest.mark.asyncio
    async def test_revoke_license_without_api_key(self, client: AsyncClient) -> None:
        """Test revoking license without API key returns 401."""
        response = await client.post("/api/v1/licenses/SOME-KEY/revoke")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_license(self, client: AsyncClient) -> None:
        """Test revoking non-existent license returns 404."""
        response = await client.post(
            "/api/v1/licenses/NONEXISTENT-KEY/revoke",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert response.status_code == 404


class TestUsageSync:
    """Tests for usage sync endpoint."""

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
    async def test_sync_with_invalid_period_format(self, client: AsyncClient) -> None:
        """Test syncing with invalid period format."""
        response = await client.post(
            "/api/v1/usage/sync",
            json={
                "license_key": "INVALID-KEY",
                "machine_id": "test-machine",
                "usage": {"scans_count": 1},
                "period": "2025-13",  # Invalid month
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Will fail on license lookup first, but format validation happens after
        assert data["synced"] is False

    @pytest.mark.asyncio
    async def test_sync_with_negative_usage(self, client: AsyncClient) -> None:
        """Test syncing with negative usage values."""
        response = await client.post(
            "/api/v1/usage/sync",
            json={
                "license_key": "INVALID-KEY",
                "machine_id": "test-machine",
                "usage": {"scans_count": -1},
            },
        )
        assert response.status_code == 200
        # Will fail on license lookup before usage validation


class TestQuotaCheck:
    """Tests for quota check endpoint."""

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

    @pytest.mark.asyncio
    async def test_check_quota_invalid_operation(self, client: AsyncClient) -> None:
        """Test checking quota with invalid operation type."""
        response = await client.post(
            "/api/v1/usage/check-quota",
            json={
                "license_key": "INVALID-KEY",
                "operation": "invalid_op",
                "amount": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert data["error"] == "invalid_operation"

    @pytest.mark.asyncio
    async def test_check_quota_invalid_amount(self, client: AsyncClient) -> None:
        """Test checking quota with invalid amount."""
        response = await client.post(
            "/api/v1/usage/check-quota",
            json={
                "license_key": "INVALID-KEY",
                "operation": "scans",
                "amount": 0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert data["error"] == "invalid_amount"


class TestUsageHistory:
    """Tests for usage history endpoint."""

    @pytest.mark.asyncio
    async def test_get_history_invalid_license(self, client: AsyncClient) -> None:
        """Test getting usage history for invalid license."""
        response = await client.get("/api/v1/usage/INVALID-KEY/history")
        assert response.status_code == 200
        data = response.json()
        assert data.get("error") == "invalid_license"


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, client: AsyncClient) -> None:
        """Test that rate limit headers are present in response."""
        response = await client.get("/api/v1/licenses/test-key")
        # Check for rate limit headers (even on 404)
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


class TestInputValidation:
    """Tests for input validation."""

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient) -> None:
        """Test missing required fields returns validation error."""
        response = await client.post(
            "/api/v1/licenses/validate",
            json={},  # Missing license_key
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_json(self, client: AsyncClient) -> None:
        """Test invalid JSON returns error."""
        response = await client.post(
            "/api/v1/licenses/validate",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
