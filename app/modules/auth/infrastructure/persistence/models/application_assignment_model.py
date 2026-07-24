from __future__ import annotations

from uuid import UUID

from sqlalchemy import Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.auth.domain.enums.application import Application
from app.modules.auth.domain.enums.assignment_type import AssignmentType
from app.shared.database.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from app.modules.auth.infrastructure.persistence.models.user_model import UserModel


class ApplicationAssignmentModel(Base):
	__tablename__ = "user_application_assignments"

	user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
	application: Mapped[Application] = mapped_column(SAEnum(Application, name="auth_application"), primary_key=True)
	assignment_type: Mapped[AssignmentType] = mapped_column(SAEnum(AssignmentType, name="auth_assignment_type"), primary_key=True)

	user: Mapped["UserModel"] = relationship(back_populates="application_assignments")
