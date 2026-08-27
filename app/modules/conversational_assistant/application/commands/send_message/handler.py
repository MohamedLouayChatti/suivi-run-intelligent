from __future__ import annotations

from functools import partial

from app.modules.conversational_assistant.application.commands.send_message.command import SendMessageCommand
from app.modules.conversational_assistant.application.dto.send_message_result_dto import SendMessageResultDTO
from app.modules.conversational_assistant.application.exceptions import ConversationNotFound
from app.modules.conversational_assistant.application.interfaces.agent_run_runner import AgentRunRunner
from app.modules.conversational_assistant.application.interfaces.unit_of_work import UnitOfWork
from app.modules.conversational_assistant.domain.events.user_message_received import UserMessageReceived
from app.shared.events.event_publisher import EventPublisher
from app.workers.jobs import JobQueue


class SendMessageHandler:
	"""Persists the user's message and starts a Run for it, then hands the turn off to the
	background job queue -- mirrors TriggerSimilarityRecalculationHandler's shape exactly: enqueue
	first, publish the "a person did this" event after, since the announcement should follow the
	act it announces.

	The agent's own reply is never written here. It is written later, from inside
	`AgentRunRunner.run`, using its own fresh session -- the request that accepted this message
	is not the request that will still be open when the agent finishes answering.
	"""

	def __init__(
		self, uow: UnitOfWork, event_publisher: EventPublisher, job_queue: JobQueue, runner: AgentRunRunner,
	) -> None:
		self.uow = uow
		self.event_publisher = event_publisher
		self.job_queue = job_queue
		self.runner = runner

	async def handle(self, command: SendMessageCommand) -> SendMessageResultDTO:
		conversation = await self.uow.conversations.get(command.conversation_id)
		if conversation is None:
			raise ConversationNotFound()

		message = conversation.add_user_message(
			id=command.message_id, content=command.content, sent_at=command.sent_at,
		)
		if conversation.title is None:
			conversation.set_title_from_first_message(command.content)
		run = conversation.start_run(
			id=command.run_id, triggering_message_id=message.id, started_at=command.sent_at,
		)

		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise

		await self.job_queue.enqueue(
			partial(self.runner.run, conversation_id=conversation.id, run_id=run.id),
			name=f"conversational_assistant.run_agent[{run.id}]",
		)
		await self.event_publisher.publish(
			UserMessageReceived(
				conversation_id=conversation.id, message_id=message.id, run_id=run.id,
				occurred_at=command.sent_at, actor_id=command.actor_id,
			)
		)
		return SendMessageResultDTO(conversation_id=conversation.id, user_message_id=message.id, run_id=run.id)
