"""Translate domain errors into HTTP response status codes."""

from __future__ import annotations

from fastapi import status

from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.domain.exceptions import (
    AttachmentNotFound,
    CommentNotFound,
    DuplicateAttachment,
    InvalidStatusTransition,
    TicketArchived,
    TicketClosed,
    TicketNotArchived,
    TicketNotAssigned,
)
from app.shared.exceptions.domain_exceptions import DomainError
from app.shared.exceptions.application_exceptions import ApplicationError



EXCEPTION_STATUS_CODES: dict[type[DomainError | ApplicationError], int] = {
    InvalidStatusTransition: status.HTTP_409_CONFLICT,
    TicketNotAssigned: status.HTTP_409_CONFLICT,
    TicketClosed: status.HTTP_409_CONFLICT,
    TicketArchived: status.HTTP_409_CONFLICT,
    TicketNotArchived: status.HTTP_409_CONFLICT,
    DuplicateAttachment: status.HTTP_409_CONFLICT,
    CommentNotFound: status.HTTP_404_NOT_FOUND,
    AttachmentNotFound: status.HTTP_404_NOT_FOUND,
    TicketNotFound: status.HTTP_404_NOT_FOUND,
}


def get_status_code(exc: DomainError | ApplicationError) -> int:
    """Return the HTTP status code configured for a domain error.

    Future modules extend ``EXCEPTION_STATUS_CODES`` with their own error types.
    Domain errors without an explicit mapping return HTTP 400.
    """

    for error_type in type(exc).__mro__:
        status_code = EXCEPTION_STATUS_CODES.get(error_type)
        if status_code is not None:
            return status_code

    return status.HTTP_400_BAD_REQUEST
