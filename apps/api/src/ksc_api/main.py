"""FastAPI application factory.

Phase 4 scope: system endpoints only. No court documents are fetched, parsed
or served, and no AI provider is called.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ksc_api import __version__
from ksc_api.config import get_settings
from ksc_api.logging_config import configure_logging
from ksc_api.routers import system


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
    return app


app = create_app()
