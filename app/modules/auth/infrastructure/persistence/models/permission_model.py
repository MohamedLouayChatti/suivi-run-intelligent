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

from .association_tables import permission_dependencies, role_permissions, user_direct_permissions, user_revoked_permissions


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
	required_permissions: Mapped[list["PermissionModel"]] = relationship(
		secondary=permission_dependencies,
		primaryjoin=lambda: PermissionModel.id == permission_dependencies.c.permission_id,
		secondaryjoin=lambda: PermissionModel.id == permission_dependencies.c.requires_permission_id,
		lazy="selectin",
		join_depth=1,
	)
	"""The permissions this one cannot be used without -- direct prerequisites only.

	Eagerly loaded like the rest of this model's relationships: the catalog is forty rows of
	reference data, and every effective-permission resolution needs the whole graph anyway.
	One-directional on purpose -- nothing asks a permission what depends on it, and the
	reverse edges are derived in the domain when a cascade needs them.
	"""
