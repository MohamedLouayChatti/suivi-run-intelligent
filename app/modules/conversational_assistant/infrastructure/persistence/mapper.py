from __future__ import annotations

from app.modules.conversational_assistant.application.dto.conversation_summary_dto import ConversationSummaryDTO
from app.modules.conversational_assistant.application.dto.message_dto import MessageDTO
from app.modules.conversational_assistant.application.dto.run_summary_dto import RunSummaryDTO
from app.modules.conversational_assistant.domain.entities.conversation import Conversation
from app.modules.conversational_assistant.domain.entities.message import Message
from app.modules.conversational_assistant.domain.entities.run import Run
from app.modules.conversational_assistant.domain.entities.tool_invocation import ToolInvocation
from app.modules.conversational_assistant.infrastructure.persistence.models.conversation_model import (
	ConversationModel,
)
from app.modules.conversational_assistant.infrastructure.persistence.models.message_model import MessageModel
from app.modules.conversational_assistant.infrastructure.persistence.models.run_model import RunModel
from app.modules.conversational_assistant.infrastructure.persistence.models.tool_invocation_model import (
	ToolInvocationModel,
)


def conversation_to_model(conversation: Conversation) -> ConversationModel:
	conversation_model = ConversationModel(
		id=conversation.id, user_id=conversation.user_id, title=conversation.title,
		created_at=conversation.created_at, updated_at=conversation.updated_at,
	)
	conversation_model.messages = [message_to_model(message, conversation_model) for message in conversation.messages]
	conversation_model.runs = [run_to_model(run, conversation_model) for run in conversation.runs]
	return conversation_model


def sync_conversation_model(conversation_model: ConversationModel, conversation: Conversation) -> ConversationModel:
	conversation_model.title = conversation.title
	conversation_model.updated_at = conversation.updated_at
	_sync_messages(conversation_model, conversation.messages)
	_sync_runs(conversation_model, conversation.runs)
	return conversation_model


def conversation_model_to_domain(conversation_model: ConversationModel) -> Conversation:
	return Conversation(
		id=conversation_model.id, user_id=conversation_model.user_id,
		created_at=conversation_model.created_at, updated_at=conversation_model.updated_at,
		title=conversation_model.title,
		messages=[message_model_to_domain(message) for message in conversation_model.messages],
		runs=[run_model_to_domain(run) for run in conversation_model.runs],
	)


def conversation_model_to_summary_dto(conversation_model: ConversationModel) -> ConversationSummaryDTO:
	return ConversationSummaryDTO(
		id=conversation_model.id, title=conversation_model.title,
		created_at=conversation_model.created_at, updated_at=conversation_model.updated_at,
	)


def message_to_model(message: Message, conversation_model: ConversationModel) -> MessageModel:
	return MessageModel(
		id=message.id, conversation=conversation_model, role=message.role,
		content=message.content, created_at=message.created_at,
	)


def message_model_to_domain(message_model: MessageModel) -> Message:
	return Message(
		id=message_model.id, role=message_model.role, content=message_model.content,
		created_at=message_model.created_at,
	)


def message_model_to_dto(message_model: MessageModel) -> MessageDTO:
	return MessageDTO(
		id=message_model.id, role=message_model.role, content=message_model.content,
		created_at=message_model.created_at,
	)


def run_to_model(run: Run, conversation_model: ConversationModel) -> RunModel:
	run_model = RunModel(
		id=run.id, conversation=conversation_model, triggering_message_id=run.triggering_message_id,
		response_message_id=run.response_message_id, status=run.status, started_at=run.started_at,
		completed_at=run.completed_at, failure_reason=run.failure_reason, failure_detail=run.failure_detail,
	)
	run_model.tool_invocations = [
		tool_invocation_to_model(tool_invocation, run_model) for tool_invocation in run.tool_invocations
	]
	return run_model


