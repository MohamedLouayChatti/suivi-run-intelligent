from __future__ import annotations

from functools import partial

from app.modules.conversational_assistant.application.commands.send_message.command import SendMessageCommand
from app.modules.conversational_assistant.application.dto.send_message_result_dto import SendMessageResultDTO
from app.modules.conversational_assistant.application.exceptions import ConversationNotFound
from app.modules.conversational_assistant.application.interfaces.agent_run_runner import AgentRunRunner
from app.modules.conversational_assistant.application.interfaces.conversation_title_runner import (
	ConversationTitleRunner,
)
from app.modules.conversational_assistant.application.interfaces.unit_of_work import UnitOfWork
from app.modules.conversational_assistant.domain.entities.conversation import summarize_title
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

	A conversation's first message also starts a *second*, unrelated job: naming the conversation.
	Two enqueues rather than one chained after the other, because the title is derived from the
	question and owes nothing to the answer -- making it wait on the agent turn would delay a label
	the user could have had a second in, for no dependency that exists.
	"""

	def __init__(
		self,
		uow: UnitOfWork,
		event_publisher: EventPublisher,
		job_queue: JobQueue,
		runner: AgentRunRunner,
		title_runner: ConversationTitleRunner,
	) -> None:
		self.uow = uow
		self.event_publisher = event_publisher
		self.job_queue = job_queue
		self.runner = runner
		self.title_runner = title_runner

	async def handle(self, command: SendMessageCommand) -> SendMessageResultDTO:
		conversation = await self.uow.conversations.get(command.conversation_id)
		if conversation is None:
			raise ConversationNotFound()

		message = conversation.add_user_message(
			id=command.message_id, content=command.content, sent_at=command.sent_at,
		)
		# Read before the crop is written, and the only signal there is: an untitled conversation is
		# a conversation nobody has sent a message to yet. Nothing distinguishes a crop from a
		# generated title afterwards, so a conversation is named once, on its first message -- a
		# failed generation leaves the crop for good rather than being retried on the next turn.
		is_first_message = conversation.title is None
		run = conversation.start_run(
			id=command.run_id, triggering_message_id=message.id, started_at=command.sent_at,
		)

		try:
			await self.uow.conversations.save(conversation)
			if is_first_message:
				# The interim title, written synchronously so the conversation is identifiable in
				# the panel from the moment it appears. The generated one overwrites it when it
				# lands, and stands in for it permanently if nothing ever does.
				#
				# Through set_title rather than the aggregate, even here where nothing else is
				# writing yet: `title` has exactly one write path, and this call sharing it with
				# the background job is what makes "the last title written is the title stored"
				# true. Same Unit of Work as the save above, so the message, the run and the
				# interim title still land in one transaction or none.
				await self.uow.conversations.set_title(
					conversation.id, summarize_title(command.content)
				)
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise

		await self.job_queue.enqueue(
			partial(self.runner.run, conversation_id=conversation.id, run_id=run.id),
			name=f"conversational_assistant.run_agent[{run.id}]",
		)
		if is_first_message:
			await self.job_queue.enqueue(
				partial(
					self.title_runner.run,
					conversation_id=conversation.id, run_id=run.id, first_message=command.content,
				),
				name=f"conversational_assistant.generate_title[{conversation.id}]",
			)
		await self.event_publisher.publish(
			UserMessageReceived(
				conversation_id=conversation.id, message_id=message.id, run_id=run.id,
				occurred_at=command.sent_at, actor_id=command.actor_id,
			)
		)
		return SendMessageResultDTO(conversation_id=conversation.id, user_message_id=message.id, run_id=run.id)
