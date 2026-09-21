"""FastAPI application factory.

System endpoints plus the Phase 6 public read API (`/api/v1`). No court
document is fetched and no AI provider is called; the read API serves whatever
the database holds, filtered to the public record.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from ksc_api import __version__
from ksc_api.config import get_settings
from ksc_api.logging_config import configure_logging
from ksc_api.repositories.records import CaseNotConfiguredError
from ksc_api.routers import ai, appeal, ingestion, records, system

MAX_REQUEST_BYTES = 10 * 1024 * 1024


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="KSC Public Record Intelligence API",
        version=__version__,
        description=(
            "Citation-first research API over the public record of KSC-BC-2020-06. "
            "Primary sources, the database, provenance and citations are authoritative; "
            "AI output, when it exists, is analysis only."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(system.router)
    app.include_router(records.router)
    app.include_router(ingestion.router)
    app.include_router(ai.router)
    app.include_router(appeal.router)

    @app.middleware("http")
    async def _security_boundary(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                too_large = int(content_length) > MAX_REQUEST_BYTES
            except ValueError:
                too_large = True
            if too_large:
                return JSONResponse(status_code=413, content={"detail": "request too large"})
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    @app.exception_handler(CaseNotConfiguredError)
    def _case_not_configured(_: Request, exc: CaseNotConfiguredError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": f"case {exc} is not seeded; run ksc-seed"},
        )

    return app


app = create_app()
