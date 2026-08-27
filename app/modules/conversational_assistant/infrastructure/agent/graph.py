from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolSpec
from app.modules.conversational_assistant.infrastructure.agent.nodes import build_agent_node, build_tools_node
from app.modules.conversational_assistant.infrastructure.agent.state import AgentState
from app.shared.ai.llm_provider import LLMProvider


def _route_after_agent(state: AgentState) -> str:
	last_message = state["messages"][-1]
	return "tools" if last_message.tool_calls else END


def build_agent_graph(llm_provider: LLMProvider, tool_specs: Sequence[ToolSpec], tool_context: ToolContext) -> Any:
	"""A minimal hand-rolled ReAct loop -- START -> agent (=) tools -> END -- built fresh for
	each run, since `tool_specs` (already permission-filtered) and `tool_context` (the caller)
	differ per user and must never be cached across runs.

	No LangChain BaseChatModel/BaseTool anywhere in this file or the nodes it wires: nodes call
	this codebase's own LLMProvider/ToolSpec ports directly, so LangGraph stays pure agent-loop
	orchestration, never the application's authorization or business-logic layer.
	"""
	graph = StateGraph(AgentState)
	graph.add_node("agent", build_agent_node(llm_provider, tool_specs))
	graph.add_node("tools", build_tools_node(tool_specs, tool_context))
	graph.add_edge(START, "agent")
	graph.add_conditional_edges("agent", _route_after_agent, {"tools": "tools", END: END})
	graph.add_edge("tools", "agent")
	return graph.compile()
