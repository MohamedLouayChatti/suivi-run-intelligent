from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.conversational_assistant.domain.entities.conversation import Conversation


class ConversationRepository(ABC):
	@abstractmethod
	async def add(self, conversation: Conversation) -> None:
		raise NotImplementedError

	@abstractmethod
	async def get(self, conversation_id: UUID) -> Conversation | None:
		raise NotImplementedError

	@abstractmethod
	async def save(self, conversation: Conversation) -> None:
		raise NotImplementedError

	@abstractmethod
	async def set_title(self, conversation_id: UUID, title: str) -> None:
		"""Write one conversation's title. **The only way a title is ever written** -- `save` leaves
		the stored one alone, and both writers come through here.

		The one write on this contract that is not aggregate-shaped, and deliberately so, because
		`title` is the one field with two writers: the request that crops an interim one from the
		first message, and the background job that generates the real one about a second later.
		Every other field `save` overwrites has a single writer, which is what makes a blind
		full-aggregate overwrite safe for them and unsafe for this one -- an agent run holds its
		aggregate across a whole turn and saves it again at the end, so a title written by the job
		meanwhile was silently restored to the crop the run had loaded at the start. Narrowing the
		write is only half of the fix; the other half is that nothing else writes the column at all
		(see the note in mapper.sync_conversation_model, which is where that overwrite lived).

		It matters that both halves are in place, because the overwrite was *intermittent*: whether
		the stale assignment produced an UPDATE depended on whether SQLAlchemy's weakly-referenced
		identity map had dropped the row's instance mid-turn. A race that usually loses is still a
		race, and this one lost only after a garbage collection nobody controls.

		Safe to keep off the aggregate because `title` carries no invariant against messages or
		runs -- the rules it does carry live in Domain as `summarize_title`/`normalize_title`, which
		the callers apply. `updated_at` is deliberately left alone: a title is derived from a message
		that already bumped it, and titling is not activity to reorder a conversation list by.
		"""
		raise NotImplementedError