def sync_run_model(run_model: RunModel, run: Run) -> RunModel:
	# Unlike Message, a Run *is* mutated in place across up to three commits (PENDING -> RUNNING ->
	# COMPLETED/FAILED), so an existing row is synced rather than left untouched.
	run_model.response_message_id = run.response_message_id
	run_model.status = run.status
	run_model.completed_at = run.completed_at
	run_model.failure_reason = run.failure_reason
	run_model.failure_detail = run.failure_detail
	_sync_tool_invocations(run_model, run.tool_invocations)
	return run_model


def run_model_to_domain(run_model: RunModel) -> Run:
	return Run(
		id=run_model.id, triggering_message_id=run_model.triggering_message_id,
		status=run_model.status, started_at=run_model.started_at,
		response_message_id=run_model.response_message_id, completed_at=run_model.completed_at,
		failure_reason=run_model.failure_reason, failure_detail=run_model.failure_detail,
		tool_invocations=[
			tool_invocation_model_to_domain(tool_invocation_model)
			for tool_invocation_model in run_model.tool_invocations
		],
	)


def run_model_to_summary_dto(run_model: RunModel) -> RunSummaryDTO:
	return RunSummaryDTO(
		id=run_model.id, status=run_model.status, failure_reason=run_model.failure_reason,
		created_at=run_model.started_at,
	)


def tool_invocation_to_model(tool_invocation: ToolInvocation, run_model: RunModel) -> ToolInvocationModel:
	return ToolInvocationModel(
		id=tool_invocation.id, run=run_model, tool_name=tool_invocation.tool_name,
		arguments=tool_invocation.arguments, result=tool_invocation.result, error=tool_invocation.error,
		started_at=tool_invocation.started_at, completed_at=tool_invocation.completed_at,
	)


def tool_invocation_model_to_domain(tool_invocation_model: ToolInvocationModel) -> ToolInvocation:
	return ToolInvocation(
		id=tool_invocation_model.id, tool_name=tool_invocation_model.tool_name,
		arguments=tool_invocation_model.arguments, result=tool_invocation_model.result,
		error=tool_invocation_model.error, started_at=tool_invocation_model.started_at,
		completed_at=tool_invocation_model.completed_at,
	)


def _sync_messages(conversation_model: ConversationModel, messages: list[Message]) -> None:
	# Append-only: a Message row is never edited once created (see Message's own docstring), so
	# an existing row is only ever re-parented, never re-synced.
	existing = {message_model.id: message_model for message_model in conversation_model.messages}
	synced: list[MessageModel] = []
	for message in messages:
		message_model = existing.get(message.id)
		if message_model is None:
			message_model = message_to_model(message, conversation_model)
		else:
			message_model.conversation = conversation_model
		synced.append(message_model)
	conversation_model.messages = synced


def _sync_runs(conversation_model: ConversationModel, runs: list[Run]) -> None:
	existing = {run_model.id: run_model for run_model in conversation_model.runs}
	synced: list[RunModel] = []
	for run in runs:
		run_model = existing.get(run.id)
		if run_model is None:
			run_model = run_to_model(run, conversation_model)
		else:
			sync_run_model(run_model, run)
			run_model.conversation = conversation_model
		synced.append(run_model)
	conversation_model.runs = synced


def _sync_tool_invocations(run_model: RunModel, tool_invocations: list[ToolInvocation]) -> None:
	# Append-only, and in practice only ever written once -- a Run only ever completes or fails once.
	existing = {
		tool_invocation_model.id: tool_invocation_model for tool_invocation_model in run_model.tool_invocations
	}
	synced: list[ToolInvocationModel] = []
	for tool_invocation in tool_invocations:
		tool_invocation_model = existing.get(tool_invocation.id)
		if tool_invocation_model is None:
			tool_invocation_model = tool_invocation_to_model(tool_invocation, run_model)
		else:
			tool_invocation_model.run = run_model
		synced.append(tool_invocation_model)
	run_model.tool_invocations = synced
