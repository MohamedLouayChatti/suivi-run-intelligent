"""Global FastAPI exception handlers for the API boundary."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.exceptions.mapper import get_status_code
from app.shared.exceptions.exceptions import DomainError


logger = logging.getLogger(__name__)


async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    """Expose safe, client-facing messages for known domain errors."""

    return JSONResponse(
        status_code=get_status_code(exc),
        content={"detail": str(exc)},
    )


async def unexpected_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Log unexpected failures without exposing implementation details."""

    logger.exception("Unhandled exception while processing an API request", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error."},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register the API's centralized exception translation handlers."""

    app.add_exception_handler(DomainError, domain_error_handler) # type: ignore[arg-type]
    app.add_exception_handler(Exception, unexpected_exception_handler)
