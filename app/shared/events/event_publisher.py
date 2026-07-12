from __future__ import annotations

from abc import ABC, abstractmethod

from app.shared.events.event import DomainEvent

class EventPublisher(ABC):
	@abstractmethod
	async def publish(self, event: DomainEvent) -> None:
		raise NotImplementedError
