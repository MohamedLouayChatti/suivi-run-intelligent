from __future__ import annotations
from abc import ABC, abstractmethod

from app.shared.events.event import DomainEvent

class EventHandler(ABC):
	@abstractmethod
	async def handle(self, event: DomainEvent) -> None:
		raise NotImplementedError
