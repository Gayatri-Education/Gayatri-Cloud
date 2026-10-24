"""Gayatri Cloud — Application Entrypoint."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_v1_router
from app.core.config import settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("gayatri.cloud.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan setup and teardown handler."""
    logger.info(
        "Starting Gayatri Cloud API [Env: %s, Version: %s]",
        settings.ENVIRONMENT,
        settings.APP_VERSION,
    )
    yield
    logger.info("Shutting down Gayatri Cloud API")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Mount API v1
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
)


@app.middleware("http")
async def correlation_and_security_headers_middleware(request: Request, call_next) -> Response:
    """Injects correlation IDs, tracks request duration, and sets defensive security headers."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.perf_counter()

    # Pass request ID in request state
    request.state.request_id = request_id

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception(
            "Unhandled error processing request [Request-ID: %s]: %s", request_id, str(exc)
        )
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please contact support with the request ID.",
                    "request_id": request_id,
                }
            },
        )

    duration_ms = (time.perf_counter() - start_time) * 1000.0

    # Defensive Security & Diagnostic Headers (OWASP)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
@app.get("/health/live", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check() -> dict[str, str]:
    """Lightweight health probe for container/orchestrator liveness.

    Zero secret exposure, zero internal topology leakage.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/ready", status_code=status.HTTP_200_OK, tags=["Health"])
@app.get("/health/ready", status_code=status.HTTP_200_OK, tags=["Health"])
async def readiness_check() -> dict[str, object]:
    """Readiness probe verifying that dependencies and subsystem configurations are operational."""
    # Subsystem readiness checks can expand with DB and Cache connectivity in later phases
    checks = {
        "api": "ok",
        "environment": settings.ENVIRONMENT,
    }
    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }
