from __future__ import annotations

from collections.abc import Sequence

from app.modules.conversational_assistant.domain.entities.message import Message
from app.modules.conversational_assistant.domain.enums.message_role import MessageRole
from app.shared.ai.llm_provider import ChatMessage

_ROLE_TO_CHAT_ROLE = {
	MessageRole.USER: "user",
	MessageRole.ASSISTANT: "assistant",
}


def build_llm_context(messages: Sequence[Message]) -> list[ChatMessage]:
	"""Turns persisted Messages into the LLM's own message shape, oldest first.

	No filtering happens here because none is needed: a Message row only ever exists for a
	successful turn (Run's own failure never produces one -- see the Conversation aggregate),
	so the persisted history already excludes every failed attempt by construction.
	"""
	return [
		ChatMessage(role=_ROLE_TO_CHAT_ROLE[message.role], content=message.content)
		for message in messages
	]
