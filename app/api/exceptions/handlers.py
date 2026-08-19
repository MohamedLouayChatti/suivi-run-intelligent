"""Global FastAPI exception handlers for the API boundary."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.exceptions.mapper import get_status_code
from app.modules.knowledge_base.api.schemas.batch_import import BatchImportRejectedResponse
from app.modules.knowledge_base.application.exceptions import BatchImportError
from app.modules.ticket_management.application.exceptions import TicketImportRejected
from app.shared.exceptions.application_exceptions import ApplicationError
from app.shared.exceptions.domain_exceptions import DomainError


logger = logging.getLogger(__name__)


async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    """Expose safe, client-facing messages for known domain errors."""

    return JSONResponse(
        status_code=get_status_code(exc),
        content={"detail": type(exc).__name__},
    )

async def application_error_handler(_: Request, exc: ApplicationError) -> JSONResponse:
    return JSONResponse(
        status_code=get_status_code(exc),
        content={"detail": type(exc).__name__},
    )

async def ticket_import_rejected_handler(_: Request, exc: TicketImportRejected) -> JSONResponse:
    """Answers a rejected batch import with every problem found in the file.

    The only handler here that returns more than a type name, because it is the only error whose
    reader has to act on the specifics: an import is rejected as a whole, so the response is what
    an operator edits their file from. `detail` keeps the type name every other error answers with,
    and the rest is added alongside it rather than in place of it.
    """

    return JSONResponse(
        status_code=get_status_code(exc),
        content=BatchImportRejectedResponse.from_exception(exc).model_dump(),
    )


async def batch_import_error_handler(_: Request, exc: BatchImportError) -> JSONResponse:
    """Batch import failures carry a sentence explaining what to do next -- whether the file can
    simply be uploaded again, or whether something was left behind that a backfill has to repair.
    Answering with the type name alone, as the generic handler does, would throw exactly that
    away."""

    return JSONResponse(
        status_code=get_status_code(exc),
        content={"detail": type(exc).__name__, "message": str(exc)},
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
    app.add_exception_handler(ApplicationError, application_error_handler) # type: ignore[arg-type]
    # Registered after the ApplicationError base they inherit from: Starlette resolves a handler by
    # walking the exception's own class hierarchy, so the more specific registration is the one
    # these two reach.
    app.add_exception_handler(TicketImportRejected, ticket_import_rejected_handler) # type: ignore[arg-type]
    app.add_exception_handler(BatchImportError, batch_import_error_handler) # type: ignore[arg-type]
    app.add_exception_handler(Exception, unexpected_exception_handler)
