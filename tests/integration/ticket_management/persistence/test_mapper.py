"""
Integration tests for the Ticket Management persistence mapper.

These tests are purely in-memory (no database required).  They verify that
every mapper function preserves all field values across conversions, that
nested objects are handled correctly, and that no information is lost during
round-trips.

Domain → ORM → Domain round-trips are the primary assertion pattern.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.entities.comment import Comment
from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.infrastructure.persistence import mapper
from app.modules.ticket_management.infrastructure.persistence.models.attachment_model import (
    AttachmentModel,
)
from app.modules.ticket_management.infrastructure.persistence.models.comment_model import (
    CommentModel,
)
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import (
    TicketModel,
)

# Reuse the domain test factories — no duplication.
from tests.unit.ticket_management.domain.factories import (
    make_attachment,
    make_comment,
    make_ticket,
    BASE_TIME,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# ticket_to_model
# ---------------------------------------------------------------------------


class TestTicketToModel:
    def test_scalar_fields_are_preserved(self):
        # Arrange
        ticket_id = uuid4()
        assignee_id = uuid4()
        ticket = Ticket(
            id=ticket_id,
            title="DB Connection Pool Exhausted",
            description="All connections in use during peak traffic.",
            application=Application.APP_2,
            status=Status.IN_PROGRESS,
            priority=Priority.HIGH,
            assignee_id=assignee_id,
            created_at=BASE_TIME,
            updated_at=BASE_TIME,
            pending_reason="Waiting for infra team",
            resolution_notes=None,
            archived_at=None,
        )

        # Act
        model = mapper.ticket_to_model(ticket)

        # Assert
        assert model.id == ticket_id
        assert model.title == "DB Connection Pool Exhausted"
        assert model.description == "All connections in use during peak traffic."
        assert model.application == Application.APP_2
        assert model.status == Status.IN_PROGRESS
        assert model.priority == Priority.HIGH
        assert model.assignee_id == assignee_id
        assert model.created_at == BASE_TIME
        assert model.updated_at == BASE_TIME
        assert model.pending_reason == "Waiting for infra team"
        assert model.resolution_notes is None
        assert model.archived_at is None

    def test_empty_collections_produce_empty_lists(self):
        # Arrange
        ticket = make_ticket()

        # Act
        model = mapper.ticket_to_model(ticket)

        # Assert
        assert model.comments == []
        assert model.attachments == []

    def test_comments_are_mapped(self):
        # Arrange
        comment = make_comment()
        ticket = make_ticket()
        ticket.comments.append(comment)

        # Act
        model = mapper.ticket_to_model(ticket)

        # Assert
        assert len(model.comments) == 1
        assert model.comments[0].id == comment.id
        assert model.comments[0].content == comment.content
        assert model.comments[0].author_id == comment.author_id

    def test_ticket_attachments_are_mapped(self):
        # Arrange
        attachment = make_attachment()
        ticket = make_ticket()
        ticket.attachments.append(attachment)

        # Act
        model = mapper.ticket_to_model(ticket)

        # Assert
        assert len(model.attachments) == 1
        assert model.attachments[0].id == attachment.id
        assert model.attachments[0].filename == attachment.filename

    def test_archived_at_is_preserved(self):
        # Arrange
        archived_at = BASE_TIME
        ticket = make_ticket()
        ticket.archived_at = archived_at

        # Act
        model = mapper.ticket_to_model(ticket)

        # Assert
        assert model.archived_at == archived_at


# ---------------------------------------------------------------------------
# ticket_model_to_domain
# ---------------------------------------------------------------------------


class TestTicketModelToDomain:
    def _make_model(self, **overrides) -> TicketModel:
        defaults = dict(
            id=uuid4(),
            title="Timeout on auth service",
            description="JWT validation times out under load.",
            application=Application.APP_1,
            status=Status.OPEN,
            priority=Priority.MEDIUM,
            assignee_id=None,
            created_at=BASE_TIME,
            updated_at=BASE_TIME,
            resolved_at=None,
            closed_at=None,
            pending_reason=None,
            resolution_notes=None,
            archived_at=None,
        )
        defaults.update(overrides)
        model = TicketModel(**defaults)
        model.comments = []
        model.attachments = []
        return model

    def test_scalar_fields_are_preserved(self):
        # Arrange
        ticket_id = uuid4()
        assignee_id = uuid4()
        model = self._make_model(id=ticket_id, assignee_id=assignee_id, priority=Priority.CRITICAL)

        # Act
        ticket = mapper.ticket_model_to_domain(model)

        # Assert
        assert ticket.id == ticket_id
        assert ticket.assignee_id == assignee_id
        assert ticket.priority == Priority.CRITICAL

    def test_empty_collections_produce_empty_lists(self):
        # Arrange
        model = self._make_model()

        # Act
        ticket = mapper.ticket_model_to_domain(model)

        # Assert
        assert ticket.comments == []
        assert ticket.attachments == []

    def test_archived_at_is_preserved(self):
        # Arrange
        model = self._make_model(archived_at=BASE_TIME)

        # Act
        ticket = mapper.ticket_model_to_domain(model)

        # Assert
        assert ticket.archived_at == BASE_TIME

    def test_nullable_timestamp_fields_survive_as_none(self):
        # Arrange
        model = self._make_model(resolved_at=None, closed_at=None)

        # Act
        ticket = mapper.ticket_model_to_domain(model)

        # Assert
        assert ticket.resolved_at is None
        assert ticket.closed_at is None


# ---------------------------------------------------------------------------
# Round-trip: Domain → Model → Domain
# ---------------------------------------------------------------------------


class TestTicketRoundTrip:
    def test_basic_ticket_round_trip(self):
        # Arrange
        original = make_ticket()

        # Act
        model = mapper.ticket_to_model(original)
        reconstructed = mapper.ticket_model_to_domain(model)

        # Assert
        assert reconstructed.id == original.id
        assert reconstructed.title == original.title
        assert reconstructed.description == original.description
        assert reconstructed.status == original.status
        assert reconstructed.priority == original.priority
        assert reconstructed.application == original.application
        assert reconstructed.assignee_id == original.assignee_id
        assert reconstructed.created_at == original.created_at
        assert reconstructed.updated_at == original.updated_at
        assert reconstructed.archived_at == original.archived_at

    def test_ticket_with_comment_round_trip(self):
        # Arrange
        ticket = make_ticket()
        comment = make_comment()
        ticket.comments.append(comment)

        # Act
        model = mapper.ticket_to_model(ticket)
        reconstructed = mapper.ticket_model_to_domain(model)

        # Assert
        assert len(reconstructed.comments) == 1
        rc = reconstructed.comments[0]
        assert rc.id == comment.id
        assert rc.author_id == comment.author_id
        assert rc.content == comment.content
        assert rc.created_at == comment.created_at
        assert rc.edited_at == comment.edited_at
        assert rc.deleted_at == comment.deleted_at

    def test_ticket_with_direct_attachment_round_trip(self):
        # Arrange
        ticket = make_ticket()
        attachment = make_attachment()
        ticket.attachments.append(attachment)

        # Act
        model = mapper.ticket_to_model(ticket)
        reconstructed = mapper.ticket_model_to_domain(model)

        # Assert
        assert len(reconstructed.attachments) == 1
        ra = reconstructed.attachments[0]
        assert ra.id == attachment.id
        assert ra.filename == attachment.filename
        assert ra.content_type == attachment.content_type
        assert ra.storage_path == attachment.storage_path
        assert ra.uploaded_by == attachment.uploaded_by
        assert ra.uploaded_at == attachment.uploaded_at

    def test_comment_with_attachment_round_trip(self):
        # Arrange
        ticket = make_ticket()
        comment = make_comment()
        attachment = make_attachment()
        comment.attachments.append(attachment)
        ticket.comments.append(comment)

        # Act
        model = mapper.ticket_to_model(ticket)
        reconstructed = mapper.ticket_model_to_domain(model)

        # Assert
        assert len(reconstructed.comments[0].attachments) == 1
        ra = reconstructed.comments[0].attachments[0]
        assert ra.id == attachment.id

    def test_deleted_comment_round_trip(self):
        # Arrange
        ticket = make_ticket()
        comment = make_comment()
        comment.deleted_at = BASE_TIME
        ticket.comments.append(comment)

        # Act
        model = mapper.ticket_to_model(ticket)
        reconstructed = mapper.ticket_model_to_domain(model)

        # Assert
        assert reconstructed.comments[0].deleted_at == BASE_TIME

    def test_deleted_attachment_round_trip(self):
        # Arrange
        ticket = make_ticket()
        attachment = make_attachment()
        attachment.deleted_at = BASE_TIME
        ticket.attachments.append(attachment)

        # Act
        model = mapper.ticket_to_model(ticket)
        reconstructed = mapper.ticket_model_to_domain(model)

        # Assert
        assert reconstructed.attachments[0].deleted_at == BASE_TIME


# ---------------------------------------------------------------------------
# DTO mappers
# ---------------------------------------------------------------------------


class TestDtoMappers:
    def _make_model_with_comment_and_attachment(self) -> TicketModel:
        ticket_id = uuid4()
        comment_id = uuid4()
        attachment_id = uuid4()
        comment_attachment_id = uuid4()

        ticket_model = TicketModel(
            id=ticket_id,
            title="API rate limit exceeded",
            description="Third-party API returning 429.",
            application=Application.APP_3,
            status=Status.PENDING,
            priority=Priority.HIGH,
            assignee_id=uuid4(),
            created_at=BASE_TIME,
            updated_at=BASE_TIME,
            resolved_at=None,
            closed_at=None,
            pending_reason="Waiting for vendor",
            resolution_notes=None,
            archived_at=None,
        )

        comment_model = CommentModel(
            id=comment_id,
            ticket=ticket_model,
            author_id=uuid4(),
            content="Vendor acknowledged the issue.",
            created_at=BASE_TIME,
            edited_at=None,
            deleted_at=None,
        )
        comment_model.attachments = [
            AttachmentModel(
                id=comment_attachment_id,
                comment=comment_model,
                ticket=None,
                filename="vendor-response.pdf",
                content_type="application/pdf",
                storage_path="s3://bucket/vendor-response.pdf",
                uploaded_by=uuid4(),
                uploaded_at=BASE_TIME,
                deleted_at=None,
            )
        ]
        ticket_model.comments = [comment_model]
        ticket_model.attachments = [
            AttachmentModel(
                id=attachment_id,
                ticket=ticket_model,
                comment=None,
                filename="rate-limit-log.txt",
                content_type="text/plain",
                storage_path="s3://bucket/rate-limit-log.txt",
                uploaded_by=uuid4(),
                uploaded_at=BASE_TIME,
                deleted_at=None,
            )
        ]
        return ticket_model

    def test_summary_dto_contains_expected_fields(self):
        # Arrange
        model = self._make_model_with_comment_and_attachment()

        # Act
        dto = mapper.ticket_model_to_summary_dto(model)

        # Assert
        assert dto.id == model.id
        assert dto.title == model.title
        assert dto.application == model.application
        assert dto.status == model.status
        assert dto.priority == model.priority
        assert dto.assignee_id == model.assignee_id
        assert dto.created_at == model.created_at
        assert dto.updated_at == model.updated_at
        assert dto.archived_at == model.archived_at

    def test_detail_dto_contains_expected_nested_fields(self):
        # Arrange
        model = self._make_model_with_comment_and_attachment()

        # Act
        dto = mapper.ticket_model_to_detail_dto(model)

        # Assert — scalar fields
        assert dto.id == model.id
        assert dto.description == model.description
        assert dto.pending_reason == model.pending_reason

        # Assert — nested comments
        assert len(dto.comments) == 1
        comment_dto = dto.comments[0]
        assert comment_dto.content == "Vendor acknowledged the issue."
        assert len(comment_dto.attachments) == 1
        assert comment_dto.attachments[0].filename == "vendor-response.pdf"

        # Assert — ticket-level attachments
        assert len(dto.attachments) == 1
        assert dto.attachments[0].filename == "rate-limit-log.txt"
