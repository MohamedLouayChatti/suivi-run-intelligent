from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination

@dataclass(frozen=True)
class TransferTicketCommand:
	ticket_id: UUID
	transferred_to: TransferDestination
	transferred_at: datetime
	actor_id: UUID
