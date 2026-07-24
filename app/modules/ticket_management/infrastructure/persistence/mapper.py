from __future__ import annotations

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.application.dto.comment_dto import CommentDTO
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO, TicketSummaryDTO
from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.entities.comment import Comment
from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.infrastructure.persistence.models.attachment_model import AttachmentModel
from app.modules.ticket_management.infrastructure.persistence.models.comment_model import CommentModel
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel


def ticket_to_model(ticket: Ticket) -> TicketModel:
	ticket_model = TicketModel(
		id=ticket.id,
		title=ticket.title,
		description=ticket.description,
		application=ticket.application,
		status=ticket.status,
		priority=ticket.priority,
		assignee_id=ticket.assignee_id,
		category=ticket.category,
		functional_team=ticket.functional_team,
		genergy_id=ticket.genergy_id,
		oceane_id=ticket.oceane_id,
		jira_id=ticket.jira_id,
		requires_jira=ticket.requires_jira,
		operational_highlight=ticket.operational_highlight,
		offer=ticket.offer,
		version=ticket.version,
		element=ticket.element,
		transferred_to=ticket.transferred_to,
		created_at=ticket.created_at,
		updated_at=ticket.updated_at,
		resolved_at=ticket.resolved_at,
		closed_at=ticket.closed_at,
		resolution_notes=ticket.resolution_notes,
		archived_at=ticket.archived_at,
	)
	ticket_model.comments = [comment_to_model(comment, ticket_model) for comment in ticket.comments]
	ticket_model.attachments = [attachment_to_model(attachment, ticket_model=ticket_model) for attachment in ticket.attachments]
	return ticket_model


def sync_ticket_model(ticket_model: TicketModel, ticket: Ticket) -> TicketModel:
	ticket_model.title = ticket.title
	ticket_model.description = ticket.description
	ticket_model.application = ticket.application
	ticket_model.status = ticket.status
	ticket_model.priority = ticket.priority
	ticket_model.assignee_id = ticket.assignee_id
	ticket_model.category = ticket.category
	ticket_model.functional_team = ticket.functional_team
	ticket_model.genergy_id = ticket.genergy_id
	ticket_model.oceane_id = ticket.oceane_id
	ticket_model.jira_id = ticket.jira_id
	ticket_model.requires_jira = ticket.requires_jira
	ticket_model.operational_highlight = ticket.operational_highlight
	ticket_model.offer = ticket.offer
	ticket_model.version = ticket.version
	ticket_model.element = ticket.element
	ticket_model.transferred_to = ticket.transferred_to
	ticket_model.created_at = ticket.created_at
	ticket_model.updated_at = ticket.updated_at
	ticket_model.resolved_at = ticket.resolved_at
	ticket_model.closed_at = ticket.closed_at
	ticket_model.resolution_notes = ticket.resolution_notes
	ticket_model.archived_at = ticket.archived_at
	_sync_ticket_attachments(ticket_model, ticket.attachments)
	_sync_ticket_comments(ticket_model, ticket.comments)
	return ticket_model


def ticket_model_to_domain(ticket_model: TicketModel) -> Ticket:
	return Ticket(
		id=ticket_model.id,
		title=ticket_model.title,
		description=ticket_model.description,
		application=ticket_model.application,
		status=ticket_model.status,
		priority=ticket_model.priority,
		assignee_id=ticket_model.assignee_id,
		category=ticket_model.category,
		functional_team=ticket_model.functional_team,
		genergy_id=ticket_model.genergy_id,
		oceane_id=ticket_model.oceane_id,
		jira_id=ticket_model.jira_id,
		requires_jira=ticket_model.requires_jira,
		operational_highlight=ticket_model.operational_highlight,
		offer=ticket_model.offer,
		version=ticket_model.version,
		element=ticket_model.element,
		transferred_to=ticket_model.transferred_to,
		created_at=ticket_model.created_at,
		updated_at=ticket_model.updated_at,
		resolved_at=ticket_model.resolved_at,
		closed_at=ticket_model.closed_at,
		resolution_notes=ticket_model.resolution_notes,
		comments=[comment_model_to_domain(comment_model) for comment_model in ticket_model.comments],
		attachments=[attachment_model_to_domain(attachment_model) for attachment_model in ticket_model.attachments],
		archived_at=ticket_model.archived_at,
	)


