"""Nexlayer application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from nexlayer.api.middleware import RateLimitMiddleware, RequestTracingMiddleware
from nexlayer.api.routes import router
from nexlayer.config.settings import get_settings
from nexlayer.core.logging import setup_logging
from nexlayer.telemetry.setup import setup_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hooks."""
    settings = get_settings()
    setup_logging(settings.log_level)
    setup_telemetry()

    # Optionally initialise database tables in dev
    if settings.app_env in ("development", "test"):
        try:
            from nexlayer.database.session import init_db

            await init_db()
        except Exception:
            pass  # DB may not be available in dev/test without Docker

    yield

    # Shutdown
    from nexlayer.database.session import close_db

    await close_db()


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    openapi_tags = [
        {
            "name": "ai",
            "description": "AI gateway operations. Send prompts to AI providers with policy enforcement.",
        },
        {
            "name": "auth",
            "description": "Authentication endpoints for obtaining tokens (dev/test only).",
        },
        {
            "name": "system",
            "description": "System health and status endpoints.",
        },
    ]

    app = FastAPI(
        title="Nexlayer AI Gateway",
        description=(
            "Secure AI Integration Gateway MVP.\n\n"
            "## Authentication\n\n"
            "Use the **Authorize** button above to authenticate with either:\n"
            "- **JWT Bearer Token**: Obtain from `POST /v1/auth/token` (dev/test only)\n"
            "- **API Key**: Use a pre-configured API key in the `X-API-Key` header\n"
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        openapi_tags=openapi_tags,
        swagger_ui_parameters={
            "persistAuthorization": True,
            "filter": True,
        },
    )

    # Middleware (applied bottom-up: tracing wraps rate-limit)
    app.add_middleware(RequestTracingMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Routes
    app.include_router(router)

    return app


# Default application instance used by `uvicorn nexlayer.main:app`
app = create_app()
