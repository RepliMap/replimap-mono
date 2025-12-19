"""FastAPI application entry point."""

import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from config import get_settings
from database import get_db, init_db

from .licenses import router as licenses_router
from .stripe_webhook import router as stripe_webhook_router
from .usage import router as usage_router

logger = logging.getLogger(__name__)
settings = get_settings()

# Default weak secrets that must be changed in production
WEAK_SECRETS = {"change-me-in-production", "dev-secret-change-in-production", "dev-signing-key"}


def validate_production_secrets() -> None:
    """Validate that secrets are not using weak defaults in production."""
    # Only enforce in production (not in dev/test)
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env not in ("production", "prod"):
        return

    errors = []
    if settings.jwt_secret in WEAK_SECRETS:
        errors.append("JWT_SECRET is using a weak default value")
    if settings.license_signing_key in WEAK_SECRETS:
        errors.append("LICENSE_SIGNING_KEY is using a weak default value")

    if errors:
        for error in errors:
            logger.critical(f"Security configuration error: {error}")
        raise RuntimeError(
            "Cannot start in production mode with weak secrets. "
            f"Please configure: {', '.join(errors)}"
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.

    NOTE: This implementation uses in-memory storage and is suitable for
    single-instance deployments. For production with multiple instances,
    use Redis-backed rate limiting (e.g., slowapi with Redis backend).
    """

    def __init__(self, app: FastAPI, requests_limit: int, window_seconds: int) -> None:
        super().__init__(app)
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        # Track requests per IP: {ip: [(timestamp, count), ...]}
        self.request_counts: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies."""
        # Check for forwarded header (behind reverse proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _clean_old_requests(self, ip: str, now: float) -> None:
        """Remove request timestamps older than the window."""
        cutoff = now - self.window_seconds
        self.request_counts[ip] = [
            ts for ts in self.request_counts[ip] if ts > cutoff
        ]

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()

        # Clean old requests
        self._clean_old_requests(client_ip, now)

        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_limit:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content='{"detail": "Rate limit exceeded. Please try again later."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.requests_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + self.window_seconds)),
                },
            )

        # Record this request
        self.request_counts[client_ip].append(now)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = self.requests_limit - len(self.request_counts[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(now + self.window_seconds))

        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup validations
    validate_production_secrets()

    # Initialize database
    await init_db()

    logger.info("RepliMap API started successfully")
    yield

    # Shutdown
    logger.info("RepliMap API shutting down")


app = FastAPI(
    title="RepliMap API",
    description="License validation and usage tracking API for RepliMap",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting middleware (add first so it wraps all requests)
app.add_middleware(
    RateLimitMiddleware,
    requests_limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(licenses_router, prefix="/api/v1/licenses", tags=["licenses"])
app.include_router(usage_router, prefix="/api/v1/usage", tags=["usage"])
app.include_router(stripe_webhook_router, prefix="/api/v1/stripe", tags=["stripe"])


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint.

    Verifies that the API is running and can connect to the database.
    """
    health_status: dict[str, Any] = {"status": "healthy", "checks": {}}

    # Check database connectivity
    try:
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "connected"
            break
    except Exception as e:
        logger.error(f"Health check failed - database error: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = "disconnected"
        raise HTTPException(status_code=503, detail=health_status)

    return health_status


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "name": "RepliMap API",
        "version": "0.1.0",
        "docs": "/docs",
    }
