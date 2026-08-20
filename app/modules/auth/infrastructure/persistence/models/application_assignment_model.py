from __future__ import annotations

from uuid import UUID

from sqlalchemy import Enum as SAEnum, ForeignKey, Index
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

	# One assignment per application per user, so assignment_type is an attribute of it rather
	# than part of its identity -- with it in the key, one application could be held as both
	# PRIMARY and BACKUP. The two partial unique indexes carry the other half of the rule: a
	# user runs at most one application and backs up at most one other.
	__table_args__ = (
		Index(
			"uq_user_application_assignments_one_primary",
			"user_id",
			unique=True,
			postgresql_where="assignment_type = 'PRIMARY'",
		),
		Index(
			"uq_user_application_assignments_one_backup",
			"user_id",
			unique=True,
			postgresql_where="assignment_type = 'BACKUP'",
		),
	)

	user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
	application: Mapped[Application] = mapped_column(SAEnum(Application, name="auth_application"), primary_key=True)
	assignment_type: Mapped[AssignmentType] = mapped_column(SAEnum(AssignmentType, name="auth_assignment_type"), nullable=False)

	user: Mapped["UserModel"] = relationship(back_populates="application_assignments")
