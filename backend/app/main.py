"""
EcoTracker — FastAPI application entry point.

Architecture:
  - SecurityHeadersMiddleware: OWASP security headers on every response
  - CORSMiddleware: Restricted to localhost in development
  - slowapi rate limiting: Per-IP request throttling
  - Router mounts: /api/health, /api/calculate, /api/insights, /api/entries
  - SPA fallback: Serves React build for all non-API paths
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings, validate_config
from app.core.rate_limit import limiter
from app.core.security import SecurityHeadersMiddleware
from app.routes import calculate, entries, health, insights


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler â€” validate config and configure logging on startup."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s â€” %(message)s",
    )
    _log = logging.getLogger(__name__)

    # Validate environment configuration and log warnings for missing credentials
    validate_config(settings)

    _log.info(
        "EcoTracker starting up (env=%s, openrouter=%s, supabase=%s)",
        settings.ENVIRONMENT,
        settings.ai_enabled,
        settings.db_enabled,
    )
    yield
    logging.getLogger(__name__).info("EcoTracker shutting down")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="EcoTracker",
    description=(
        "Understand, track, and reduce your personal carbon footprint "
        "with AI-powered insights via OpenRouter."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware (order matters â€” outer middleware wraps inner)
# ---------------------------------------------------------------------------

# 1. Security headers (outermost â€” applied to every response)
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS â€” allow the Vite dev server in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    max_age=3600,
)

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, cast(Any, _rate_limit_exceeded_handler))

# ---------------------------------------------------------------------------
# API Routers
# ---------------------------------------------------------------------------
app.include_router(health.router, prefix="/api")
app.include_router(calculate.router, prefix="/api")
app.include_router(insights.router, prefix="/api")
app.include_router(entries.router, prefix="/api")

# ---------------------------------------------------------------------------
# Serve compiled React SPA (production only â€” frontend build must exist)
# ---------------------------------------------------------------------------
_static_path = os.path.join(os.path.dirname(__file__), "..", "static")
_assets_path = os.path.join(_static_path, "assets")

if os.path.isdir(_assets_path):
    app.mount("/assets", StaticFiles(directory=_assets_path), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        """Fall-through route: serve the React SPA index.html for all non-API paths."""
        return FileResponse(os.path.join(_static_path, "index.html"))