def ticket_model_to_summary_dto(ticket_model: TicketModel) -> TicketSummaryDTO:
	return TicketSummaryDTO(
		id=ticket_model.id,
		title=ticket_model.title,
		application=ticket_model.application,
		status=ticket_model.status,
		priority=ticket_model.priority,
		assignee_id=ticket_model.assignee_id,
		category=ticket_model.category,
		functional_team=ticket_model.functional_team,
		operational_highlight=ticket_model.operational_highlight,
		transferred_to=ticket_model.transferred_to,
		created_at=ticket_model.created_at,
		updated_at=ticket_model.updated_at,
		archived_at=ticket_model.archived_at,
	)


def ticket_model_to_detail_dto(ticket_model: TicketModel) -> TicketDetailDTO:
	return TicketDetailDTO(
		id=ticket_model.id,
		title=ticket_model.title,
		description=ticket_model.description,
		application=ticket_model.application,
		status=ticket_model.status,
		priority=ticket_model.priority,
		assignee_id=ticket_model.assignee_id,
		category=ticket_model.category,
		functional_team=ticket_model.functional_team,
		genergy_id=ticket_model.genergy_id,
		oceane_id=ticket_model.oceane_id,
		jira_id=ticket_model.jira_id,
		requires_jira=ticket_model.requires_jira,
		operational_highlight=ticket_model.operational_highlight,
		offer=ticket_model.offer,
		version=ticket_model.version,
		element=ticket_model.element,
		transferred_to=ticket_model.transferred_to,
		created_at=ticket_model.created_at,
		updated_at=ticket_model.updated_at,
		resolved_at=ticket_model.resolved_at,
		closed_at=ticket_model.closed_at,
		resolution_notes=ticket_model.resolution_notes,
		comments=[comment_model_to_dto(comment_model) for comment_model in ticket_model.comments],
		attachments=[attachment_model_to_dto(attachment_model) for attachment_model in ticket_model.attachments],
		archived_at=ticket_model.archived_at,
	)


def comment_to_model(comment: Comment, ticket_model: TicketModel) -> CommentModel:
	comment_model = CommentModel(
		id=comment.id,
		ticket=ticket_model,
		author_id=comment.author_id,
		content=comment.content,
		created_at=comment.created_at,
		edited_at=comment.edited_at,
		deleted_at=comment.deleted_at,
	)
	comment_model.attachments = [attachment_to_model(attachment, comment_model=comment_model) for attachment in comment.attachments]
	return comment_model


def sync_comment_model(comment_model: CommentModel, comment: Comment) -> CommentModel:
	comment_model.author_id = comment.author_id
	comment_model.content = comment.content
	comment_model.created_at = comment.created_at
	comment_model.edited_at = comment.edited_at
	comment_model.deleted_at = comment.deleted_at
	_sync_comment_attachments(comment_model, comment.attachments)
	return comment_model


def comment_model_to_domain(comment_model: CommentModel) -> Comment:
	return Comment(
		id=comment_model.id,
		author_id=comment_model.author_id,
		content=comment_model.content,
		created_at=comment_model.created_at,
		attachments=[attachment_model_to_domain(attachment_model) for attachment_model in comment_model.attachments],
		edited_at=comment_model.edited_at,
		deleted_at=comment_model.deleted_at,
	)


def comment_model_to_dto(comment_model: CommentModel) -> CommentDTO:
	return CommentDTO(
		id=comment_model.id,
		author_id=comment_model.author_id,
		content=comment_model.content,
		created_at=comment_model.created_at,
		attachments=[attachment_model_to_dto(attachment_model) for attachment_model in comment_model.attachments],
		edited_at=comment_model.edited_at,
		deleted_at=comment_model.deleted_at,
	)


