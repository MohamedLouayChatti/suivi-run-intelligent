from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry


class ToolArgumentError(ValueError):
	"""The model called a tool with arguments its schema refuses.

	Carries a French, user-safe message that *names the offending field and its legal values*,
	because that message is fed straight back to the model as the tool's result and is the only
	thing it has to correct itself with. A bare "invalid arguments" left it guessing, and a
	guessing model spends the whole iteration budget re-guessing.
	"""


def _inline_definitions(schema: dict[str, Any]) -> dict[str, Any]:
	"""Resolve every `$ref` against the schema's own `$defs` and drop the `$defs` block.

	Pydantic factors each enum out into `$defs` and points at it with a `$ref`, which is valid
	JSON Schema and useless here: the model is shown the tool's parameters as a literal blob and
	does not chase references, so `{"$ref": "#/$defs/TimeRange"}` told it nothing at all about
	which values `time_range` accepts. It then invented plausible-looking ones ("3 months",
	"Resolved"), every call was refused, and the answer that came back described a period nobody
	asked about. Inlining puts each `enum` list where the model actually reads it.
	"""
	definitions: dict[str, Any] = schema.get("$defs", {})

	def resolve(node: Any, seen: frozenset[str]) -> Any:
		if isinstance(node, list):
			return [resolve(item, seen) for item in node]
		if not isinstance(node, dict):
			return node
		reference = node.get("$ref")
		if isinstance(reference, str) and reference.startswith("#/$defs/"):
			name = reference.removeprefix("#/$defs/")
			# A self-referential definition would recurse forever; none exists today, and leaving
			# the `$ref` in place is the honest outcome if one ever does.
			if name in seen or name not in definitions:
				return node
			resolved = resolve(definitions[name], seen | {name})
			# Anything alongside the `$ref` (a `default`, a `description`) still applies.
			return {**resolved, **{key: value for key, value in node.items() if key != "$ref"}}
		return {key: resolve(value, seen) for key, value in node.items()}

	inlined = {key: resolve(value, frozenset()) for key, value in schema.items() if key != "$defs"}
	return inlined


def _permitted_values(field_schema: Any) -> list[str]:
	"""Every literal value a field accepts, gathered across `anyOf` branches -- an optional enum
	is `anyOf: [<the enum>, {"type": "null"}]`, so reading `enum` off the top level alone finds
	nothing for exactly the fields most worth explaining."""
	if not isinstance(field_schema, dict):
		return []
	values = [str(value) for value in field_schema.get("enum", [])]
	for branch in field_schema.get("anyOf", []):
		values.extend(_permitted_values(branch))
	return values


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
		return _inline_definitions(self.args_model.model_json_schema())

	def validate_arguments(self, raw_arguments: dict[str, Any]) -> BaseModel:
		"""Validate what the model produced, or raise ToolArgumentError describing what is wrong
		in terms the model can act on. Lives here, beside `args_model`, because which values are
		legal is a property of the tool's own argument contract -- the agent loop only decides
		what to do with the refusal."""
		try:
			return self.args_model.model_validate(raw_arguments)
		except ValidationError as exc:
			raise ToolArgumentError(self._describe(exc)) from exc

	def _describe(self, exc: ValidationError) -> str:
		schema = self.json_schema()
		properties: dict[str, Any] = schema.get("properties", {})
		problems: list[str] = []
		seen: set[str] = set()
		for error in exc.errors():
			field = str(error["loc"][0]) if error["loc"] else "?"
			if field in seen:
				continue
			seen.add(field)
			if error["type"] == "extra_forbidden":
				problems.append(
					f"« {field} » n'est pas un paramètre de cet outil (paramètres acceptés : "
					f"{', '.join(properties) or 'aucun'})"
				)
				continue
			permitted = _permitted_values(properties.get(field))
			if permitted:
				problems.append(
					f"« {field} » n'accepte que ces valeurs exactes : {', '.join(permitted)}"
				)
			else:
				problems.append(f"« {field} » : {error['msg']}")
		return (
			f"Arguments refusés par l'outil {self.name} : {' ; '.join(problems)}. "
			"Rappelez cet outil avec des valeurs valides, ou omettez le paramètre concerné."
		)
