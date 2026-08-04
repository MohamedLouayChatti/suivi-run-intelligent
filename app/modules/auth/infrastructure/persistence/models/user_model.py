from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, Index, String, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel
    from app.modules.auth.infrastructure.persistence.models.role_model import RoleModel
    from app.modules.auth.infrastructure.persistence.models.application_assignment_model import ApplicationAssignmentModel

from app.shared.database.base import Base
from app.modules.auth.domain.enums.functional_team import FunctionalTeam

from .association_tables import role_permissions, user_direct_permissions, user_revoked_permissions, user_roles


class UserModel(Base):
	__tablename__ = "users"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	auth_provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
	email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
	display_name: Mapped[str] = mapped_column(String(255), nullable=False)
	active: Mapped[bool] = mapped_column(Boolean, nullable=False)
	avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
	functional_team: Mapped[FunctionalTeam] = mapped_column(SAEnum(FunctionalTeam, name="auth_functional_team"), nullable=False)

	roles: Mapped[list["RoleModel"]] = relationship(secondary=user_roles, back_populates="users", lazy="selectin")
	direct_permissions: Mapped[list["PermissionModel"]] = relationship(
		secondary=user_direct_permissions, back_populates="direct_users", lazy="selectin"
	)
	revoked_permissions: Mapped[list["PermissionModel"]] = relationship(
		secondary=user_revoked_permissions, back_populates="revoked_users", lazy="selectin"
	)
	application_assignments: Mapped[list["ApplicationAssignmentModel"]] = relationship(
		back_populates="user", cascade="all, delete-orphan", lazy="selectin"
	)
