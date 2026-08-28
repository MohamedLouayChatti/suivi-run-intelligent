from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.conversational_assistant.domain.entities.message import Message
from app.modules.conversational_assistant.domain.entities.run import Run
from app.modules.conversational_assistant.domain.entities.tool_invocation import ToolInvocation
from app.modules.conversational_assistant.domain.enums.message_role import MessageRole
from app.modules.conversational_assistant.domain.exceptions import RunNotFound

TITLE_MAX_LENGTH = 60

# What a summarizing model wraps its answer in rather than says: a quoted title, a "Titre :"
# preamble, a Markdown heading, a trailing full stop, a reasoning block a thinking model failed to
# keep out of its content. Stripped here rather than only asked against in the prompt, because the
# prompt is a request and this is the rule.
_THINKING_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_TITLE_PREFIX = re.compile(r"^\s*(?:titre|title)\s*[:\-–]\s*", re.IGNORECASE)
# Stripped from both ends, not just the leading one: a model that emphasises its answer wraps it
# (`**Panne COLORIS**`) as readily as it prefixes it with a bullet or a heading marker.
_WRAPPING_MARKUP = "#*_>-` \t"
_WRAPPING_QUOTES = "\"'«»“”‘’‹›"
# Includes U+00A0: French typography puts a non-breaking space before ! and ?, so stripping the
# punctuation alone would leave the space behind it.
_TRAILING_PUNCTUATION = ".!?  "


def _truncate(collapsed: str) -> str:
	if len(collapsed) <= TITLE_MAX_LENGTH:
		return collapsed
	return collapsed[:TITLE_MAX_LENGTH].rsplit(" ", 1)[0] + "…"


def summarize_title(content: str) -> str:
	"""The interim title a conversation carries until a generated one replaces it: its first
	message, collapsed and cropped to the same ceiling.

	A function rather than a method on the aggregate, for the same reason `normalize_title` is one:
	a title is not written through `save()` (see ConversationRepository.set_title), so a mutator
	setting `Conversation.title` would change an object nothing persists -- which is worse than no
	mutator at all, because it reads as though it did.
	"""
	return _truncate(" ".join(content.split()))


def normalize_title(raw: str) -> str | None:
	"""A model's raw answer reduced to a title this aggregate would accept, or None when nothing
	usable is left of it.

	Public, and in Domain, because the generated title is not written through the aggregate: that
	write is a targeted column update (see ConversationRepository.set_title), taken deliberately so
	a background job cannot save a stale aggregate over a concurrently-completing Run. Bypassing
	the aggregate is only safe while the rule it would have applied still lives in one place, which
	is here -- the same ceiling the crop respects, since the two produce the same field.
	"""
	first_line = next((line for line in _THINKING_BLOCK.sub("", raw).splitlines() if line.strip()), "")
	unwrapped = _TITLE_PREFIX.sub("", first_line.strip(_WRAPPING_MARKUP))
	collapsed = " ".join(unwrapped.strip(_WRAPPING_MARKUP).strip(_WRAPPING_QUOTES).split())
	return _truncate(collapsed.rstrip(_TRAILING_PUNCTUATION).strip()) or None


@dataclass
class Conversation:
	"""Aggregate root: one chat thread, owning its ordered Messages and Runs -- the same shape
	Ticket owns Comment/Attachment/TicketHistoryEntry. Ownership is strictly self-only in v1:
	`user_id` is the only thing an instance policy ever checks, with no breadth override.

	`title` is the one field here that is read but never written back: it is set through
	ConversationRepository.set_title, and saving this aggregate deliberately leaves the stored one
	alone. It is the only field with two writers -- the request that crops an interim title and the
	background job that generates the real one -- and this aggregate is held across a whole agent
	turn, long enough for the copy loaded into it to go stale while the turn is still running.
	"""

	id: UUID
	user_id: UUID
	created_at: datetime
	updated_at: datetime
	title: str | None = None
	messages: list[Message] = field(default_factory=list)
	runs: list[Run] = field(default_factory=list)

	@classmethod
	def start(cls, *, id: UUID, user_id: UUID, created_at: datetime) -> Conversation:
		return cls(id=id, user_id=user_id, created_at=created_at, updated_at=created_at)

	def add_user_message(self, *, id: UUID, content: str, sent_at: datetime) -> Message:
		message = Message.create(id=id, role=MessageRole.USER, content=content, created_at=sent_at)
		self.messages.append(message)
		self.updated_at = sent_at
		return message

	def start_run(self, *, id: UUID, triggering_message_id: UUID, started_at: datetime) -> Run:
		run = Run.start(id=id, triggering_message_id=triggering_message_id, started_at=started_at)
		self.runs.append(run)
		return run

	def get_run(self, run_id: UUID) -> Run:
		for run in self.runs:
			if run.id == run_id:
				return run
		raise RunNotFound()

	def mark_run_running(self, *, run_id: UUID, at: datetime) -> None:
		self.get_run(run_id).mark_running(at=at)

	def complete_run(
		self, *, run_id: UUID, response_message_id: UUID, content: str,
		tool_invocations: Sequence[ToolInvocation], completed_at: datetime,
	) -> Message:
		run = self.get_run(run_id)
		message = Message.create(
			id=response_message_id, role=MessageRole.ASSISTANT, content=content, created_at=completed_at,
		)
		run.complete(
			response_message_id=response_message_id, tool_invocations=tool_invocations, completed_at=completed_at,
		)
		self.messages.append(message)
		self.updated_at = completed_at
		return message

	def fail_run(
		self, *, run_id: UUID, failure_reason: str, failure_detail: str | None, completed_at: datetime,
	) -> None:
		run = self.get_run(run_id)
		run.fail(failure_reason=failure_reason, failure_detail=failure_detail, completed_at=completed_at)
		self.updated_at = completed_at

	@property
	def latest_run(self) -> Run | None:
		return self.runs[-1] if self.runs else None
