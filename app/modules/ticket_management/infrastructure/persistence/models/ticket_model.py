from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.ticket_management.infrastructure.persistence.models.comment_model import CommentModel
    from app.modules.ticket_management.infrastructure.persistence.models.attachment_model import AttachmentModel

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.element import Element
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.offer import Offer
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination
from app.modules.ticket_management.domain.enums.vio_app import VioApp
from app.modules.ticket_management.domain.enums.version import Version
from app.shared.database.base import Base


class TicketModel(Base):
	__tablename__ = "tickets"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	title: Mapped[str] = mapped_column(String(255), nullable=False)
	description: Mapped[str] = mapped_column(Text, nullable=False)
	application: Mapped[Application] = mapped_column(SAEnum(Application, name="ticket_application"), nullable=False)
	status: Mapped[Status] = mapped_column(SAEnum(Status, name="ticket_status"), nullable=False)
	priority: Mapped[Priority] = mapped_column(SAEnum(Priority, name="ticket_priority"), nullable=False)
	assignee_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
	category: Mapped[Category] = mapped_column(SAEnum(Category, name="ticket_category"), nullable=False)
	functional_team: Mapped[FunctionalTeam] = mapped_column(SAEnum(FunctionalTeam, name="ticket_functional_team"), nullable=False)
	genergy_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
	oceane_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
	jira_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
	jira_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
	requires_jira: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	operational_highlight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	offer: Mapped[Offer | None] = mapped_column(SAEnum(Offer, name="ticket_offer"), nullable=True)
	version: Mapped[Version | None] = mapped_column(SAEnum(Version, name="ticket_version"), nullable=True)
	element: Mapped[Element | None] = mapped_column(SAEnum(Element, name="ticket_element"), nullable=True)
	vio_app: Mapped[VioApp | None] = mapped_column(SAEnum(VioApp, name="ticket_vio_app"), nullable=True)
	transferred_to: Mapped[TransferDestination | None] = mapped_column(SAEnum(TransferDestination, name="ticket_transfer_destination"), nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
	archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

	comments: Mapped[list["CommentModel"]] = relationship(
		back_populates="ticket",
		cascade="all, delete-orphan",
		lazy="selectin",
		single_parent=True,
	)
	attachments: Mapped[list["AttachmentModel"]] = relationship(
		back_populates="ticket",
		cascade="all, delete-orphan",
		lazy="selectin",
		single_parent=True,
		foreign_keys="AttachmentModel.ticket_id",
	)
