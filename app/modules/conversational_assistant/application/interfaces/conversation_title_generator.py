from __future__ import annotations

from abc import ABC, abstractmethod


class ConversationTitleGenerator(ABC):
	"""Port for turning a conversation's first user message into a short title.

	Deliberately narrow, and owned by this module rather than added to the shared LLMProvider port:
	this is a single-pass, tool-free, non-streamed summarization with nothing in common with an
	agent turn but the fact that a model serves it. LLMProvider argues for having exactly one
	method because every agent turn is a stream that may request tools; a title is neither, and
	widening that contract to fit would make both jobs harder to read. Keeping them apart also
	keeps them separately swappable -- the title model is pinned independently of the chat model.

	One operation, taking text and returning text. The implementation owns retries, timeouts and
	which model answers; callers own what to do when it raises, which for the only caller today is
	"nothing, the interim title stands".
	"""

	@abstractmethod
	async def generate(self, first_message: str) -> str:
		"""The model's raw answer for `first_message`, unnormalized.

		Raw on purpose: shaping an answer into an acceptable title is a rule about what a title is,
		which belongs to the domain (`normalize_title`), not to whichever provider happens to be
		answering. Raises when no answer could be obtained -- there is no "" or None sentinel to
		mistake for a model that legitimately returned nothing.
		"""
		raise NotImplementedError
