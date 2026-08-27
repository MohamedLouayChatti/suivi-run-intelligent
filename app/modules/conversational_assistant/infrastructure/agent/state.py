from __future__ import annotations

from typing import TypedDict

from app.modules.conversational_assistant.domain.entities.tool_invocation import ToolInvocation
from app.shared.ai.llm_provider import ChatMessage


class AgentState(TypedDict):
	messages: list[ChatMessage]
	tool_calls_made: list[ToolInvocation]
	iterations: int
