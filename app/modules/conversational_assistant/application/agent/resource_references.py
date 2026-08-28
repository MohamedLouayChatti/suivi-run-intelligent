from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence
from typing import Any
from uuid import UUID

from app.modules.conversational_assistant.application.tools.registry import ALL_TOOL_SPECS
from app.modules.conversational_assistant.domain.entities.tool_invocation import ToolInvocation

# The scheme the model is told to write and the frontend is taught to resolve. Deliberately not a
# URL: the backend names *what* is being referenced and leaves *where it lives* to the client, the
# same division Notifications' NotificationAction already makes. A path here would put this module
# in the business of knowing the frontend's route table.
REFERENCE_SCHEME = "ticket"

# Ordinary Markdown link syntax, so the renderer needs no grammar of its own -- only a rule for
# this scheme. The target is matched loosely (anything up to the closing paren) rather than as a
# UUID: a malformed id has to be *caught* here to be unwrapped, and a pattern that only matched
# well-formed ones would leave it in the text as a live link to nothing.
_REFERENCE_PATTERN = re.compile(r"\[(?P<label>[^\[\]]*)\]\(\s*ticket:(?P<id>[^)\s]*)\s*\)")

_TICKET_ID_EXTRACTORS: dict[str, Callable[[dict[str, Any]], Iterable[str]]] = {
	spec.name: spec.referenced_ticket_ids
	for spec in ALL_TOOL_SPECS
	if spec.referenced_ticket_ids is not None
}


def _canonical_id(raw: str) -> str | None:
	"""One spelling for one ticket, so a model that echoes an id back in upper case still matches."""
	try:
		return str(UUID(raw))
	except (ValueError, AttributeError, TypeError):
		return None


def collect_referable_ticket_ids(tool_invocations: Sequence[ToolInvocation]) -> set[str]:
	"""The tickets this run actually retrieved -- the only ones its answer may link to.

	Reads `result`, which a failed invocation never has: a call refused by an instance policy or a
	scope check records an `error` instead, so a ticket the caller was not allowed to see cannot
	enter this set. Authorization is therefore inherited from the tools rather than re-decided
	here, and a link can never reach further than the answer's own evidence did.
	"""
	referable: set[str] = set()
	for invocation in tool_invocations:
		extractor = _TICKET_ID_EXTRACTORS.get(invocation.tool_name)
		if extractor is None or invocation.result is None:
			continue
		try:
			raw_ids = extractor(invocation.result)
		except (KeyError, TypeError):
			# A payload that no longer matches its own extractor: link nothing from this call
			# rather than fail the run, which would lose an answer that is otherwise correct.
			continue
		referable.update(filter(None, (_canonical_id(raw) for raw in raw_ids)))
	return referable


def resolve_ticket_references(content: str, tool_invocations: Sequence[ToolInvocation]) -> str:
	"""Keep the references the run's own tool results vouch for; unwrap the rest to plain text.

	This is what makes an invented link impossible rather than merely unlikely. A model that
	guesses an id, reuses one from earlier in the conversation, or reformats a real one into
	something unparseable loses the link and keeps its sentence: the label is preserved in every
	rejection, so the reader still gets the answer, only without a target that would 404 or --
	worse -- point at a ticket the answer never actually consulted.
	"""
	referable = collect_referable_ticket_ids(tool_invocations)

	def replace(match: re.Match[str]) -> str:
		label = match.group("label")
		if not label.strip():
			# A link with nothing to click. Dropping the whole construct is the only reading that
			# leaves the sentence intact -- keeping it would render an invisible target.
			return ""
		ticket_id = _canonical_id(match.group("id"))
		if ticket_id is None or ticket_id not in referable:
			return label
		return f"[{label}]({REFERENCE_SCHEME}:{ticket_id})"

	return _REFERENCE_PATTERN.sub(replace, content)
