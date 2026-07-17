from __future__ import annotations

from uuid import UUID

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.auth.infrastructure.persistence.models.user_model import UserModel
    from app.modules.auth.infrastructure.persistence.models.role_model import RoleModel

from app.shared.database.base import Base

from .association_tables import role_permissions, user_direct_permissions, user_revoked_permissions


class PermissionModel(Base):
	__tablename__ = "permissions"
	__table_args__ = (Index("ix_permissions_name", "name"),)

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
	description: Mapped[str] = mapped_column(Text, nullable=False)

	roles: Mapped[list["RoleModel"]] = relationship(
		secondary=role_permissions, back_populates="permissions", lazy="selectin"
	)
	direct_users: Mapped[list["UserModel"]] = relationship(
		secondary=user_direct_permissions, back_populates="direct_permissions", lazy="selectin"
	)
	revoked_users: Mapped[list["UserModel"]] = relationship(
		secondary=user_revoked_permissions, back_populates="revoked_permissions", lazy="selectin"
	)