def attachment_to_model(
	attachment: Attachment,
	*,
	ticket_model: TicketModel | None = None,
	comment_model: CommentModel | None = None,
) -> AttachmentModel:
	return AttachmentModel(
		id=attachment.id,
		ticket=ticket_model,
		comment=comment_model,
		filename=attachment.filename,
		content_type=attachment.content_type,
		storage_path=attachment.storage_path,
		uploaded_by=attachment.uploaded_by,
		uploaded_at=attachment.uploaded_at,
		deleted_at=attachment.deleted_at,
	)


def sync_attachment_model(attachment_model: AttachmentModel, attachment: Attachment) -> AttachmentModel:
	attachment_model.filename = attachment.filename
	attachment_model.content_type = attachment.content_type
	attachment_model.storage_path = attachment.storage_path
	attachment_model.uploaded_by = attachment.uploaded_by
	attachment_model.uploaded_at = attachment.uploaded_at
	attachment_model.deleted_at = attachment.deleted_at
	return attachment_model


def attachment_model_to_domain(attachment_model: AttachmentModel) -> Attachment:
	return Attachment(
		id=attachment_model.id,
		filename=attachment_model.filename,
		content_type=attachment_model.content_type,
		storage_path=attachment_model.storage_path,
		uploaded_by=attachment_model.uploaded_by,
		uploaded_at=attachment_model.uploaded_at,
		deleted_at=attachment_model.deleted_at,
	)


def attachment_model_to_dto(attachment_model: AttachmentModel) -> AttachmentDTO:
	return AttachmentDTO(
		id=attachment_model.id,
		filename=attachment_model.filename,
		content_type=attachment_model.content_type,
		storage_path=attachment_model.storage_path,
		uploaded_by=attachment_model.uploaded_by,
		uploaded_at=attachment_model.uploaded_at,
		deleted_at=attachment_model.deleted_at,
	)


def _sync_ticket_comments(ticket_model: TicketModel, comments: list[Comment]) -> None:
	existing_comments = {comment_model.id: comment_model for comment_model in ticket_model.comments}
	synced_comments: list[CommentModel] = []

	for comment in comments:
		comment_model = existing_comments.get(comment.id)
		if comment_model is None:
			comment_model = comment_to_model(comment, ticket_model)
		else:
			sync_comment_model(comment_model, comment)
			comment_model.ticket = ticket_model
		synced_comments.append(comment_model)

	ticket_model.comments = synced_comments


def _sync_ticket_attachments(ticket_model: TicketModel, attachments: list[Attachment]) -> None:
	existing_attachments = {attachment_model.id: attachment_model for attachment_model in ticket_model.attachments}
	synced_attachments: list[AttachmentModel] = []

	for attachment in attachments:
		attachment_model = existing_attachments.get(attachment.id)
		if attachment_model is None:
			attachment_model = attachment_to_model(attachment, ticket_model=ticket_model)
		else:
			sync_attachment_model(attachment_model, attachment)
			attachment_model.ticket = ticket_model
			attachment_model.comment = None
		synced_attachments.append(attachment_model)

	ticket_model.attachments = synced_attachments


def _sync_comment_attachments(comment_model: CommentModel, attachments: list[Attachment]) -> None:
	existing_attachments = {attachment_model.id: attachment_model for attachment_model in comment_model.attachments}
	synced_attachments: list[AttachmentModel] = []

	for attachment in attachments:
		attachment_model = existing_attachments.get(attachment.id)
		if attachment_model is None:
			attachment_model = attachment_to_model(attachment, comment_model=comment_model)
		else:
			sync_attachment_model(attachment_model, attachment)
			attachment_model.comment = comment_model
			attachment_model.ticket = None
		synced_attachments.append(attachment_model)

	comment_model.attachments = synced_attachments

