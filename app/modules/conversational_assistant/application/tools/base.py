from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry


@dataclass(frozen=True, slots=True)
class ToolResult:
	"""What a tool hands back to the agent loop -- deliberately not the handler's own DTO.

	`payload` is always the already-narrowed shape a tool builds by hand (never a raw DTO dump):
	only the fields the model needs, never full ORM/domain-shaped objects. `error` is a short,
	French, user-safe string (fed back to the model as a role="tool" message, which the model
	may relay or paraphrase) -- it covers both "the tool refused" (authorization) and "the tool
	found nothing" (not-found), neither of which aborts the run.
	"""

	ok: bool
	payload: dict[str, Any] | None = None
	error: str | None = None


@dataclass(frozen=True, slots=True)
class ToolContext:
	"""Everything a tool's `execute` needs, built once per agent run by AgentRunRunner.

	`session_factory` rather than a single shared session: several tools can run within one
	turn (the graph may call more than one before answering), and each opens and closes its own
	session -- mirrors how every read handler elsewhere in this codebase manages its own session
	rather than sharing one across unrelated reads.
	"""

	current_user: CurrentUser
	session_factory: Callable[[], AsyncSession]
	instance_authorization_registry: InstanceAuthorizationRegistry


@dataclass(frozen=True, slots=True)
class ToolSpec:
	"""One tool's full definition: its LLM-facing schema, the permission that gates whether it
	is even offered to this user (tool-availability authorization), and the adapter that runs it.
	"""

	name: str
	description: str
	args_model: type[BaseModel]
	required_permission: str
	execute: Callable[[BaseModel, ToolContext], Awaitable[ToolResult]]
	# Which ticket ids a successful payload names, for the tools whose results the model is allowed
	# to turn into a link the reader can click. Declared here, beside the payload it reads, rather
	# than as a table of payload paths kept somewhere central: each tool already builds its own
	# narrowed shape by hand, so the shape and the way to read it stay in one file and cannot drift
	# apart. `None` -- the default -- means this tool names no linkable resource, which is the right
	# answer for every aggregate-reporting tool: a KPI is a figure, not something with a page.
	referenced_ticket_ids: Callable[[dict[str, Any]], Iterable[str]] | None = None

	def json_schema(self) -> dict[str, Any]:
		return self.args_model.model_json_schema()
