from __future__ import annotations

import logging
from collections.abc import Callable

from app.modules.audit.application.interfaces.unit_of_work import UnitOfWork
from app.modules.audit.application.mapping.audit_mapper import AuditMapper
from app.shared.events.event import DomainEvent
from app.shared.events.handler import EventHandler

logger = logging.getLogger(__name__)


class AuditEventHandler(EventHandler):
	"""Thin consumer: delegates translation to AuditMapper, persists the result.

	Receives a fresh Unit of Work per call (via `uow_factory`) rather than one
	held for the handler's lifetime, since the same handler instance is
	subscribed to every audited event type and reused across concurrent
	requests -- one shared session would not be safe for that.
	"""

	def __init__(self, uow_factory: Callable[[], UnitOfWork], mapper: AuditMapper) -> None:
		self.uow_factory = uow_factory
		self.mapper = mapper

	async def handle(self, event: DomainEvent) -> None:
		entry = self.mapper.to_entry(event)
		if entry is None:
			logger.warning("No audit mapping registered for event type %s", type(event).__name__)
			return
		uow = self.uow_factory()
		try:
			await uow.entries.add(entry)
			await uow.commit()
		except Exception:
			await uow.rollback()
			raise
		finally:
			await uow.close()
