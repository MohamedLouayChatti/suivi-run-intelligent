from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel
    from app.modules.auth.infrastructure.persistence.models.user_model import UserModel

from app.shared.database.base import Base

from .association_tables import role_permissions, user_roles


class RoleModel(Base):
	__tablename__ = "roles"
	__table_args__ = (Index("ix_roles_name", "name"),)

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

	permissions: Mapped[list["PermissionModel"]] = relationship(
		secondary=role_permissions, back_populates="roles", lazy="selectin"
	)
	users: Mapped[list["UserModel"]] = relationship(
		secondary=user_roles, back_populates="roles", lazy="selectin"
	)
