"""Translate domain errors into HTTP response status codes."""

from __future__ import annotations

from fastapi import status

from app.modules.analytics.application.exceptions import UnsupportedInsightsApplication
from app.modules.audit.application.exceptions import AuditEntryNotFound
from app.modules.knowledge_base.application.exceptions import (
    BatchImportCorpusWriteFailed,
    BatchImportFileUnreadable,
    BatchImportPreflightFailed,
    BatchImportTooLarge,
    RecalculationAlreadyRunning,
)
from app.modules.notifications.application.exceptions import NotificationNotFound
from app.modules.ticket_management.application.exceptions import (
    AssigneeNotAuthorized,
    AssigneeNotFound,
    TicketImportRejected,
    TicketNotFound,
)
from app.modules.ticket_management.application.exceptions import AttachmentNotFound as ApplicationAttachmentNotFound
from app.modules.ticket_management.application.exceptions import CommentNotFound as ApplicationCommentNotFound
from app.modules.ticket_management.domain.exceptions import (
    AssigneeUnchanged,
    AttachmentNotFound,
    AttachmentTooLarge,
    ChronologicalOrderViolation,
    CommentNotFound,
    DuplicateAttachment,
    InvalidStatusTransition,
    TicketArchived,
    TicketClosed,
    TicketNotArchived,
    TicketNotAssigned,
    TransferDestinationIsOrigin,
    UnsupportedAttachmentType,
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
    TransferDestinationIsOrigin: status.HTTP_409_CONFLICT,
    AssigneeNotFound: status.HTTP_404_NOT_FOUND,
    AssigneeNotAuthorized: status.HTTP_403_FORBIDDEN,
    AssigneeUnchanged: status.HTTP_409_CONFLICT,
    ChronologicalOrderViolation: status.HTTP_409_CONFLICT,
    ApplicationAttachmentNotFound: status.HTTP_404_NOT_FOUND,
    ApplicationCommentNotFound: status.HTTP_404_NOT_FOUND,
    AttachmentTooLarge: status.HTTP_413_CONTENT_TOO_LARGE,
    UnsupportedAttachmentType: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    AuditEntryNotFound: status.HTTP_404_NOT_FOUND,
    NotificationNotFound: status.HTTP_404_NOT_FOUND,
    UnsupportedInsightsApplication: status.HTTP_400_BAD_REQUEST,
    RecalculationAlreadyRunning: status.HTTP_409_CONFLICT,
    # A rejected import is a well-formed request describing data this module will not accept, which
    # is exactly what 422 is for -- and the same code FastAPI already answers with when a request
    # body fails validation, so a client handles both the same way.
    TicketImportRejected: status.HTTP_422_UNPROCESSABLE_CONTENT,
    BatchImportFileUnreadable: status.HTTP_400_BAD_REQUEST,
    BatchImportTooLarge: status.HTTP_413_CONTENT_TOO_LARGE,
    # Not a 500: the request was valid and this module did its part. What failed is the embedding
    # endpoint or the vector store, which is a dependency being unavailable rather than a defect
    # here, and the distinction is what tells an operator to retry rather than to report a bug.
    BatchImportCorpusWriteFailed: status.HTTP_502_BAD_GATEWAY,
    BatchImportPreflightFailed: status.HTTP_502_BAD_GATEWAY,
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
