from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.ticket_history_event_type import TicketHistoryEventType
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination
from app.shared.database.base import Base

if TYPE_CHECKING:
    from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel


class TicketHistoryModel(Base):
	__tablename__ = "ticket_history_entries"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	ticket_id: Mapped[UUID] = mapped_column(
		PGUUID(as_uuid=True),
		ForeignKey("tickets.id", ondelete="CASCADE"),
		nullable=False,
	)
	event_type: Mapped[TicketHistoryEventType] = mapped_column(SAEnum(TicketHistoryEventType, name="ticket_history_event_type"), nullable=False)
	occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	from_status: Mapped[Status | None] = mapped_column(SAEnum(Status, name="ticket_status"), nullable=True)
	to_status: Mapped[Status | None] = mapped_column(SAEnum(Status, name="ticket_status"), nullable=True)
	from_priority: Mapped[Priority | None] = mapped_column(SAEnum(Priority, name="ticket_priority"), nullable=True)
	to_priority: Mapped[Priority | None] = mapped_column(SAEnum(Priority, name="ticket_priority"), nullable=True)
	assignee_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
	transferred_to: Mapped[TransferDestination | None] = mapped_column(SAEnum(TransferDestination, name="ticket_transfer_destination"), nullable=True)
	requires_jira: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
	jira_id: Mapped[str | None] = mapped_column(String, nullable=True)
	jira_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
	operational_highlight: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

	ticket: Mapped["TicketModel"] = relationship(back_populates="history")
