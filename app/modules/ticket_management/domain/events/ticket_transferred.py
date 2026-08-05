from dataclasses import dataclass
from uuid import UUID
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination
from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class TicketTransferred(DomainEvent):
	ticket_id: UUID
	transferred_to: TransferDestination
